import datetime
from enum import Enum, auto
from typing import Optional

# =============================================================================
# HENDELSES-TYPER
# =============================================================================
class KalenderHendelse(Enum):
    # Overgangsvindu
    OVERGANG_1_AAPNER   = auto()
    OVERGANG_1_LUKKER   = auto()
    OVERGANG_2_AAPNER   = auto()
    OVERGANG_2_LUKKER   = auto()

    # Serie
    SERIESTART          = auto()
    SERIERUNDE          = auto()
    SERIEFINALE         = auto()   # Runde 30 — alle kamper samtidig

    # NM-cup
    CUP_RUNDE_1         = auto()
    CUP_RUNDE_2         = auto()
    CUP_RUNDE_3         = auto()
    CUP_RUNDE_4         = auto()
    CUP_RUNDE_5         = auto()
    CUP_SEMIFINALE      = auto()
    CUP_FINALE          = auto()

    # Europa
    EUROPA_KVALIK_START = auto()
    EUROPA_KAMPDAG      = auto()

    # Landslag
    FIFA_VINDU_START    = auto()
    FIFA_VINDU_SLUTT    = auto()

    # System
    NYTT_AAR            = auto()
    SESONGSLUTT         = auto()   # Opprykk/nedrykk prosesseres


# Menneskeleselige navn for tekstmenyen
HENDELSE_TEKST = {
    KalenderHendelse.OVERGANG_1_AAPNER:   "📋 Overgangsvindu 1 åpner",
    KalenderHendelse.OVERGANG_1_LUKKER:   "📋 Overgangsvindu 1 lukker",
    KalenderHendelse.OVERGANG_2_AAPNER:   "📋 Overgangsvindu 2 åpner",
    KalenderHendelse.OVERGANG_2_LUKKER:   "📋 Overgangsvindu 2 lukker",
    KalenderHendelse.SERIESTART:          "⚽ Seriestart! Eliteserien runde 1",
    KalenderHendelse.SERIERUNDE:          "⚽ Serierunde",
    KalenderHendelse.SERIEFINALE:         "🔥 Runde 30 — Alt avgjøres i dag!",
    KalenderHendelse.CUP_RUNDE_1:        "🏆 NM-cup: 1. runde",
    KalenderHendelse.CUP_RUNDE_2:        "🏆 NM-cup: 2. runde",
    KalenderHendelse.CUP_RUNDE_3:        "🏆 NM-cup: 3. runde",
    KalenderHendelse.CUP_RUNDE_4:        "🏆 NM-cup: 4. runde",
    KalenderHendelse.CUP_RUNDE_5:        "🏆 NM-cup: 5. runde",
    KalenderHendelse.CUP_SEMIFINALE:     "🏆 NM-cup: Semifinale",
    KalenderHendelse.CUP_FINALE:         "🏆🏆 NM-cup: FINALE på Ullevaal!",
    KalenderHendelse.EUROPA_KVALIK_START: "🌍 Europacup-kvalifisering starter",
    KalenderHendelse.EUROPA_KAMPDAG:      "🌍 Europacup-kampdag",
    KalenderHendelse.FIFA_VINDU_START:    "🌐 FIFA-vindu åpner — spillere til landslag",
    KalenderHendelse.FIFA_VINDU_SLUTT:    "🌐 FIFA-vindu lukker — spillere tilbake",
    KalenderHendelse.NYTT_AAR:            "🎆 Godt nytt år!",
    KalenderHendelse.SESONGSLUTT:         "📊 Sesongslutt — opprykk og nedrykk prosesseres",
}

# FIFA-vinduer (måned, dag) — start og slutt
# Basert på standard FIFA-kalender
FIFA_VINDUER = [
    ((3, 17), (3, 25)),   # Mars
    ((6, 2),  (6, 10)),   # Juni
    ((9, 1),  (9, 9)),    # September
    ((10, 6), (10, 14)),  # Oktober
    ((11, 10),(11, 18)),  # November
]


# =============================================================================
# SPILLDAG — én enkelt dag i kalenderen
# =============================================================================
class Spilldag:
    """
    Representerer én dag i spillet.
    Holder alle hendelser og kamper som skal prosesseres denne dagen.
    """
    def __init__(self, dato: datetime.date):
        self.dato = dato
        self.hendelser: list[KalenderHendelse] = []
        self.kamper: list = []          # Kamp-objekter fra liga.py / europa.py
        self.er_prosessert: bool = False

    @property
    def har_innhold(self) -> bool:
        return bool(self.hendelser or self.kamper)

    @property
    def er_kampdag(self) -> bool:
        return bool(self.kamper)

    def legg_til_hendelse(self, hendelse: KalenderHendelse):
        if hendelse not in self.hendelser:
            self.hendelser.append(hendelse)

    def legg_til_kamp(self, kamp):
        self.kamper.append(kamp)

    def __repr__(self):
        return (
            f"<Spilldag: {self.dato.strftime('%d.%m.%Y')}, "
            f"{len(self.hendelser)} hendelser, "
            f"{len(self.kamper)} kamper>"
        )


# =============================================================================
# TERMINLISTE-GENERATOR
# Fordeler 30 serierunder på datoer mellom 15. mars og 6. desember
# =============================================================================
class TerminlisteGenerator:
    """
    Fordeler serierunder på søndager mellom seriestart og seriefinale.
    Unngår konflikter med faste hendelser og sikrer minimum 2 dagers mellomrom
    per lag mellom kamper.
    """

    def __init__(
        self,
        seriestart: datetime.date,
        seriefinale: datetime.date,
        opptatte_datoer: set[datetime.date],
    ):
        self.seriestart = seriestart
        self.seriefinale = seriefinale
        self.opptatte_datoer = opptatte_datoer   # Faste hendelser som blokkerer

    def generer_rundeplan(self, antall_runder: int = 30) -> list[datetime.date]:
        """
        Returnerer en liste med én dato per runde.
        Runde 29 og 30 får samme dato (seriefinale-helgen).
        """
        tilgjengelige = self._finn_søndager()

        if len(tilgjengelige) < antall_runder - 1:
            raise ValueError(
                f"Ikke nok søndager ({len(tilgjengelige)}) "
                f"til {antall_runder} runder!"
            )

        # Fordel runde 1–28 jevnt, runde 29 og 30 = seriefinale
        runde_datoer = []
        steg = len(tilgjengelige) // (antall_runder - 2)
        for i in range(antall_runder - 2):
            indeks = min(i * steg, len(tilgjengelige) - 1)
            runde_datoer.append(tilgjengelige[indeks])

        # Runde 29 og 30 spilles samme dag (seriefinale-søndagen)
        finale_sondag = self._finn_forrige_sondag(self.seriefinale)
        runde_datoer.append(finale_sondag)
        runde_datoer.append(finale_sondag)

        return runde_datoer

    def _finn_søndager(self) -> list[datetime.date]:
        """Returnerer alle søndager mellom seriestart og seriefinale som ikke er opptatt."""
        søndager = []
        dato = self.seriestart
        # Start på første søndag etter seriestart
        while dato.weekday() != 6:
            dato += datetime.timedelta(days=1)

        while dato < self.seriefinale:
            if dato not in self.opptatte_datoer:
                søndager.append(dato)
            dato += datetime.timedelta(days=7)

        return søndager

    def _finn_forrige_sondag(self, dato: datetime.date) -> datetime.date:
        while dato.weekday() != 6:
            dato -= datetime.timedelta(days=1)
        return dato

    def finn_ledig_kampdag(
        self,
        lag_opptatte_datoer: set[datetime.date],
        tidligst: datetime.date,
        foretrukket_ukedag: int = 6,   # 6 = søndag
        min_mellomrom: int = 2,
    ) -> datetime.date:
        """
        Finner første ledige dato for et spesifikt lag.
        Respekterer minimum mellomrom mellom kamper.
        Prøver foretrukket ukedag først, faller tilbake på nærmeste ledige dag.
        """
        dato = tidligst
        # Prøv foretrukket ukedag
        kandidat = dato
        while kandidat.weekday() != foretrukket_ukedag:
            kandidat += datetime.timedelta(days=1)

        for _ in range(14):   # Prøv to uker frem
            if self._er_ledig(kandidat, lag_opptatte_datoer, min_mellomrom):
                return kandidat
            kandidat += datetime.timedelta(days=7)

        # Fallback: finn nærmeste ledige dag
        kandidat = dato
        for _ in range(30):
            if self._er_ledig(kandidat, lag_opptatte_datoer, min_mellomrom):
                return kandidat
            kandidat += datetime.timedelta(days=1)

        return dato   # Siste utvei

    def _er_ledig(
        self,
        dato: datetime.date,
        lag_opptatte_datoer: set[datetime.date],
        min_mellomrom: int,
    ) -> bool:
        for opptatt in lag_opptatte_datoer:
            if abs((dato - opptatt).days) < min_mellomrom:
                return False
        return dato not in self.opptatte_datoer


# =============================================================================
# SPILLKALENDEREN — hjertet i spillet
# =============================================================================
class SpillKalender:
    """
    Hjertet i spillet. Holder styr på alle hendelser, kamper og datoer.

    Spilleren navigerer fra hendelse til hendelse —
    stille perioder hoppes over automatisk.
    """

    def __init__(self, start_aar: int = 2026):
        self.start_aar = start_aar
        self.dagens_dato = datetime.date(start_aar, 1, 1)

        # Alle spilldager med innhold, indeksert på dato
        self.dager: dict[datetime.date, Spilldag] = {}

        # Overgangsvindu-tilstand
        self._overgangsvindu_aapent: bool = True   # Starter 1. jan

        # Faste årshjul-hendelser
        self._faste_hendelser: dict[tuple, KalenderHendelse] = {
            (1, 1):   KalenderHendelse.OVERGANG_1_AAPNER,
            (2, 28):  KalenderHendelse.OVERGANG_1_LUKKER,
            (3, 5):   KalenderHendelse.CUP_RUNDE_4,
            (3, 15):  KalenderHendelse.SERIESTART,
            (3, 18):  KalenderHendelse.CUP_RUNDE_5,
            (4, 22):  KalenderHendelse.CUP_SEMIFINALE,
            (5, 9):   KalenderHendelse.CUP_FINALE,
            (6, 1):   KalenderHendelse.OVERGANG_2_AAPNER,
            (7, 15):  KalenderHendelse.EUROPA_KVALIK_START,
            (8, 13):  KalenderHendelse.CUP_RUNDE_1,
            (8, 27):  KalenderHendelse.CUP_RUNDE_2,
            (9, 18):  KalenderHendelse.CUP_RUNDE_3,
            (10, 31): KalenderHendelse.OVERGANG_2_LUKKER,
            (12, 6):  KalenderHendelse.SERIEFINALE,
            (12, 10): KalenderHendelse.SESONGSLUTT,
            (12, 31): KalenderHendelse.NYTT_AAR,
        }

        # Bygg kalenderen for hele året
        self._bygg_aarskalender()

    # =========================================================================
    # BYGGING AV KALENDEREN
    # =========================================================================
    def _bygg_aarskalender(self):
        """Populerer self.dager med alle faste hendelser og FIFA-vinduer."""
        aar = self.start_aar

        # Faste hendelser
        for (mnd, dag), hendelse in self._faste_hendelser.items():
            dato = datetime.date(aar, mnd, dag)
            self._hent_eller_opprett_dag(dato).legg_til_hendelse(hendelse)

        # FIFA-vinduer
        for (start_mnd, start_dag), (slutt_mnd, slutt_dag) in FIFA_VINDUER:
            start = datetime.date(aar, start_mnd, start_dag)
            slutt = datetime.date(aar, slutt_mnd, slutt_dag)
            self._hent_eller_opprett_dag(start).legg_til_hendelse(
                KalenderHendelse.FIFA_VINDU_START
            )
            self._hent_eller_opprett_dag(slutt).legg_til_hendelse(
                KalenderHendelse.FIFA_VINDU_SLUTT
            )

    def _hent_eller_opprett_dag(self, dato: datetime.date) -> Spilldag:
        if dato not in self.dager:
            self.dager[dato] = Spilldag(dato)
        return self.dager[dato]

    def populer_serierunder(self, terminliste: list):
        """
        Tar imot terminlisten fra liga.py og legger kampene inn i kalenderen.
        Genererer datoer for alle 30 runder og plasserer kampene på riktige dager.

        terminliste: liste av lister — [[kamp1, kamp2, ...], [kamp1, ...], ...]
                     én underliste per runde
        """
        aar = self.start_aar
        seriestart  = datetime.date(aar, 3, 15)
        seriefinale = datetime.date(aar, 12, 6)

        opptatte = {dato for dato in self.dager if self.dager[dato].har_innhold}
        generator = TerminlisteGenerator(seriestart, seriefinale, opptatte)
        runde_datoer = generator.generer_rundeplan(antall_runder=len(terminliste))

        for i, (dato, runde_kamper) in enumerate(zip(runde_datoer, terminliste)):
            dag = self._hent_eller_opprett_dag(dato)
            # Runde 29 og 30 får SERIEFINALE-hendelse, resten SERIERUNDE
            if i >= len(terminliste) - 2:
                dag.legg_til_hendelse(KalenderHendelse.SERIEFINALE)
            else:
                dag.legg_til_hendelse(KalenderHendelse.SERIERUNDE)
            for kamp in runde_kamper:
                dag.legg_til_kamp(kamp)

        print(f"[Kalender] {len(terminliste)} serierunder lagt inn.")

    def legg_til_europakamp(self, dato: datetime.date, kamp):
        """Legger til en europakamp på en spesifikk dato."""
        dag = self._hent_eller_opprett_dag(dato)
        dag.legg_til_hendelse(KalenderHendelse.EUROPA_KAMPDAG)
        dag.legg_til_kamp(kamp)

    # =========================================================================
    # NAVIGASJON — hjerterytmen
    # =========================================================================
    def hopp_til_neste_hendelse(self) -> Spilldag:
        """
        Spoler frem til neste dag med hendelser eller kamper.
        Dette er primærmetoden for å navigere i spillet.
        Stille dager hoppes over automatisk.
        """
        dato = self.dagens_dato + datetime.timedelta(days=1)
        slutt = datetime.date(self.start_aar, 12, 31)

        while dato <= slutt:
            if dato in self.dager and self.dager[dato].har_innhold:
                self.dagens_dato = dato
                return self.dager[dato]
            dato += datetime.timedelta(days=1)

        # Ingenting mer dette året
        self.dagens_dato = slutt
        return Spilldag(slutt)

    def simuler_neste_dag(self) -> Spilldag:
        """
        Går én enkelt dag frem — for situasjoner der spilleren
        vil ha finere kontroll (f.eks. midt i overgangsvinduet).
        """
        self.dagens_dato += datetime.timedelta(days=1)
        mnd_dag = (self.dagens_dato.month, self.dagens_dato.day)

        dag = self._hent_eller_opprett_dag(self.dagens_dato)

        # Sjekk årshjulet
        if mnd_dag in self._faste_hendelser:
            dag.legg_til_hendelse(self._faste_hendelser[mnd_dag])

        return dag

    # =========================================================================
    # TILSTANDSSJEKKER
    # =========================================================================
    @property
    def overgangsvindu_aapent(self) -> bool:
        """Returnerer True hvis overgangsvinduet er åpent akkurat nå."""
        mnd = self.dagens_dato.month
        dag = self.dagens_dato.day
        aar = self.dagens_dato.year

        vindu_1 = (
            datetime.date(aar, 1, 1) <= self.dagens_dato <= datetime.date(aar, 2, 28)
        )
        vindu_2 = (
            datetime.date(aar, 6, 1) <= self.dagens_dato <= datetime.date(aar, 10, 31)
        )
        return vindu_1 or vindu_2

    @property
    def er_i_fifa_vindu(self) -> bool:
        """Returnerer True hvis spillere kan kalles inn til landslag."""
        for (sm, sd), (em, ed) in FIFA_VINDUER:
            aar = self.dagens_dato.year
            start = datetime.date(aar, sm, sd)
            slutt = datetime.date(aar, em, ed)
            if start <= self.dagens_dato <= slutt:
                return True
        return False

    @property
    def dager_til_neste_kamp(self) -> Optional[int]:
        """Returnerer antall dager til neste kampdag, eller None."""
        dato = self.dagens_dato + datetime.timedelta(days=1)
        for i in range(1, 120):
            if dato in self.dager and self.dager[dato].er_kampdag:
                return i
            dato += datetime.timedelta(days=1)
        return None

    # =========================================================================
    # VISNING
    # =========================================================================
    @property
    def formatert_dato(self) -> str:
        maaneder = [
            "Januar", "Februar", "Mars", "April", "Mai", "Juni",
            "Juli", "August", "September", "Oktober", "November", "Desember"
        ]
        d = self.dagens_dato
        return f"{d.day}. {maaneder[d.month - 1]} {d.year}"

    def print_kommende_hendelser(self, antall: int = 5):
        """Skriver ut de neste N hendelsene — nyttig for spillerens planlegging."""
        print(f"\n  Kommende hendelser:")
        funnet = 0
        dato = self.dagens_dato + datetime.timedelta(days=1)
        while funnet < antall and dato <= datetime.date(self.start_aar, 12, 31):
            if dato in self.dager and self.dager[dato].har_innhold:
                dag = self.dager[dato]
                for h in dag.hendelser:
                    tekst = HENDELSE_TEKST.get(h, h.name)
                    print(f"    {dato.strftime('%d.%m')}  {tekst}")
                    funnet += 1
            dato += datetime.timedelta(days=1)

    def __repr__(self):
        return (
            f"<SpillKalender: {self.formatert_dato}, "
            f"{len(self.dager)} dager med innhold>"
        )


# =============================================================================
# SPILLSLØYFEN — The Game Loop
# =============================================================================
def start_spill():
    """
    Enkel tekstbasert spillsløyfe.
    I en fullstendig versjon erstattes denne av et GUI eller richer TUI.
    """
    kalender = SpillKalender(start_aar=2026)

    print("=" * 55)
    print("  Velkommen til Norsk Fotballmanager")
    print("=" * 55)
    print(f"  Dato: {kalender.formatert_dato}")
    kalender.print_kommende_hendelser()

    while True:
        print(f"\n[{kalender.formatert_dato}]", end="  ")

        if kalender.overgangsvindu_aapent:
            print("🔓 Overgangsvindu åpent", end="  ")
        if kalender.er_i_fifa_vindu:
            print("🌐 FIFA-vindu", end="  ")

        neste = kalender.dager_til_neste_kamp
        if neste is not None:
            print(f"⚽ Neste kamp om {neste} dager", end="")
        print()

        valg = input(
            "  [Enter] Hopp til neste hendelse  "
            "[d] Én dag frem  "
            "[k] Kommende hendelser  "
            "[q] Avslutt\n  > "
        ).strip().lower()

        if valg == "q":
            print("\n  Vi ses neste gang!")
            break

        elif valg == "d":
            dag = kalender.simuler_neste_dag()
            if dag.har_innhold:
                _prosesser_dag(dag)

        elif valg == "k":
            kalender.print_kommende_hendelser(antall=8)

        else:
            # Standard: hopp til neste hendelse
            dag = kalender.hopp_til_neste_hendelse()
            _prosesser_dag(dag)


def _prosesser_dag(dag: Spilldag):
    """Skriver ut og håndterer alle hendelser på en spilldag."""
    print(f"\n  {'=' * 50}")
    for hendelse in dag.hendelser:
        tekst = HENDELSE_TEKST.get(hendelse, hendelse.name)
        print(f"  {tekst}")

        # Her kobles resten av spillet på:
        if hendelse == KalenderHendelse.SERIESTART:
            pass   # → liga.py: simuler_runde(1)
        elif hendelse == KalenderHendelse.SERIEFINALE:
            pass   # → liga.py: simuler_runde(30), alle kamper simultant
        elif hendelse == KalenderHendelse.CUP_FINALE:
            pass   # → cup.py: spill_finale()
        elif hendelse == KalenderHendelse.SESONGSLUTT:
            pass   # → liga.py: gjennomfoer_direkte_opp_nedrykk()
                   # → liga.py: generer_kvalifiseringer()
                   # → europa.py: fordel_norske_europaplasser()
        elif hendelse == KalenderHendelse.NYTT_AAR:
            pass   # → reset og bygg ny kalender for neste år

    if dag.kamper:
        print(f"\n  Dagens kamper ({len(dag.kamper)}):")
        for kamp in dag.kamper:
            print(f"    {kamp}")
    print(f"  {'=' * 50}")


# =============================================================================
if __name__ == "__main__":
    start_spill()
