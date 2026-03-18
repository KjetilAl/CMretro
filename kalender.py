"""
kalender.py  –  Norsk Football Manager '95
Sesongkalender, dagssimulering og økonomiflyt.

Hvert spill-år varer 1. januar – 31. desember.
SpillKalender er den sentrale klokken i spillet:

  ● Simulerer én dag av gangen
  ● Distribuerer kampdatoer fra liga.py, cup.py og europa.py
  ● Styrer overgangsvindu 1 (jan–feb) og 2 (jun–okt)
  ● Betaler lønn til alle klubber hver mandag
  ● Krediterer billettinntekter direkte etter hjemmekamper
  ● Eksponerer klare integrasjonspunkter (hooks) for turneringssystemene
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from klubb import Klubb


# =============================================================================
# HENDELSESTYPER
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
    SERIEFINALE         = auto()   # Runde 29+30 — alt avgjøres

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

    # Økonomi
    LONN_BETALT         = auto()   # Mandag — generert automatisk
    SESONG_SPONSOR      = auto()   # Sesongstart-sponsor

    # System
    SESONGSLUTT         = auto()   # Opprykk/nedrykk prosesseres
    NYTT_AAR            = auto()


HENDELSE_TEKST: dict[KalenderHendelse, str] = {
    KalenderHendelse.OVERGANG_1_AAPNER:   "Overgangsvindu 1 åpner",
    KalenderHendelse.OVERGANG_1_LUKKER:   "Overgangsvindu 1 lukker",
    KalenderHendelse.OVERGANG_2_AAPNER:   "Overgangsvindu 2 åpner",
    KalenderHendelse.OVERGANG_2_LUKKER:   "Overgangsvindu 2 lukker",
    KalenderHendelse.SERIESTART:          "Seriestart! Eliteserien runde 1",
    KalenderHendelse.SERIERUNDE:          "Serierunde",
    KalenderHendelse.SERIEFINALE:         "Runde 30 — Alt avgjøres i dag!",
    KalenderHendelse.CUP_RUNDE_1:        "NM-cup: 1. runde",
    KalenderHendelse.CUP_RUNDE_2:        "NM-cup: 2. runde",
    KalenderHendelse.CUP_RUNDE_3:        "NM-cup: 3. runde",
    KalenderHendelse.CUP_RUNDE_4:        "NM-cup: 4. runde",
    KalenderHendelse.CUP_RUNDE_5:        "NM-cup: 5. runde",
    KalenderHendelse.CUP_SEMIFINALE:     "NM-cup: Semifinale",
    KalenderHendelse.CUP_FINALE:         "NM-cup: FINALE på Ullevaal!",
    KalenderHendelse.EUROPA_KVALIK_START: "Europacup-kvalifisering starter",
    KalenderHendelse.EUROPA_KAMPDAG:      "Europacup-kampdag",
    KalenderHendelse.FIFA_VINDU_START:    "FIFA-vindu åpner",
    KalenderHendelse.FIFA_VINDU_SLUTT:    "FIFA-vindu lukker",
    KalenderHendelse.LONN_BETALT:         "Lønnsutbetaling",
    KalenderHendelse.SESONG_SPONSOR:      "Sponsorinntekt utbetalt",
    KalenderHendelse.SESONGSLUTT:         "Sesongslutt — opprykk/nedrykk",
    KalenderHendelse.NYTT_AAR:            "Godt nytt år!",
}

# Faste årshjul-datoer  (måned, dag) → hendelse
FASTE_HENDELSER: dict[tuple[int, int], KalenderHendelse] = {
    (1,  1):  KalenderHendelse.OVERGANG_1_AAPNER,
    (2, 28):  KalenderHendelse.OVERGANG_1_LUKKER,
    (3,  5):  KalenderHendelse.CUP_RUNDE_4,
    (3, 15):  KalenderHendelse.SERIESTART,
    (3, 18):  KalenderHendelse.CUP_RUNDE_5,
    (4, 22):  KalenderHendelse.CUP_SEMIFINALE,
    (5,  9):  KalenderHendelse.CUP_FINALE,
    (6,  1):  KalenderHendelse.OVERGANG_2_AAPNER,
    (7, 15):  KalenderHendelse.EUROPA_KVALIK_START,
    (8, 13):  KalenderHendelse.CUP_RUNDE_1,
    (8, 27):  KalenderHendelse.CUP_RUNDE_2,
    (9, 18):  KalenderHendelse.CUP_RUNDE_3,
    (10, 31): KalenderHendelse.OVERGANG_2_LUKKER,
    (12,  6): KalenderHendelse.SERIEFINALE,
    (12, 10): KalenderHendelse.SESONGSLUTT,
    (12, 31): KalenderHendelse.NYTT_AAR,
}

# FIFA-internasjonale vinduer  (start_mnd, start_dag), (slutt_mnd, slutt_dag)
FIFA_VINDUER: list[tuple[tuple[int, int], tuple[int, int]]] = [
    ((3, 17), (3, 25)),
    ((6,  2), (6, 10)),
    ((9,  1), (9,  9)),
    ((10, 6), (10, 14)),
    ((11, 10), (11, 18)),
]


# =============================================================================
# ØKONOMI-KVITTERING
# =============================================================================

@dataclass
class OkonomiKvittering:
    """Oppsummering av ett dags økonomiflyt for én klubb."""
    klubb_id:   str
    dato:       datetime.date
    lonn:       int = 0
    vedlikehold: int = 0
    billetter:  int = 0
    sponsor:    int = 0
    netto:      int = 0   # billetter + sponsor − lonn − vedlikehold


# =============================================================================
# KAMPREGISTRERING
# Brukes av liga.py / cup.py / europa.py til å melde inn kamper
# =============================================================================

@dataclass
class KampInfo:
    """
    Metadata om én kamp som skal simuleres på en gitt dato.
    kamp-objektet er hentet fra liga/cup/europa — kalender berører ikke innmaten.
    """
    kamp:           object              # Kamp/CupKamp/EuropaKamp
    hjemmelag:      Optional["Klubb"]   # None for rene LOD-0-kamper
    bortelag:       Optional["Klubb"]   # None for rene LOD-0-kamper
    turnering:      str                 # "serie" | "cup" | "europa"
    er_nøytral:     bool = False        # Cup-finale / europakamper på nøytralbane
    billettpris:    int  = 150          # NOK per tilskuer


# =============================================================================
# SPILLDAG
# =============================================================================

class Spilldag:
    """
    Én enkelt dag i spillet.
    Holder hendelser og kamper som prosesseres denne dagen.
    """

    def __init__(self, dato: datetime.date) -> None:
        self.dato:            datetime.date        = dato
        self.hendelser:       list[KalenderHendelse] = []
        self.kamper:          list[KampInfo]         = []
        self.er_prosessert:   bool                   = False

        # Økonomi-logg for dagen (fylles ut av SpillKalender.prosesser_dag)
        self.okonomi_logg:    list[OkonomiKvittering] = []

    @property
    def har_innhold(self) -> bool:
        return bool(self.hendelser or self.kamper)

    @property
    def er_kampdag(self) -> bool:
        return bool(self.kamper)

    @property
    def er_mandag(self) -> bool:
        return self.dato.weekday() == 0

    def legg_til_hendelse(self, hendelse: KalenderHendelse) -> None:
        if hendelse not in self.hendelser:
            self.hendelser.append(hendelse)

    def legg_til_kamp(self, info: KampInfo) -> None:
        self.kamper.append(info)

    def __repr__(self) -> str:
        return (
            f"<Spilldag {self.dato.strftime('%d.%m.%Y')} "
            f"hendelser={len(self.hendelser)} "
            f"kamper={len(self.kamper)}>"
        )


# =============================================================================
# TERMINLISTE-GENERATOR
# Fordeler N runder på søndager mellom seriestart og seriefinale
# =============================================================================

class TerminlisteGenerator:
    """
    Fordeler serierunder på søndager mellom seriestart og seriefinale.
    Unngår datoer som allerede er blokkert av faste hendelser.
    """

    def __init__(
        self,
        seriestart:    datetime.date,
        seriefinale:   datetime.date,
        opptatte:      set[datetime.date],
    ) -> None:
        self.seriestart   = seriestart
        self.seriefinale  = seriefinale
        self.opptatte     = opptatte

    def generer_rundeplan(self, antall_runder: int = 30) -> list[datetime.date]:
        """
        Returnerer én dato per runde.
        Runde 29 og 30 legges begge på seriefinale-søndagen.
        """
        søndager = self._finn_søndager()

        # Vi trenger datoer for runde 1–28 (runde 29+30 = seriefinale)
        nødvendige = antall_runder - 2
        if len(søndager) < nødvendige:
            raise ValueError(
                f"Ikke nok søndager ({len(søndager)}) for {nødvendige} runder "
                f"(av {antall_runder} totalt)"
            )

        steg      = max(1, len(søndager) // nødvendige)
        datoer    = [søndager[min(i * steg, len(søndager) - 1)]
                     for i in range(nødvendige)]

        # Runde 29 og 30 → seriefinale-søndagen
        finale_søndag = self._forrige_søndag(self.seriefinale)
        datoer.append(finale_søndag)
        datoer.append(finale_søndag)
        return datoer

    # ── private ──────────────────────────────────────────────────────────────

    def _finn_søndager(self) -> list[datetime.date]:
        søndager: list[datetime.date] = []
        dato = self.seriestart
        while dato.weekday() != 6:          # frem til første søndag
            dato += datetime.timedelta(days=1)
        while dato < self.seriefinale:
            if dato not in self.opptatte:
                søndager.append(dato)
            dato += datetime.timedelta(days=7)
        return søndager

    @staticmethod
    def _forrige_søndag(dato: datetime.date) -> datetime.date:
        while dato.weekday() != 6:
            dato -= datetime.timedelta(days=1)
        return dato


# =============================================================================
# SPILLKALENDEREN  —  den sentrale klokken
# =============================================================================

class SpillKalender:
    """
    Den sentrale klokken i spillet.

    Ansvar:
      • Administrere alle dager fra 1. januar til 31. desember
      • Holde styr på overgangsvindu og FIFA-vinduer
      • Ta imot kamper fra liga.py, cup.py og europa.py og plassere dem på datoer
      • Betale lønn til alle klubber hver mandag
      • Kreditere billettinntekter etter hjemmekamper
      • Eksponere klare integrasjonspunkter (on_*-callbacks) for turneringssystemer

    Bruk:
        kalender = SpillKalender(start_aar=2026, alle_klubber=alle_klubber)
        kalender.registrer_liga(liga_system)
        kalender.registrer_cup(cup_motor)
        kalender.registrer_europa(europa_system)

        # Hent en dag med hendelser
        dag = kalender.neste_dag_med_innhold()
        # eller: simuler én dag av gangen
        dag = kalender.simuler_neste_dag()
    """

    def __init__(
        self,
        start_aar:    int,
        alle_klubber: list["Klubb"] | None = None,
    ) -> None:
        self.start_aar    = start_aar
        self.alle_klubber: list["Klubb"] = alle_klubber or []
        self.dagens_dato  = datetime.date(start_aar, 1, 1)

        # Alle spilldager (inkl. stille dager uten events — opprettes ved behov)
        self._dager: dict[datetime.date, Spilldag] = {}

        # Turneringssystemer  (settes av registrer_*-metodene)
        self._liga:   object | None = None
        self._cup:    object | None = None
        self._europa: object | None = None

        # Callbacks fra turneringssystemene
        # Kalles av kalender når spesifikk hendelse inntreffer
        # Signatur: (dato: datetime.date, hendelse: KalenderHendelse) → None
        self.on_seriestart:    Callable | None = None
        self.on_serierunde:    Callable | None = None
        self.on_seriefinale:   Callable | None = None
        self.on_cup_runde:     Callable | None = None   # kalles med rundenummer
        self.on_cup_finale:    Callable | None = None
        self.on_europa_kampdag:Callable | None = None
        self.on_sesongslutt:   Callable | None = None
        self.on_nytt_aar:      Callable | None = None

        # Logg
        self.okonomi_logg: list[OkonomiKvittering] = []

        # Bygg årshjulet
        self._bygg_aarskalender()

    # =========================================================================
    # REGISTRERING AV TURNERINGSSYSTEMER
    # =========================================================================

    def registrer_liga(self, liga) -> None:
        self._liga = liga

    def registrer_cup(self, cup) -> None:
        self._cup = cup

    def registrer_europa(self, europa) -> None:
        self._europa = europa

    def registrer_klubber(self, klubber: list["Klubb"]) -> None:
        self.alle_klubber = klubber

    # =========================================================================
    # REGISTRERING AV KAMPER  (kalles av liga.py / cup.py / europa.py)
    # =========================================================================

    def populer_serierunder(self, terminliste: list[list]) -> None:
        """
        Tar imot terminlisten fra liga.py og plasserer kampene i kalenderen.

        terminliste: liste av runder — [[kamp1, kamp2, ...], [kamp1, ...], ...]
                     Hvert kamp-objekt forventes å ha attributtene
                     .hjemmelag og .bortelag (Klubb-instanser).
        """
        aar         = self.start_aar
        seriestart  = datetime.date(aar, 3, 15)
        seriefinale = datetime.date(aar, 12, 6)

        opptatte    = {d for d, s in self._dager.items() if s.har_innhold}
        generator   = TerminlisteGenerator(seriestart, seriefinale, opptatte)
        runde_datoer = generator.generer_rundeplan(antall_runder=len(terminliste))

        for i, (dato, kamper_i_runde) in enumerate(
            zip(runde_datoer, terminliste)
        ):
            dag = self._hent_eller_opprett(dato)
            er_finale = i >= len(terminliste) - 2
            dag.legg_til_hendelse(
                KalenderHendelse.SERIEFINALE if er_finale
                else KalenderHendelse.SERIERUNDE
            )

            for kamp in kamper_i_runde:
                hjemme = getattr(kamp, "hjemmelag", None)
                borte  = getattr(kamp, "bortelag",  None)
                dag.legg_til_kamp(KampInfo(
                    kamp=kamp,
                    hjemmelag=hjemme,
                    bortelag=borte,
                    turnering="serie",
                    billettpris=150,
                ))

        print(f"[Kalender] {len(terminliste)} serierunder lagt inn.")

    def legg_til_cupkamp(
        self,
        dato:       datetime.date,
        kamp,
        runde:      int,
        nøytral:    bool    = False,
        billettpris: int    = 150,
    ) -> None:
        """
        Legger til én cup-kamp på gitt dato.
        Kalles av cup.py for hver kamp i turneringen.
        """
        _cup_hendelse = {
            1: KalenderHendelse.CUP_RUNDE_1,
            2: KalenderHendelse.CUP_RUNDE_2,
            3: KalenderHendelse.CUP_RUNDE_3,
            4: KalenderHendelse.CUP_RUNDE_4,
            5: KalenderHendelse.CUP_RUNDE_5,
            6: KalenderHendelse.CUP_SEMIFINALE,
            7: KalenderHendelse.CUP_FINALE,
        }
        dag = self._hent_eller_opprett(dato)
        hendelse = _cup_hendelse.get(runde)
        if hendelse:
            dag.legg_til_hendelse(hendelse)

        hjemme = None if nøytral else getattr(kamp, "hjemmelag", None)
        borte  = getattr(kamp, "bortelag", None)
        dag.legg_til_kamp(KampInfo(
            kamp=kamp,
            hjemmelag=hjemme,
            bortelag=borte,
            turnering="cup",
            er_nøytral=nøytral,
            billettpris=billettpris,
        ))

    def legg_til_europakamp(
        self,
        dato:        datetime.date,
        kamp,
        billettpris: int = 200,
    ) -> None:
        """
        Legger til én europakamp på gitt dato.
        Kalles av europa.py for kamper der norsk lag er involvert.
        """
        dag = self._hent_eller_opprett(dato)
        dag.legg_til_hendelse(KalenderHendelse.EUROPA_KAMPDAG)
        hjemme = getattr(kamp, "hjemmelag", None)
        borte  = getattr(kamp, "bortelag",  None)
        dag.legg_til_kamp(KampInfo(
            kamp=kamp,
            hjemmelag=hjemme,
            bortelag=borte,
            turnering="europa",
            billettpris=billettpris,
        ))

    # =========================================================================
    # NAVIGASJON — dag-for-dag-simulering
    # =========================================================================

    def simuler_neste_dag(self) -> Spilldag:
        """
        Avanserer én dag og prosesserer alle hendelser og økonomi for den dagen.
        Dette er primærmetoden for spillsløyfen.

        Returnerer Spilldag-objektet for den nye dagens-datoen.
        """
        self.dagens_dato += datetime.timedelta(days=1)
        dag = self._hent_eller_opprett(self.dagens_dato)

        # Sjekk faste hendelser fra årshjulet
        mnd_dag = (self.dagens_dato.month, self.dagens_dato.day)
        if mnd_dag in FASTE_HENDELSER:
            dag.legg_til_hendelse(FASTE_HENDELSER[mnd_dag])

        # Sjekk FIFA-vinduer
        for (sm, sd), (em, ed) in FIFA_VINDUER:
            aar = self.start_aar
            if self.dagens_dato == datetime.date(aar, sm, sd):
                dag.legg_til_hendelse(KalenderHendelse.FIFA_VINDU_START)
            if self.dagens_dato == datetime.date(aar, em, ed):
                dag.legg_til_hendelse(KalenderHendelse.FIFA_VINDU_SLUTT)

        # ── Økonomi: lønn hver mandag ─────────────────────────────────────────
        if dag.er_mandag and self.alle_klubber:
            self._betal_lønn(dag)

        # ── Kamper: billettinntekter ──────────────────────────────────────────
        if dag.er_kampdag:
            self._prosesser_kampøkonomi(dag)

        # ── Callbacks til turneringssystemene ─────────────────────────────────
        self._kjør_callbacks(dag)

        dag.er_prosessert = True
        return dag

    def neste_dag_med_innhold(self) -> Spilldag:
        """
        Spoler frem til neste dag med hendelser eller kamper.
        Internt kalles simuler_neste_dag() for ALLE mellomliggende dager
        slik at økonomi (lønn hver mandag) alltid prosesseres korrekt.
        """
        slutt = datetime.date(self.start_aar, 12, 31)
        dag   = None

        while self.dagens_dato < slutt:
            dag = self.simuler_neste_dag()
            if dag.har_innhold:
                return dag

        # Årets slutt
        return dag or Spilldag(self.dagens_dato)

    # =========================================================================
    # TILSTANDSSJEKKER
    # =========================================================================

    @property
    def overgangsvindu_aapent(self) -> bool:
        """True mens overgangsvindu 1 (jan–feb) eller 2 (jun–okt) er åpent."""
        d = self.dagens_dato
        aar = d.year
        vindu1 = datetime.date(aar, 1, 1) <= d <= datetime.date(aar, 2, 28)
        vindu2 = datetime.date(aar, 6, 1) <= d <= datetime.date(aar, 10, 31)
        return vindu1 or vindu2

    @property
    def er_i_fifa_vindu(self) -> bool:
        """True mens spillere kan kalles inn til landslagsspill."""
        aar = self.dagens_dato.year
        for (sm, sd), (em, ed) in FIFA_VINDUER:
            if (datetime.date(aar, sm, sd)
                    <= self.dagens_dato
                    <= datetime.date(aar, em, ed)):
                return True
        return False

    @property
    def dager_til_neste_kamp(self) -> Optional[int]:
        """Antall dager til neste kampdag, eller None."""
        for i in range(1, 120):
            dato = self.dagens_dato + datetime.timedelta(days=i)
            dag  = self._dager.get(dato)
            if dag and dag.er_kampdag:
                return i
        return None

    @property
    def er_siste_dag(self) -> bool:
        return self.dagens_dato >= datetime.date(self.start_aar, 12, 31)

    # =========================================================================
    # VISNING
    # =========================================================================

    @property
    def formatert_dato(self) -> str:
        måneder = [
            "Januar", "Februar", "Mars", "April", "Mai", "Juni",
            "Juli", "August", "September", "Oktober", "November", "Desember",
        ]
        d = self.dagens_dato
        return f"{d.day}. {måneder[d.month - 1]} {d.year}"

    def kommende_hendelser(self, antall: int = 5) -> list[tuple[datetime.date, str]]:
        """Returnerer de N neste hendelsene som (dato, tekst)-par."""
        resultat: list[tuple[datetime.date, str]] = []
        dato = self.dagens_dato + datetime.timedelta(days=1)
        slutt = datetime.date(self.start_aar, 12, 31)

        while len(resultat) < antall and dato <= slutt:
            dag = self._dager.get(dato)
            if dag and dag.har_innhold:
                for h in dag.hendelser:
                    resultat.append((dato, HENDELSE_TEKST.get(h, h.name)))
                    if len(resultat) >= antall:
                        break
            dato += datetime.timedelta(days=1)

        return resultat

    def print_kommende_hendelser(self, antall: int = 5) -> None:
        print(f"\n  Kommende hendelser:")
        for dato, tekst in self.kommende_hendelser(antall):
            print(f"    {dato.strftime('%d.%m')}  {tekst}")

    def __repr__(self) -> str:
        return (
            f"<SpillKalender {self.formatert_dato}  "
            f"vindu={'åpent' if self.overgangsvindu_aapent else 'stengt'}  "
            f"dager_med_innhold={len(self._dager)}>"
        )

    # =========================================================================
    # PRIVATE HJELPEMETODER
    # =========================================================================

    def _bygg_aarskalender(self) -> None:
        """Populerer kalenderen med alle faste hendelser og FIFA-vinduer."""
        aar = self.start_aar

        for (mnd, dag), hendelse in FASTE_HENDELSER.items():
            dato = datetime.date(aar, mnd, dag)
            self._hent_eller_opprett(dato).legg_til_hendelse(hendelse)

        for (sm, sd), (em, ed) in FIFA_VINDUER:
            start = datetime.date(aar, sm, sd)
            slutt = datetime.date(aar, em, ed)
            self._hent_eller_opprett(start).legg_til_hendelse(
                KalenderHendelse.FIFA_VINDU_START
            )
            self._hent_eller_opprett(slutt).legg_til_hendelse(
                KalenderHendelse.FIFA_VINDU_SLUTT
            )

    def _hent_eller_opprett(self, dato: datetime.date) -> Spilldag:
        if dato not in self._dager:
            self._dager[dato] = Spilldag(dato)
        return self._dager[dato]

    # ── Økonomi ──────────────────────────────────────────────────────────────

    def _betal_lønn(self, dag: Spilldag) -> None:
        """
        Kalles hver mandag.
        Trekker ukentlige lønns- og vedlikeholdsutgifter fra alle klubbers saldo.
        """
        dag.legg_til_hendelse(KalenderHendelse.LONN_BETALT)

        for klubb in self.alle_klubber:
            kvittering_dict = klubb.betal_ukentlige_utgifter()
            kvitt = OkonomiKvittering(
                klubb_id    = klubb.id,
                dato        = dag.dato,
                lonn        = kvittering_dict.get("lonn", 0),
                vedlikehold = kvittering_dict.get("vedlikehold", 0),
                netto       = -(
                    kvittering_dict.get("lonn", 0)
                    + kvittering_dict.get("vedlikehold", 0)
                ),
            )
            dag.okonomi_logg.append(kvitt)
            self.okonomi_logg.append(kvitt)

    def _prosesser_kampøkonomi(self, dag: Spilldag) -> None:
        """
        Etter simulering av kamper:
        krediterer billettinntekter til hjemmelagets konto.

        Merk: selve kampsimulasjonen (LOD 1) utføres av kampmotor.py
        og kalles fra spillmotor_pygame.py / turneringssystemene.
        Denne metoden håndterer kun økonomiflytdelen.
        """
        for info in dag.kamper:
            if info.hjemmelag is None:
                continue   # Nøytralbane eller rent LOD-0-oppgjør
            if info.er_nøytral:
                continue   # Cup-finale etc. — ingen hjemmelagsfordel

            hjemme = info.hjemmelag
            borte  = info.bortelag
            motstander_rykte = (
                getattr(borte, "historisk_suksess", 10)
                if borte else 10
            )

            tilskuere, inntekt = hjemme.beregn_billettinntekter(
                motstander_rykte=motstander_rykte,
                billettpris=info.billettpris,
            )

            kvitt = OkonomiKvittering(
                klubb_id   = hjemme.id,
                dato       = dag.dato,
                billetter  = inntekt,
                netto      = inntekt,
            )
            dag.okonomi_logg.append(kvitt)
            self.okonomi_logg.append(kvitt)

    # ── Callbacks ────────────────────────────────────────────────────────────

    def _kjør_callbacks(self, dag: Spilldag) -> None:
        """Kaller registrerte hooks basert på dagens hendelser."""
        for hendelse in dag.hendelser:
            if hendelse == KalenderHendelse.SERIESTART and self.on_seriestart:
                self.on_seriestart(dag.dato, hendelse)

            elif hendelse == KalenderHendelse.SERIERUNDE and self.on_serierunde:
                self.on_serierunde(dag.dato, hendelse)

            elif hendelse == KalenderHendelse.SERIEFINALE and self.on_seriefinale:
                self.on_seriefinale(dag.dato, hendelse)

            elif hendelse in (
                KalenderHendelse.CUP_RUNDE_1,
                KalenderHendelse.CUP_RUNDE_2,
                KalenderHendelse.CUP_RUNDE_3,
                KalenderHendelse.CUP_RUNDE_4,
                KalenderHendelse.CUP_RUNDE_5,
                KalenderHendelse.CUP_SEMIFINALE,
            ) and self.on_cup_runde:
                _runde_nr = {
                    KalenderHendelse.CUP_RUNDE_1: 1,
                    KalenderHendelse.CUP_RUNDE_2: 2,
                    KalenderHendelse.CUP_RUNDE_3: 3,
                    KalenderHendelse.CUP_RUNDE_4: 4,
                    KalenderHendelse.CUP_RUNDE_5: 5,
                    KalenderHendelse.CUP_SEMIFINALE: 6,
                }[hendelse]
                self.on_cup_runde(dag.dato, hendelse, _runde_nr)

            elif hendelse == KalenderHendelse.CUP_FINALE and self.on_cup_finale:
                self.on_cup_finale(dag.dato, hendelse)

            elif hendelse == KalenderHendelse.EUROPA_KAMPDAG and self.on_europa_kampdag:
                self.on_europa_kampdag(dag.dato, hendelse)

            elif hendelse == KalenderHendelse.SESONGSLUTT and self.on_sesongslutt:
                self.on_sesongslutt(dag.dato, hendelse)

            elif hendelse == KalenderHendelse.NYTT_AAR and self.on_nytt_aar:
                self.on_nytt_aar(dag.dato, hendelse)


# =============================================================================
# ENKEL TEKSTBASERT SPILLSLØYFE  (kjøres direkte med: python kalender.py)
# =============================================================================

def _prosesser_dag_tekst(dag: Spilldag) -> None:
    """Skriver ut hendelser og kamper for dagen i tekstmodus."""
    linje = "─" * 52
    print(f"\n  {linje}")
    for h in dag.hendelser:
        print(f"  {HENDELSE_TEKST.get(h, h.name)}")
    if dag.kamper:
        print(f"\n  Kamper ({len(dag.kamper)}):")
        for info in dag.kamper:
            kamp = info.kamp
            print(f"    {kamp}")
    if dag.okonomi_logg:
        total_lonn = sum(k.lonn for k in dag.okonomi_logg)
        total_bill = sum(k.billetter for k in dag.okonomi_logg)
        if total_lonn:
            print(f"\n  Lønnsutbetaling:   {total_lonn:>12,.0f} kr")
        if total_bill:
            print(f"  Billettinntekter:  {total_bill:>12,.0f} kr")
    print(f"  {linje}")


def start_spill() -> None:
    """Enkel tekstbasert spillsløyfe for rask testing av kalenderen."""
    kalender = SpillKalender(start_aar=2026)

    print("=" * 55)
    print("  Norsk Football Manager")
    print("=" * 55)
    print(f"  Dato: {kalender.formatert_dato}")
    kalender.print_kommende_hendelser()

    while not kalender.er_siste_dag:
        statuslinje = f"[{kalender.formatert_dato}]"
        if kalender.overgangsvindu_aapent:
            statuslinje += "  Overgangsvindu åpent"
        if kalender.er_i_fifa_vindu:
            statuslinje += "  FIFA-vindu"
        neste = kalender.dager_til_neste_kamp
        if neste is not None:
            statuslinje += f"  Neste kamp om {neste} dager"
        print(f"\n{statuslinje}")

        valg = input(
            "  [Enter] Neste hendelse  "
            "[d] Én dag  "
            "[k] Kommende  "
            "[q] Avslutt\n  > "
        ).strip().lower()

        if valg == "q":
            print("\n  Vi ses neste gang!")
            break
        elif valg == "d":
            dag = kalender.simuler_neste_dag()
            if dag.har_innhold:
                _prosesser_dag_tekst(dag)
        elif valg == "k":
            kalender.print_kommende_hendelser(antall=8)
        else:
            dag = kalender.neste_dag_med_innhold()
            _prosesser_dag_tekst(dag)


if __name__ == "__main__":
    start_spill()
