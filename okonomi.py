"""
okonomi.py  –  Norsk Football Manager '95
Kontrakter, spillermarked, overgangslogikk og AI-kjøp.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from person import Person, Posisjon, SKALA_MIN, SKALA_MAX

if TYPE_CHECKING:
    from klubb import Klubb


# =============================================================================
# KONTRAKT
# =============================================================================

@dataclass
class Kontrakt:
    """
    En spillers arbeidsavtale med klubben.
    Årstall er in-game år (f.eks. 1995).
    """
    ukelonn:      int    # NOK per uke
    utlops_aar:   int    # Siste gyldige år (1997 → utløper etter sesongen 1997)
    signert_aar:  int    # Brukes til å beregne signeringsbonus osv.
    spiller_verdi_ved_signering: int = 0   # Snapshot av markedsverdi ved signering

    def aar_igjen_fra(self, dags_dato_aar: int) -> int:
        """Antall hele år igjen av kontrakten."""
        return max(0, self.utlops_aar - dags_dato_aar)

    def er_utlopt(self, dags_dato_aar: int) -> bool:
        return dags_dato_aar > self.utlops_aar

    @property
    def aarlig_kostnad(self) -> int:
        return self.ukelonn * 52

    def __str__(self) -> str:
        return (
            f"Kontrakt  lønn={self.ukelonn:,} kr/uke  "
            f"utløper={self.utlops_aar}"
        )


# =============================================================================
# BUD
# =============================================================================

@dataclass
class Bud:
    """Et overgangs-bud fra én klubb på én spiller."""
    fra_klubb:       "Klubb"
    til_spiller:     Person
    budsum:          int        # NOK
    foreslått_lonn:  int        # NOK/uke
    foreslått_aar:   int        # Kontraktsår (in-game)
    kontraktsvarighet: int = 3  # År

    @property
    def akseptabel_for_spiller(self) -> bool:
        """
        Enkel vurdering fra spillerens side:
        - Lojalitet senker sjansen for å bytte klubb
        - Egoisme øker kravet om lønnsøkning
        Returnerer True hvis spilleren sannsynligvis ville sagt ja.
        """
        spiller = self.til_spiller
        lonn_ok = self.foreslått_lonn >= _minstelonn_krav(spiller)
        lojalitets_sjanse = 1.0 - (spiller.lojalitet / 20.0) * 0.6
        return lonn_ok and random.random() < lojalitets_sjanse

    @property
    def akseptabel_for_selger(self) -> bool:
        """
        Enkel vurdering fra selgerklubbens side:
        Bud over 80 % av markedsverdi aksepteres normalt.
        Intern uro øker viljen til å selge.
        """
        mv = self.til_spiller.markedsverdi_nok
        terskel = 0.80 if random.random() > 0.3 else 0.65
        return self.budsum >= mv * terskel


def _minstelonn_krav(spiller: Person) -> int:
    """
    Beregner hva en spiller forventer som ukentlig minimumslønn.
    Påvirket av OVR, alder og egoisme.
    """
    base   = 1_000 + spiller.ferdighet * 800
    ego_f  = 1.0 + (spiller.egoisme - 10) * 0.05   # ±50 % for egoisme 1–20
    alder_f = 1.0 + max(0, spiller.alder - 28) * 0.03
    return round(base * ego_f * alder_f)


# =============================================================================
# SPILLERMARKED
# =============================================================================

class SpillerMarked:
    """
    Globalt marked for spillere uten kontrakt og spillere til salgs.
    Holdes av spillmotoren og deles mellom alle klubber.
    """

    def __init__(self) -> None:
        self.free_agents:     list[Person]          = []
        self.overgangsliste:  list[tuple[Person, "Klubb"]] = []  # (spiller, eier)
        self.ventende_bud:    list[Bud]             = []
        self.overgang_logg:   list[str]             = []

    # ── Listeadministrasjon ───────────────────────────────────────────────────

    def legg_til_free_agent(self, spiller: Person) -> None:
        if spiller not in self.free_agents:
            self.free_agents.append(spiller)

    def fjern_free_agent(self, spiller: Person) -> None:
        self.free_agents = [p for p in self.free_agents if p.id != spiller.id]

    def legg_ut_for_salg(self, spiller: Person, eier: "Klubb") -> None:
        if not any(s.id == spiller.id for s, _ in self.overgangsliste):
            self.overgangsliste.append((spiller, eier))

    def trekk_fra_salg(self, spiller: Person) -> None:
        self.overgangsliste = [(s, k) for s, k in self.overgangsliste
                               if s.id != spiller.id]

    # ── Søk ──────────────────────────────────────────────────────────────────

    def soek_free_agents(
        self,
        posisjon: Optional[Posisjon] = None,
        min_ovr: int = 1,
        maks_alder: int = 40,
        maks_pris: Optional[int] = None,   # ukeslønn
    ) -> list[Person]:
        """Søk etter free agents med filtre."""
        treff = []
        for p in self.free_agents:
            if posisjon and p.primær_posisjon != posisjon:
                continue
            if p.ferdighet < min_ovr:
                continue
            if p.alder > maks_alder:
                continue
            if maks_pris and _minstelonn_krav(p) > maks_pris:
                continue
            treff.append(p)
        return sorted(treff, key=lambda p: p.ferdighet, reverse=True)

    def soek_til_salgs(
        self,
        posisjon: Optional[Posisjon] = None,
        min_ovr: int = 1,
        maks_markedsverdi: Optional[int] = None,
    ) -> list[tuple[Person, "Klubb"]]:
        """Søk blant spillere som er lagt ut til salgs."""
        treff = []
        for spiller, eier in self.overgangsliste:
            if posisjon and spiller.primær_posisjon != posisjon:
                continue
            if spiller.ferdighet < min_ovr:
                continue
            if maks_markedsverdi and spiller.markedsverdi_nok > maks_markedsverdi:
                continue
            treff.append((spiller, eier))
        return sorted(treff, key=lambda t: t[0].ferdighet, reverse=True)

    # ── Sesongslutt ──────────────────────────────────────────────────────────

    def oppdater_kontrakter_ved_sesongslutt(
        self,
        alle_klubber: list["Klubb"],
        dags_dato_aar: int,
    ) -> list[str]:
        """
        Kalles av kalenderen på NYTT_AAR-hendelsen.
        Spillere med utgåtte kontrakter frigjøres som free agents.
        Returnerer liste med nyhetsstrenger.
        """
        nyheter: list[str] = []

        for klubb in alle_klubber:
            for spiller in list(klubb.spillerstall):
                kontrakt = spiller.kontrakt
                if kontrakt is None:
                    continue
                if kontrakt.er_utlopt(dags_dato_aar):
                    klubb.fjern_person(spiller)
                    self.legg_til_free_agent(spiller)
                    nyhet = (
                        f"BOSMAN: {spiller.fullt_navn} forlater "
                        f"{klubb.navn} som free agent!"
                    )
                    nyheter.append(nyhet)
                    self.overgang_logg.append(nyhet)
                    print(nyhet)

        return nyheter

    # =========================================================================
    # OVERGANGSTRANSAKSJON
    # =========================================================================

    def behandle_bud(
        self,
        bud: Bud,
        selger: "Klubb",
        dags_dato_aar: int,
        tvungen: bool = False,
    ) -> tuple[bool, str]:
        """
        Forsøker å gjennomføre et bud.
        tvungen=True brukes av AI for å simulere aksepterte bud uten RNG.
        Returnerer (suksess, melding).
        """
        spiller  = bud.til_spiller
        kjøper   = bud.fra_klubb

        # Har kjøper råd?
        if kjøper.saldo < bud.budsum:
            return False, f"{kjøper.navn} har ikke råd ({kjøper.saldo:,} < {bud.budsum:,})"

        # Vil selger godta budet?
        if not tvungen and not bud.akseptabel_for_selger:
            mv = spiller.markedsverdi_nok
            return False, (
                f"{selger.navn} avviser budet. "
                f"Markedsverdi: {mv:,} kr, bud: {bud.budsum:,} kr"
            )

        # Vil spilleren flytte?
        if not tvungen and not bud.akseptabel_for_spiller:
            return False, f"{spiller.fullt_navn} ønsker ikke å flytte til {kjøper.navn}"

        # Gjennomfør overgangen
        selger.fjern_person(spiller)
        self.trekk_fra_salg(spiller)
        self.fjern_free_agent(spiller)

        from person import SpillerRolle
        kjøper.legg_til_person(spiller, SpillerRolle())

        ny_kontrakt = Kontrakt(
            ukelonn=bud.foreslått_lonn,
            utlops_aar=bud.foreslått_aar + bud.kontraktsvarighet,
            signert_aar=dags_dato_aar,
            spiller_verdi_ved_signering=spiller.markedsverdi_nok,
        )
        spiller.kontrakt = ny_kontrakt

        # Pengeoverføring
        kjøper.saldo -= bud.budsum
        selger.saldo += bud.budsum

        melding = (
            f"OVERGANG: {spiller.fullt_navn} "
            f"({selger.navn} → {kjøper.navn})  "
            f"{bud.budsum:,} kr  "
            f"lønn {bud.foreslått_lonn:,} kr/uke"
        )
        self.overgang_logg.append(melding)
        print(melding)
        return True, melding

    def hent_free_agent(
        self,
        kjøper: "Klubb",
        spiller: Person,
        dags_dato_aar: int,
        foreslått_lonn: int,
        kontraktsvarighet: int = 3,
    ) -> tuple[bool, str]:
        """
        Signerer en free agent til kjøper uten overgangssum.
        """
        if spiller not in self.free_agents:
            return False, f"{spiller.fullt_navn} er ikke en free agent"

        if foreslått_lonn < _minstelonn_krav(spiller):
            return False, (
                f"{spiller.fullt_navn} krever minst "
                f"{_minstelonn_krav(spiller):,} kr/uke"
            )

        self.fjern_free_agent(spiller)
        from person import SpillerRolle
        kjøper.legg_til_person(spiller, SpillerRolle())

        ny_kontrakt = Kontrakt(
            ukelonn=foreslått_lonn,
            utlops_aar=dags_dato_aar + kontraktsvarighet,
            signert_aar=dags_dato_aar,
            spiller_verdi_ved_signering=spiller.markedsverdi_nok,
        )
        spiller.kontrakt = ny_kontrakt

        melding = (
            f"SIGNERING: {spiller.fullt_navn} → {kjøper.navn}  "
            f"(free agent, {foreslått_lonn:,} kr/uke, "
            f"{kontraktsvarighet} år)"
        )
        self.overgang_logg.append(melding)
        print(melding)
        return True, melding


# =============================================================================
# AI-MANAGER
# =============================================================================

class AIManager:
    """
    Enkel AI som styrer overgangsmarkedet for datakontrollerte klubber.
    Kalles av spillmotoren i overgangsvinduet.
    """

    # Hvor mange prosent av saldoen AI er villig til å bruke per overgang
    MAKS_ANDEL_AV_SALDO: float = 0.40

    def __init__(self, klubb: "Klubb") -> None:
        self.klubb = klubb

    def _svak_posisjon(self) -> Optional[Posisjon]:
        """
        Finner den posisjonen der stallen er svakest (lavest gjennomsnittlig OVR).
        Returnerer None hvis alle posisjoner er dekket.
        """
        if not self.klubb.spillerstall:
            return None

        ovr_per_pos: dict[Posisjon, list[int]] = {}
        for spiller in self.klubb.spillerstall:
            pos = spiller.primær_posisjon
            if pos:
                ovr_per_pos.setdefault(pos, []).append(spiller.ferdighet)

        if not ovr_per_pos:
            return None

        snitt = {pos: sum(v) / len(v) for pos, v in ovr_per_pos.items()}
        return min(snitt, key=lambda p: snitt[p])

    def _maks_budsum(self) -> int:
        return int(self.klubb.saldo * self.MAKS_ANDEL_AV_SALDO)

    def kjøp_runde(
        self,
        marked: SpillerMarked,
        dags_dato_aar: int,
    ) -> list[str]:
        """
        Én runde med AI-kjøp i overgangsvinduet.
        Returnerer liste med gjennomførte overgangsstrenger.
        """
        resultater: list[str] = []
        pos = self._svak_posisjon()
        if pos is None:
            return resultater

        budsjett = self._maks_budsum()

        # 1. Prøv free agents først (gratis overgangssum)
        kandidater_fa = marked.soek_free_agents(
            posisjon=pos,
            min_ovr=8,
            maks_pris=int(budsjett * 0.05 / 52),   # rough ukeslønn-max
        )
        for kandidat in kandidater_fa[:2]:
            lonn = _minstelonn_krav(kandidat)
            if lonn * 52 * 3 > budsjett:
                continue
            ok, melding = marked.hent_free_agent(
                self.klubb, kandidat, dags_dato_aar, lonn
            )
            if ok:
                resultater.append(melding)
                break

        # 2. Prøv spillere til salgs
        kandidater_ts = marked.soek_til_salgs(
            posisjon=pos,
            maks_markedsverdi=budsjett,
        )
        for kandidat, selger in kandidater_ts[:3]:
            if selger.id == self.klubb.id:
                continue
            mv       = kandidat.markedsverdi_nok
            budsum   = int(mv * random.uniform(0.85, 1.10))
            lonn     = _minstelonn_krav(kandidat)
            if budsum > budsjett:
                continue

            bud = Bud(
                fra_klubb=self.klubb,
                til_spiller=kandidat,
                budsum=budsum,
                foreslått_lonn=lonn,
                foreslått_aar=dags_dato_aar,
                kontraktsvarighet=random.randint(2, 4),
            )
            ok, melding = marked.behandle_bud(bud, selger, dags_dato_aar)
            if ok:
                resultater.append(melding)
                break

        return resultater

    def forny_kontrakter(
        self,
        dags_dato_aar: int,
        år_terskel: int = 1,
    ) -> list[str]:
        """
        Fornyer kontrakter som utløper innen år_terskel år.
        Brukes av AI ved sesongstart.
        """
        resultater: list[str] = []
        for spiller in self.klubb.spillerstall:
            kontrakt = spiller.kontrakt
            if kontrakt is None:
                continue
            if kontrakt.aar_igjen_fra(dags_dato_aar) <= år_terskel:
                ny_lonn = round(_minstelonn_krav(spiller) * random.uniform(1.0, 1.15))
                spiller.kontrakt = Kontrakt(
                    ukelonn=ny_lonn,
                    utlops_aar=dags_dato_aar + random.randint(2, 4),
                    signert_aar=dags_dato_aar,
                    spiller_verdi_ved_signering=spiller.markedsverdi_nok,
                )
                melding = (
                    f"FORNYING: {spiller.fullt_navn} "
                    f"({self.klubb.navn})  ny lønn {ny_lonn:,} kr/uke"
                )
                resultater.append(melding)
                self.klubb._alt_personell   # trigger ingen side-effekt, bare referanse
        return resultater
