"""
spillmotor.py — Hjertet i spillet.

Ansvar:
  - Eier alle moduler (kalender, liga, cup, europa, hendelser)
  - Dag-for-dag tikk i bakgrunnen; stopper kun ved faktiske hendelser
  - Viser menyer og tar imot input
  - Koordinerer laguttak, kampavvikling og kondisjonsstyring
"""

import datetime
import random
import os
from typing import Optional

from database     import last_database, hent_spilleklar_tropp, foreslå_startellever
from kalender     import SpillKalender, KalenderHendelse
from kampmotor    import KampMotor, LagTilstand
from hendelser    import HendelsesManager
from taktikk      import TAKTIKK_KATALOG, Oppstilling, Posisjon, POSISJON_GRUPPE
from liga         import LigaSystem, opprett_ligasystem, populer_ligasystem_fra_db
from person       import Person

# =============================================================================
# KONSTANTER
# =============================================================================
SESONG_AAR       = 2025
BENK_STØRRELSE   = 7      # Antall innbyttere på benken
SKJERM_BREDDE    = 52

# Kondisjonsfarge-terskel for visning
KOND_GOD     = 90.0   # Grønn
KOND_OK      = 75.0   # Gul
KOND_LITEN   = 60.0   # Oransje (⚠)
# Under 60: rød (✗)


# =============================================================================
# HJELPEFUNKSJONER — VISNING
# =============================================================================
def _klar_skjerm():
    os.system('cls' if os.name == 'nt' else 'clear')


def _kondisjon_ikon(kond: float, skadet: bool = False) -> str:
    if skadet:
        return "✗"
    if kond >= KOND_GOD:
        return " "
    if kond >= KOND_OK:
        return "~"
    if kond >= KOND_LITEN:
        return "⚠"
    return "!"


def _kondisjon_tekst(spiller: Person) -> str:
    kond    = getattr(spiller, 'kondisjon', 100.0)
    skadet  = getattr(spiller, 'skadet', False)
    ikon    = _kondisjon_ikon(kond, skadet)
    if skadet:
        dager = getattr(spiller, 'skade_dager_igjen', 0)
        return f"{ikon} SKADET ({dager}d)"
    return f"{ikon} {kond:.0f}%"


def _linje(tegn: str = "=") -> str:
    return tegn * SKJERM_BREDDE


def _tittel(tekst: str) -> str:
    return f"\n{_linje()}\n  {tekst}\n{_linje()}"


def _meny(alternativer: list[str]) -> None:
    print()
    for i, alt in enumerate(alternativer, 1):
        print(f"  [{i}] {alt}")
    print()


def _input(prompt: str = "  Valg: ") -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return "q"


def _vent(melding: str = "  [Trykk Enter for å fortsette]") -> None:
    _input(melding)


# =============================================================================
# TROPP-BUILDER — velger startellever + benk
# =============================================================================
class TroppBuilder:
    """
    Holder styr på laguttak: startellever (11) og benk (7).
    Foreslår automatisk, men lar spilleren overstyre.
    """

    def __init__(self, klubb, formasjon_navn: str = "4-3-3"):
        self.klubb         = klubb
        self.formasjon_navn = formasjon_navn
        self.startellever: list[Person] = []   # Indeks 0–10
        self.benk: list[Person]         = []   # Indeks 0–6
        self._bygg_forslag()

    def _bygg_forslag(self):
        """Setter opp beste mulige ellever + benk automatisk."""
        formasjon  = TAKTIKK_KATALOG.get(self.formasjon_navn,
                     next(iter(TAKTIKK_KATALOG.values())))
        tropp      = hent_spilleklar_tropp(self.klubb)
        alle       = self.klubb.spillerstall   # Inkl. skadede — for benk-visning

        # Bygg startellever slot for slot
        plassert   = set()
        ellever    = []

        sone_rekkefølge = {"forsvar": 0, "midtbane": 1, "angrep": 2}
        slots = sorted(
            formasjon.slots if hasattr(formasjon, 'slots') else [],
            key=lambda s: sone_rekkefølge.get(
                getattr(s, 'sone', 'midtbane'), 1
            )
        )

        for slot in slots:
            # slot is a FormasjonSlot — pass its .posisjon
            beste = self._finn_beste_for_slot(slot.posisjon, tropp, plassert)
            if beste:
                ellever.append(beste)
                plassert.add(id(beste))

        # Fyll opp til 11 hvis nødvendig
        for s in tropp:
            if len(ellever) >= 11:
                break
            if id(s) not in plassert:
                ellever.append(s)
                plassert.add(id(s))

        self.startellever = ellever[:11]

        # Benk: spilleklar tropp sortert etter ferdighet, ikke i startelleveren
        benk_kandidater = [
            s for s in sorted(tropp,
                key=lambda x: getattr(x, 'ferdighet', 0), reverse=True)
            if id(s) not in plassert
        ]
        self.benk = benk_kandidater[:BENK_STØRRELSE]

    def _finn_beste_for_slot(
        self, slot, tropp: list[Person], plassert: set
    ) -> Optional[Person]:
        """Finner best egnede spiller for en posisjon-slot."""
        from taktikk import KOMPATIBLE_POSISJONER
        kandidater = []
        for s in tropp:
            if id(s) in plassert:
                continue
            primær   = getattr(s, 'primær_posisjon', None)
            sekundær = getattr(s, 'sekundær_posisjon', None)

            if primær == slot:
                eff = 1.00
            elif sekundær == slot:
                eff = 0.85
            elif primær and slot in KOMPATIBLE_POSISJONER.get(primær, set()):
                eff = 0.81
            else:
                continue
            score = getattr(s, 'ferdighet', 0) * eff * (getattr(s, 'kondisjon', 100) / 100)
            kandidater.append((score, s))

        if not kandidater:
            return None
        return max(kandidater, key=lambda x: x[0])[1]

    def bytt_spiller(self, start_idx: int, benk_idx: int) -> bool:
        """Bytter en starter med en benkespiller."""
        if not (0 <= start_idx < len(self.startellever)):
            return False
        if not (0 <= benk_idx < len(self.benk)):
            return False
        self.startellever[start_idx], self.benk[benk_idx] = \
            self.benk[benk_idx], self.startellever[start_idx]
        return True

    def bytt_formasjon(self, ny_formasjon: str) -> bool:
        if ny_formasjon not in TAKTIKK_KATALOG:
            return False
        self.formasjon_navn = ny_formasjon
        self._bygg_forslag()
        return True

    def bygg_oppstilling(self) -> Oppstilling:
        """Konverterer til Oppstilling-objekt for kampmotor."""
        formasjon = TAKTIKK_KATALOG[self.formasjon_navn]
        slots     = formasjon.slots if hasattr(formasjon, 'slots') else []
        plasseringer = {}
        for i, slot in enumerate(slots[:11]):
            if i < len(self.startellever):
                plasseringer[slot.posisjon] = self.startellever[i]
        return Oppstilling(formasjon=formasjon, plasseringer=plasseringer)

    def print_laguttak(self, motstandernavn: str = ""):
        """Printer laguttak-skjerm CM95-stil."""
        tittel = f"LAGUTTAK — {self.klubb.navn}"
        if motstandernavn:
            tittel += f" vs {motstandernavn}"
        print(_tittel(tittel))
        print(f"  Formasjon: {self.formasjon_navn}\n")
        print(f"  {'#':<4} {'Navn':<20} {'Pos':<6} {'Ferd':<6} Kondisjon")
        print(f"  {'-'*44}")

        for i, s in enumerate(self.startellever, 1):
            navn    = f"{s.fornavn[0]}. {s.etternavn}"
            pos     = getattr(s, 'primær_posisjon', '?')
            pos_str = pos.name if hasattr(pos, 'name') else str(pos)
            ferd    = getattr(s, 'ferdighet', '?')
            kond    = _kondisjon_tekst(s)
            print(f"  {i:<4} {navn:<20} {pos_str:<6} {ferd:<6} {kond}")

        print(f"\n  {'--- Benk ---':^44}")
        for i, s in enumerate(self.benk, 1):
            navn    = f"{s.fornavn[0]}. {s.etternavn}"
            pos     = getattr(s, 'primær_posisjon', '?')
            pos_str = pos.name if hasattr(pos, 'name') else str(pos)
            ferd    = getattr(s, 'ferdighet', '?')
            kond    = _kondisjon_tekst(s)
            print(f"  S{i:<3} {navn:<20} {pos_str:<6} {ferd:<6} {kond}")

        print(f"\n  {_linje('-')}")


# =============================================================================
# SPILLMOTOR
# =============================================================================
class Spillmotor:
    """
    Øverste koordinator. Eier alle moduler og kjører game loop.
    """

    def __init__(self):
        self.klubber: dict        = {}
        self.spiller_klubb        = None   # Klubben brukeren manager
        self.kalender: SpillKalender = None
        self.liga: LigaSystem     = None
        self.hendelser: HendelsesManager = HendelsesManager()
        self._kjører: bool        = False

    # =========================================================================
    # OPPSTART
    # =========================================================================
    def start_nytt_spill(self):
        """Kjøres én gang ved oppstart av ny sesong."""
        _klar_skjerm()
        print(_tittel("NORSK FOTBALLMANAGER  —  SESONG 2025"))
        print("\n  Laster database...")
        self.klubber = last_database(sesong_aar=SESONG_AAR, verbose=False)

        print(f"  ✓ {len(self.klubber)} klubber lastet")

        # Velg klubb
        self.spiller_klubb = self._velg_klubb()
        if not self.spiller_klubb:
            return

        # Bygg ligasystem
        print("\n  Setter opp ligasystemet...")
        self.liga = opprett_ligasystem()
        populer_ligasystem_fra_db(self.liga, list(self.klubber.values()))

        # Bygg kalender
        self.kalender = SpillKalender(start_aar=SESONG_AAR)
        self.hendelser.sett_dato(datetime.date(SESONG_AAR, 1, 1))

        kombinert_terminliste = [[] for _ in range(len(self.liga.eliteserien.terminliste))]
        for r in range(len(self.liga.eliteserien.terminliste)):
            kombinert_terminliste[r].extend(self.liga.eliteserien.terminliste[r])
            if r < len(self.liga.obos.terminliste):
                kombinert_terminliste[r].extend(self.liga.obos.terminliste[r])
            for avd in self.liga.div_2:
                if r < len(avd.terminliste):
                    kombinert_terminliste[r].extend(avd.terminliste[r])
            for avd in self.liga.div_3:
                if r < len(avd.terminliste):
                    kombinert_terminliste[r].extend(avd.terminliste[r])

        self.kalender.populer_serierunder(kombinert_terminliste)

        print(f"  ✓ Kalender klar")
        _vent("\n  [Trykk Enter for å begynne sesongen]")

        self._kjører = True
        self._game_loop()

    def _velg_klubb(self):
        """Lar spilleren velge hvilken klubb de vil manage."""
        elitelag = [
            k for k in self.klubber.values()
            if getattr(k, 'divisjon', '') == 'Eliteserien'
        ]
        elitelag.sort(key=lambda k: getattr(k, 'historisk_styrke', 0), reverse=True)

        while True:
            print(_tittel("VELG KLUBB"))
            for i, k in enumerate(elitelag, 1):
                styrke   = getattr(k, 'historisk_styrke', 0)
                stadion  = getattr(k, 'stadion', None)
                kap      = getattr(stadion, 'kapasitet', 0) if stadion else 0
                stjerner = "★" * (styrke // 4) + "☆" * (5 - styrke // 4)
                print(f"  {i:>2}. {k.navn:<25} {stjerner}  ({kap:,} tilskuere)")

            print()
            valg = _input("  Velg nummer (eller 'q' for å avslutte): ")
            if valg.lower() == 'q':
                return None
            try:
                idx = int(valg) - 1
                if 0 <= idx < len(elitelag):
                    valgt = elitelag[idx]
                    print(f"\n  Du har valgt: {valgt.navn}")
                    bekreft = _input("  Bekreft? (j/n): ").lower()
                    if bekreft == 'j':
                        return valgt
            except ValueError:
                pass
            print("  Ugyldig valg. Prøv igjen.\n")

    # =========================================================================
    # GAME LOOP — tikker dag for dag, stopper kun ved hendelser
    # =========================================================================
    def _game_loop(self):
        """
        Tikker én dag om gangen.
        Stille dager: hvil alle spillere, fortsett umiddelbart.
        Hendelsesdager: stopp og vis hovedmeny.
        """
        while self._kjører:
            dag = self.kalender.simuler_neste_dag()
            dato = self.kalender.dagens_dato
            self.hendelser.sett_dato(dato)

            # Alle spillere hviler (kondisjon + skaderehabilitering)
            self._hvil_alle(dag)

            if not dag.har_innhold:
                # Stille dag — sjekk om vi er på slutten av sesongen
                if dato >= datetime.date(SESONG_AAR, 12, 31):
                    self._sesong_slutt()
                    break
                continue   # Hopp umiddelbart til neste dag

            # Hendelsesdag — vis hovedmeny og vent på input
            self._vis_hendelsesdag(dag, dato)

    def _hvil_alle(self, dag):
        """
        Kalles hver dag, også stille dager.
        Kondisjon og skaderehabilitering tikker alltid.
        """
        for klubb in self.klubber.values():
            for spiller in klubb.spillerstall:
                var_skadet = getattr(spiller, 'skadet', False)
                if hasattr(spiller, 'hvil_en_dag'):
                    spiller.hvil_en_dag()
                # Sjekk friskmelding
                er_frisk_nå = not getattr(spiller, 'skadet', False)
                if var_skadet and er_frisk_nå:
                    self.hendelser.sjekk_friskmelding(spiller)

    # =========================================================================
    # HENDELSESDAG — vis meny og håndter input
    # =========================================================================
    def _vis_hendelsesdag(self, dag, dato: datetime.date):
        """Dispatcher: sender hendelsesdagen til riktig handler."""
        har_kamp = dag.har_kamper if hasattr(dag, 'har_kamper') else bool(dag.kamper)
        mine_kamper = [
            k for k in dag.kamper
            if (getattr(k, 'hjemme', None) == self.spiller_klubb or
                getattr(k, 'borte', None) == self.spiller_klubb)
        ]

        # Vis innboks hvis det er nyheter
        uleste = [h for h in self.hendelser.nyhets_ko if not h.lest]
        if uleste:
            self.hendelser.print_innboks()
            _vent()

        # Kampdag for spillerens klubb
        if mine_kamper:
            for kamp in mine_kamper:
                self._håndter_kampdag(kamp, dato)
            return

        # Andre hendelser (overgangsvindu, seriestart, etc.)
        if dag.hendelser:
            self._håndter_kalender_hendelse(dag, dato)
            return

        # Andre lags kamper — vis raskt og gå videre
        if har_kamp:
            self._vis_andre_resultater(dag, dato)

    def _håndter_kalender_hendelse(self, dag, dato: datetime.date):
        """Håndterer ikke-kamp kalender-hendelser."""
        for hendelse in dag.hendelser:
            _klar_skjerm()
            print(_tittel(f"  {dato.strftime('%A %d. %B %Y').upper()}"))

            if hendelse == KalenderHendelse.SERIESTART:
                print("\n  🏁  SESONGEN STARTER!")
                print(f"\n  {self.spiller_klubb.navn} er klare for Eliteserien {SESONG_AAR}.")

            elif hendelse in (KalenderHendelse.OVERGANG_1_AAPNER,
                              KalenderHendelse.OVERGANG_2_AAPNER):
                print("\n  🔄  OVERGANGSVINDUET ÅPNER")
                print("\n  Du kan nå kjøpe og selge spillere.")

            elif hendelse in (KalenderHendelse.OVERGANG_1_LUKKER,
                              KalenderHendelse.OVERGANG_2_LUKKER):
                print("\n  🔒  OVERGANGSVINDUET LUKKER")

            elif hendelse == KalenderHendelse.SERIEFINALE:
                print("\n  🏆  SERIEFINALE — siste runde spilles i dag!")

            _vent()

    def _vis_andre_resultater(self, dag, dato: datetime.date):
        """Viser resultater for kamper spillerens klubb ikke er med i — raskt."""
        andre = [k for k in dag.kamper
                 if (getattr(k, 'hjemme', None) != self.spiller_klubb and
                     getattr(k, 'borte', None) != self.spiller_klubb)
                 and getattr(k, 'spilt', False)]
        if not andre:
            return
        print(f"\n  {dato.strftime('%d.%m')} — Andre resultater:")
        for k in andre[:6]:
            print(f"    {k.hjemme.kortnavn} {k.hjemme_maal}–{k.borte_maal} {k.borte.kortnavn}")
        if len(andre) > 6:
            print(f"    ... og {len(andre)-6} til")
        _vent()

    # =========================================================================
    # KAMPDAG — laguttak → kamp → rapport
    # =========================================================================
    def _håndter_kampdag(self, kamp, dato: datetime.date):
        """Full kampdag-flyt for spillerens klubb."""
        er_hjemme = (kamp.hjemme == self.spiller_klubb)
        motstander = kamp.borte if er_hjemme else kamp.hjemme

        while True:
            _klar_skjerm()
            print(_tittel(
                f"{'HJEMME' if er_hjemme else 'BORTE'}  —  "
                f"{self.spiller_klubb.navn} vs {motstander.navn}  —  "
                f"{dato.strftime('%d.%m.%Y')}"
            ))

            # Bygg tropp-forslag
            builder = TroppBuilder(self.spiller_klubb)

            _meny([
                "Se laguttak og juster",
                "Spill kamp →",
                "Vis spillerstall",
            ])

            valg = _input()

            if valg == "1":
                self._laguttak_meny(builder, motstander.navn)
            elif valg == "2":
                self._spill_kamp(kamp, builder, motstander)
                break
            elif valg == "3":
                self._vis_spillerstall()
            else:
                print("  Ugyldig valg.")

    def _laguttak_meny(self, builder: TroppBuilder, motstandernavn: str):
        """Interaktiv laguttak-skjerm."""
        while True:
            _klar_skjerm()
            builder.print_laguttak(motstandernavn)

            _meny([
                "Bytt startspiller med benkespiller",
                "Bytt formasjon",
                "Tilbake",
            ])

            valg = _input()

            if valg == "1":
                start_nr = _input("  Startspiller nr (1–11): ")
                benk_nr  = _input("  Benkespiller nr (S1–S7, skriv 1–7): ")
                try:
                    ok = builder.bytt_spiller(int(start_nr)-1, int(benk_nr)-1)
                    print("  ✓ Byttet." if ok else "  Ugyldig bytte.")
                except ValueError:
                    print("  Ugyldig input.")
                _vent()

            elif valg == "2":
                print("\n  Tilgjengelige formasjoner:")
                formasjoner = list(TAKTIKK_KATALOG.keys())
                for i, f in enumerate(formasjoner, 1):
                    print(f"    [{i}] {f}")
                valg2 = _input("  Velg nummer: ")
                try:
                    idx = int(valg2) - 1
                    if 0 <= idx < len(formasjoner):
                        ok = builder.bytt_formasjon(formasjoner[idx])
                        print("  ✓ Formasjon endret." if ok else "  Feil.")
                except ValueError:
                    print("  Ugyldig input.")
                _vent()

            elif valg == "3":
                break

    def _spill_kamp(self, kamp, builder: TroppBuilder, motstander):
        """Kjører KampMotor og presenterer resultatet."""
        er_hjemme = (kamp.hjemme == self.spiller_klubb)

        hjemme_klubb  = kamp.hjemme
        borte_klubb   = kamp.borte
        hjemme_builder = builder if er_hjemme else TroppBuilder(hjemme_klubb)
        borte_builder  = TroppBuilder(borte_klubb) if er_hjemme else builder

        hjemme_opp = hjemme_builder.bygg_oppstilling()
        borte_opp  = borte_builder.bygg_oppstilling()

        motor  = KampMotor(tillat_ekstraomganger=(kamp.kamp_type == "cup"))
        resultat = motor.spill_kamp(
            hjemme_klubb, borte_klubb, hjemme_opp, borte_opp
        )

        # Registrer resultatet i kamp-objektet
        kamp.registrer_resultat(resultat.hjemme_maal, resultat.borte_maal)

        # Oppdater kondisjon (allerede gjort av kampmotor via _sluttspill)
        # Registrer kampresultater i hendelsessystemet
        alle_spillere = builder.startellever + builder.benk
        for s in alle_spillere:
            rating  = resultat.statistikk.hent_rating(s)
            startet = s in builder.startellever
            self.hendelser.registrer_kampresultat(s, rating, startet)

        # Vis rapport
        _klar_skjerm()
        resultat.print_kamprapport(
            hjemme_spillere=hjemme_builder.startellever,
            borte_spillere=borte_builder.startellever,
        )

        # Hendelsessjekk etter kamp
        lag_resultat = "S" if resultat.vinner_navn == self.spiller_klubb.navn else \
                       "U" if resultat.hjemme_maal == resultat.borte_maal else "T"
        if not hasattr(self.spiller_klubb, '_resultat_historikk'):
            self.spiller_klubb._resultat_historikk = []
        self.spiller_klubb._resultat_historikk.append(lag_resultat)

        self.hendelser.sjekk_lag_terskler(
            klubb      = self.spiller_klubb,
            resultater = self.spiller_klubb._resultat_historikk,
            tabellplass= 8,   # Plassholder til ligasystemet er koblet
            runde_nr   = len(self.spiller_klubb._resultat_historikk),
        )

        uleste = [h for h in self.hendelser.nyhets_ko if not h.lest]
        if uleste:
            print()
            self.hendelser.print_innboks(maks=3)

        _vent()

    # =========================================================================
    # MENYER
    # =========================================================================
    def _vis_spillerstall(self):
        """Viser komplett spillerstall med kondisjon og skadestatus."""
        _klar_skjerm()
        print(_tittel(f"SPILLERSTALL — {self.spiller_klubb.navn}"))
        print(f"\n  {'Navn':<22} {'Pos':<6} {'Ferd':<6} {'Kond':<10} Rykte")
        print(f"  {'-'*50}")

        grupper = {"K": [], "F": [], "M": [], "A": []}
        for s in sorted(self.spiller_klubb.spillerstall,
                         key=lambda x: getattr(x, 'ferdighet', 0), reverse=True):
            pos = getattr(s, 'primær_posisjon', None)
            gruppe = POSISJON_GRUPPE.get(pos, "M") if pos else "M"
            grupper[gruppe].append(s)

        gruppe_navn = {"K": "KEEPERE", "F": "FORSVAR", "M": "MIDTBANE", "A": "ANGREP"}
        for g in ["K", "F", "M", "A"]:
            if not grupper[g]:
                continue
            print(f"\n  {gruppe_navn[g]}")
            for s in grupper[g]:
                navn   = f"{s.fornavn[0]}. {s.etternavn}"
                pos    = getattr(s, 'primær_posisjon', '?')
                pos_str = pos.name if hasattr(pos, 'name') else str(pos)
                ferd   = getattr(s, 'ferdighet', '?')
                kond   = _kondisjon_tekst(s)
                rykte  = getattr(s, 'rykte', '') if hasattr(s, 'rykte') else ''
                print(f"  {navn:<22} {pos_str:<6} {ferd:<6} {kond:<14} {rykte}")

        _vent()

    # =========================================================================
    # SESONG SLUTT
    # =========================================================================
    def _sesong_slutt(self):
        _klar_skjerm()
        print(_tittel(f"SESONG {SESONG_AAR} ER OVER"))
        hist = getattr(self.spiller_klubb, '_resultat_historikk', [])
        seiere = hist.count("S")
        uavgjort = hist.count("U")
        tap = hist.count("T")
        print(f"\n  {self.spiller_klubb.navn}")
        print(f"  Kamper:    {len(hist)}")
        print(f"  Seiere:    {seiere}")
        print(f"  Uavgjort:  {uavgjort}")
        print(f"  Tap:       {tap}")
        print(f"  Poeng:     {seiere*3 + uavgjort}")
        _vent("\n  [Trykk Enter for å avslutte]")
        self._kjører = False


# =============================================================================
# INNGANGSPUNKT
# =============================================================================
if __name__ == "__main__":
    motor = Spillmotor()
    motor.start_nytt_spill()
