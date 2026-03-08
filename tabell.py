"""
tabell.py  –  Norsk Football Manager '95
Seriatabell, terminliste og spillerstatistikk.
Kan printes direkte (CM95-stil) eller leses av UI-laget.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from klubb import Klubb
    from kampmotor import KampResultat


# ── Bredder for kolonner ──────────────────────────────────────────────────────
_W_NAVN   = 22
_W_COL    =  4
_LINJE    = "─" * (_W_NAVN + _W_COL * 9 + 8)


# =============================================================================
# TABELLRAD
# =============================================================================
@dataclass
class Tabellrad:
    klubb_navn: str
    kamp: int = 0
    seier: int = 0
    uavgjort: int = 0
    tap: int = 0
    mål_for: int = 0
    mål_mot: int = 0
    poeng: int = 0

    @property
    def mål_differanse(self) -> int:
        return self.mål_for - self.mål_mot

    def oppdater(self, mål_for: int, mål_mot: int) -> None:
        self.kamp += 1
        self.mål_for  += mål_for
        self.mål_mot  += mål_mot
        if mål_for > mål_mot:
            self.seier  += 1
            self.poeng  += 3
        elif mål_for == mål_mot:
            self.uavgjort += 1
            self.poeng    += 1
        else:
            self.tap += 1

    def rad_str(self, plass: int) -> str:
        return (
            f"  {plass:>2}. {self.klubb_navn:<{_W_NAVN}}"
            f"  {self.kamp:>{_W_COL}}"
            f"  {self.seier:>{_W_COL}}"
            f"  {self.uavgjort:>{_W_COL}}"
            f"  {self.tap:>{_W_COL}}"
            f"  {self.mål_for:>{_W_COL}}"
            f"  {self.mål_mot:>{_W_COL}}"
            f"  {self.mål_differanse:>+{_W_COL}}"
            f"  {self.poeng:>{_W_COL}}"
        )


# =============================================================================
# SERIATABELL
# =============================================================================
class Seriatabell:
    """Holder styr på tabellstillingen for én divisjon."""

    def __init__(self, divisjon: str) -> None:
        self.divisjon = divisjon
        self._rader: dict[str, Tabellrad] = {}

    def registrer_klubb(self, klubb_navn: str) -> None:
        if klubb_navn not in self._rader:
            self._rader[klubb_navn] = Tabellrad(klubb_navn=klubb_navn)

    def registrer_resultat(self, resultat: "KampResultat") -> None:
        """Oppdaterer tabellen fra et KampResultat."""
        h = resultat.hjemme_navn
        b = resultat.borte_navn
        self.registrer_klubb(h)
        self.registrer_klubb(b)
        self._rader[h].oppdater(resultat.hjemme_maal, resultat.borte_maal)
        self._rader[b].oppdater(resultat.borte_maal,  resultat.hjemme_maal)

    def sorter(self) -> list[Tabellrad]:
        """Returnerer tabellen sortert etter poeng → måldiff → mål for."""
        return sorted(
            self._rader.values(),
            key=lambda r: (r.poeng, r.mål_differanse, r.mål_for),
            reverse=True,
        )

    def hent_rad(self, klubb_navn: str) -> Tabellrad | None:
        return self._rader.get(klubb_navn)

    def plass(self, klubb_navn: str) -> int:
        """Returnerer 1-indeksert tabellplass."""
        for i, r in enumerate(self.sorter(), 1):
            if r.klubb_navn == klubb_navn:
                return i
        return -1

    def print_tabell(self, maks_rader: int = 999) -> None:
        print()
        print(f"  ── {self.divisjon.upper()} ──")
        print(f"  {'#':>3}  {'Lag':<{_W_NAVN}}"
              f"  {'K':>{_W_COL}}"
              f"  {'S':>{_W_COL}}"
              f"  {'U':>{_W_COL}}"
              f"  {'T':>{_W_COL}}"
              f"  {'MF':>{_W_COL}}"
              f"  {'MM':>{_W_COL}}"
              f"  {'MD':>{_W_COL}}"
              f"  {'P':>{_W_COL}}")
        print("  " + _LINJE)
        for plass, rad in enumerate(self.sorter()[:maks_rader], 1):
            print(rad.rad_str(plass))
        print()


# =============================================================================
# KAMP (terminliste-node)
# =============================================================================
@dataclass
class Kamp:
    runde: int
    hjemme: str   # Klubbnavn
    borte:  str
    resultat: "KampResultat | None" = None

    @property
    def er_spilt(self) -> bool:
        return self.resultat is not None

    @property
    def score_str(self) -> str:
        if self.resultat:
            return f"{self.resultat.hjemme_maal} – {self.resultat.borte_maal}"
        return "– – –"

    def rad_str(self) -> str:
        return (
            f"  Runde {self.runde:>2}:  "
            f"{self.hjemme:<{_W_NAVN}}  "
            f"{self.score_str:^7}  "
            f"{self.borte:<{_W_NAVN}}"
        )


# =============================================================================
# TERMINLISTE
# =============================================================================
class Terminliste:
    """Genererer og holder styr på alle seriakamper."""

    def __init__(self, lag: list[str]) -> None:
        self.lag   = list(lag)
        self.kamper: list[Kamp] = []
        self._generer()

    def _generer(self) -> None:
        """Round-robin med hjemme- og borterunde."""
        lag = list(self.lag)
        n   = len(lag)
        if n % 2 != 0:
            lag.append("Frikamp")

        runde = 1
        for tur in range(2):  # hjemme- og borterunde
            rotasjon = list(range(1, len(lag)))
            for i in range(len(lag) - 1):
                fast   = lag[0]
                rest   = [lag[j] for j in rotasjon]
                pairs  = [(fast, rest[-1])]
                pairs += [(rest[j], rest[len(lag) - 2 - j])
                          for j in range(len(lag) // 2 - 1)]
                for h, b in pairs:
                    if "Frikamp" not in (h, b):
                        if tur == 0:
                            self.kamper.append(Kamp(runde, h, b))
                        else:
                            self.kamper.append(Kamp(runde, b, h))
                rotasjon = [rotasjon[-1]] + rotasjon[:-1]
                runde += 1

    def hent_runde(self, runde: int) -> list[Kamp]:
        return [k for k in self.kamper if k.runde == runde]

    def neste_uspilte(self, klubb_navn: str | None = None) -> list[Kamp]:
        """Henter neste uspilte runde globalt, eller for én klubb."""
        uspilte = [k for k in self.kamper if not k.er_spilt]
        if not uspilte:
            return []
        if klubb_navn:
            uspilte = [k for k in uspilte
                       if k.hjemme == klubb_navn or k.borte == klubb_navn]
        if not uspilte:
            return []
        min_runde = min(k.runde for k in uspilte)
        return [k for k in uspilte if k.runde == min_runde]

    def registrer_resultat(self, kamp: Kamp, resultat: "KampResultat") -> None:
        kamp.resultat = resultat

    def print_terminliste(
        self,
        klubb_navn: str | None = None,
        maks_kamper: int = 30,
        vis_kun_uspilte: bool = False,
    ) -> None:
        """Printer terminlisten CM95-stil."""
        filtrert = self.kamper
        if klubb_navn:
            filtrert = [k for k in filtrert
                        if k.hjemme == klubb_navn or k.borte == klubb_navn]
        if vis_kun_uspilte:
            filtrert = [k for k in filtrert if not k.er_spilt]
        filtrert = filtrert[:maks_kamper]

        print()
        tittel = f"  TERMINLISTE — {klubb_navn or 'Alle kamper'}"
        print(tittel)
        print("  " + "─" * (len(tittel) + 2))
        nåværende_runde = -1
        for kamp in filtrert:
            if kamp.runde != nåværende_runde:
                print(f"\n  ── Runde {kamp.runde} ──")
                nåværende_runde = kamp.runde
            print(kamp.rad_str())
        print()


# =============================================================================
# SPILLERSTATISTIKK
# =============================================================================
@dataclass
class SpillerSesongsStatistikk:
    """Akkumulert statistikk for én spiller gjennom sesongen."""
    spiller_id:  str
    spiller_navn: str
    kamper:      int = 0
    mål:         int = 0
    assist:      int = 0   # Kan telles eksplisitt av kampmotoren
    gule_kort:   int = 0
    røde_kort:   int = 0
    rating_sum:  float = 0.0

    @property
    def snitt_rating(self) -> float:
        if self.kamper == 0:
            return 0.0
        return round(self.rating_sum / self.kamper, 2)

    def oppdater_fra_kamp(
        self,
        mål: int = 0,
        assist: int = 0,
        gule: int = 0,
        røde: int = 0,
        rating: float = 6.0,
    ) -> None:
        self.kamper     += 1
        self.mål        += mål
        self.assist     += assist
        self.gule_kort  += gule
        self.røde_kort  += røde
        self.rating_sum += rating

    def rad_str(self, plass: int) -> str:
        kort_str = ""
        if self.gule_kort:
            kort_str += f" {self.gule_kort}🟨"
        if self.røde_kort:
            kort_str += f" {self.røde_kort}🟥"
        return (
            f"  {plass:>3}.  {self.spiller_navn:<22}"
            f"  K:{self.kamper:>3}"
            f"  M:{self.mål:>3}"
            f"  A:{self.assist:>3}"
            f"  Rtg:{self.snitt_rating:>4.1f}"
            f"{kort_str}"
        )


class SpillerStatistikkRegister:
    """Holder spillerstatistikk for hele sesongen."""

    def __init__(self) -> None:
        self._data: dict[str, SpillerSesongsStatistikk] = {}

    def _hent_eller_opprett(self, spiller) -> SpillerSesongsStatistikk:
        pid  = getattr(spiller, 'id', str(id(spiller)))
        navn = getattr(spiller, 'fullt_navn',
               getattr(spiller, 'etternavn', str(spiller)))
        if pid not in self._data:
            self._data[pid] = SpillerSesongsStatistikk(
                spiller_id=pid, spiller_navn=navn)
        return self._data[pid]

    def registrer_kamp(
        self,
        spiller,
        mål: int = 0,
        assist: int = 0,
        gule: int = 0,
        røde: int = 0,
        rating: float = 6.0,
    ) -> None:
        stat = self._hent_eller_opprett(spiller)
        stat.oppdater_fra_kamp(mål=mål, assist=assist,
                               gule=gule, røde=røde, rating=rating)

    def oppdater_fra_kampresultat(self, resultat: "KampResultat") -> None:
        """
        Leser hendelser og spillerbørs fra et KampResultat og
        oppdaterer all spillerstatistikk automatisk.
        """
        # Tell mål og kort per spiller fra hendelseslisten
        mål_teller:  dict = {}
        gul_teller:  dict = {}
        rød_teller:  dict = {}

        for h in resultat.hendelser:
            spiller = h.spiller
            pid = getattr(spiller, 'id', id(spiller))
            if h.type == "mål":
                mål_teller[pid]  = mål_teller.get(pid, 0) + 1
            elif h.type == "gult_kort":
                gul_teller[pid]  = gul_teller.get(pid, 0) + 1
            elif h.type == "rødt_kort":
                rød_teller[pid]  = rød_teller.get(pid, 0) + 1

        # Alle spillere som var med i børsen fikk en kamp
        for spiller, rating in resultat.statistikk.spiller_rating.items():
            pid = getattr(spiller, 'id', id(spiller))
            self.registrer_kamp(
                spiller,
                mål=mål_teller.get(pid, 0),
                gule=gul_teller.get(pid, 0),
                røde=rød_teller.get(pid, 0),
                rating=rating,
            )

    def toppscorere(self, topp_n: int = 10) -> list[SpillerSesongsStatistikk]:
        return sorted(self._data.values(),
                      key=lambda s: (s.mål, s.snitt_rating), reverse=True)[:topp_n]

    def beste_rating(self, topp_n: int = 10) -> list[SpillerSesongsStatistikk]:
        aktive = [s for s in self._data.values() if s.kamper >= 3]
        return sorted(aktive, key=lambda s: s.snitt_rating, reverse=True)[:topp_n]

    def print_toppscorere(self, topp_n: int = 10) -> None:
        print()
        print(f"  ── TOPPSCORERE ──")
        print(f"  {'#':>3}   {'Spiller':<22}  {'K':>4}  {'M':>4}  {'A':>4}  {'Rtg':>5}")
        print("  " + "─" * 52)
        for i, stat in enumerate(self.toppscorere(topp_n), 1):
            print(stat.rad_str(i))
        print()

    def print_spillerbors_sesong(self, topp_n: int = 10) -> None:
        print()
        print(f"  ── SESONGENS BESTE RATING (min. 3 kamper) ──")
        print(f"  {'#':>3}   {'Spiller':<22}  {'K':>4}  {'M':>4}  {'A':>4}  {'Rtg':>5}")
        print("  " + "─" * 52)
        for i, stat in enumerate(self.beste_rating(topp_n), 1):
            print(stat.rad_str(i))
        print()
