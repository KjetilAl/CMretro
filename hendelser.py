import datetime
from enum import Enum, auto
from typing import Optional
from nyhetsgenerator import generer_stordrama

# =============================================================================
# HENDELSETYPER
# =============================================================================
class HendelseType(Enum):
    # Spillerhendelser
    LAV_FORM_STREAK      = auto()   # 3 kamper under 5.0 på børsen
    HØY_FORM_STREAK      = auto()   # 3 kamper over 8.0
    BENKEVARMER          = auto()   # Ikke startet siste 5 kamper
    LANGTIDSSKADET       = auto()   # Skade over 28 dager
    FRISKMELDT           = auto()   # Tilbake fra skade
    TOPPSCORER           = auto()   # Flest mål i laget etter runde 15+

    # Lagshendelser
    TAPENDE_REKKE        = auto()   # 5 tap på rad
    VINNENDE_REKKE       = auto()   # 5 seire på rad
    KRISE                = auto()   # 8 kamper uten seier
    NEDRYKKSFARE         = auto()   # Bunn 3 etter runde 20
    OPPRYKKSSJANSE       = auto()   # Topp 2 etter runde 20

    # Europahendelser
    EUROPA_UTSLÅTT       = auto()
    EUROPA_HISTORISK_SEI = auto()   # Norsk lag slår storlag

    # Sesongshendelser
    TETT_KAMPPROGRAM     = auto()   # 3 kamper på 8 dager
    HALVVEIS_I_SESONGEN  = auto()   # Etter runde 15


# Terskelkonstanter
FORM_STREAK_LENGDE       = 3
LAV_FORM_GRENSE          = 5.0
HØY_FORM_GRENSE          = 8.0
BENK_STREAK_LENGDE       = 5
LANGTIDSSKADET_DAGER     = 28
TAP_STREAK_LENGDE        = 5
SEIER_STREAK_LENGDE      = 5
KRISE_LENGDE             = 8
NEDRYKK_RUNDE_GRENSE     = 20     # Runde etter hvilken nedrykksfare-sjekk trigges
TETT_PROGRAM_DAGER       = 8
TETT_PROGRAM_KAMPER      = 3

# Hvilke hendelser bruker Gemini (kun stordrama)
GEMINI_HENDELSER = {
    HendelseType.LAV_FORM_STREAK,
    HendelseType.HØY_FORM_STREAK,
    HendelseType.TAPENDE_REKKE,
    HendelseType.KRISE,
    HendelseType.EUROPA_HISTORISK_SEI,
    HendelseType.LANGTIDSSKADET,
}

# Ferdighetsgrense for Gemini-bruk (kun stjernespillere får AI-generert stordrama)
GEMINI_FERDIGHET_GRENSE = 15


# =============================================================================
# HENDELSE — én konkret hendelse med dato og konsekvenser
# =============================================================================
class Hendelse:
    def __init__(
        self,
        type: HendelseType,
        dato: datetime.date,
        objekt,                    # Spiller eller Klubb
        nyhet: Optional[dict] = None,
        viktighet: str = "Normal", # "Lav", "Normal", "Høy", "Krise"
    ):
        self.type      = type
        self.dato      = dato
        self.objekt    = objekt
        self.nyhet     = nyhet     # {"overskrift": ..., "ingress": ..., "tweet": ...}
        self.viktighet = viktighet
        self.lest      = False

    def __repr__(self):
        navn = getattr(self.objekt, 'etternavn',
               getattr(self.objekt, 'navn', '?'))
        return f"<Hendelse: {self.type.name} — {navn} [{self.viktighet}]>"


# =============================================================================
# HENDELSES-MANAGER
# =============================================================================
class HendelsesManager:
    """
    Observerer spilltilstanden og reagerer når terskler krysses.
    Kobler kampresultater, skader og tabellposisjoner til:
      1. Skjulte attributtendringer (person._presstoleranse etc.)
      2. Synlige nyheter i spillerens innboks
    """

    def __init__(self):
        self.nyhets_ko: list[Hendelse] = []      # Uleste nyheter
        self.historikk: list[Hendelse] = []      # Alle hendelser denne sesongen
        self._dagens_dato: Optional[datetime.date] = None

    def sett_dato(self, dato: datetime.date):
        self._dagens_dato = dato

    # =========================================================================
    # SPILLERHENDELSER
    # =========================================================================
    def registrer_kampresultat(self, spiller, rating: float, startet: bool):
        """
        Kalles av kampmotor etter hver kamp for hver spiller.
        Oppdaterer form_historikk og sjekker terskler.
        """
        if not hasattr(spiller, 'form_historikk'):
            spiller.form_historikk = []
        if not hasattr(spiller, 'starter_historikk'):
            spiller.starter_historikk = []

        spiller.form_historikk.append(round(rating, 1))
        spiller.starter_historikk.append(startet)

        # Behold bare siste 10 kamper
        spiller.form_historikk   = spiller.form_historikk[-10:]
        spiller.starter_historikk = spiller.starter_historikk[-10:]

        self.sjekk_spiller_terskler(spiller)

    def sjekk_spiller_terskler(self, spiller):
        """Sjekker alle spillerterskler og publiserer relevante hendelser."""
        historikk = getattr(spiller, 'form_historikk', [])
        starter   = getattr(spiller, 'starter_historikk', [])

        # --- Lav form streak ---
        if (len(historikk) >= FORM_STREAK_LENGDE and
                sum(historikk[-FORM_STREAK_LENGDE:]) / FORM_STREAK_LENGDE < LAV_FORM_GRENSE):
            self._publiser_spiller_hendelse(HendelseType.LAV_FORM_STREAK, spiller)

        # --- Høy form streak ---
        elif (len(historikk) >= FORM_STREAK_LENGDE and
                sum(historikk[-FORM_STREAK_LENGDE:]) / FORM_STREAK_LENGDE >= HØY_FORM_GRENSE):
            self._publiser_spiller_hendelse(HendelseType.HØY_FORM_STREAK, spiller)

        # --- Benkevarmer ---
        if (len(starter) >= BENK_STREAK_LENGDE and
                not any(starter[-BENK_STREAK_LENGDE:])):
            self._publiser_spiller_hendelse(HendelseType.BENKEVARMER, spiller)

        # --- Langtidsskadet ---
        if (getattr(spiller, 'skadet', False) and
                getattr(spiller, 'skade_dager_igjen', 0) >= LANGTIDSSKADET_DAGER):
            self._publiser_spiller_hendelse(HendelseType.LANGTIDSSKADET, spiller)

    def sjekk_friskmelding(self, spiller):
        """Kalles av kalender.py når en spiller er friskmeldt."""
        if not getattr(spiller, 'skadet', True):
            self._publiser_spiller_hendelse(HendelseType.FRISKMELDT, spiller)

    # =========================================================================
    # LAGSHENDELSER
    # =========================================================================
    def sjekk_lag_terskler(
        self,
        klubb,
        resultater: list[str],    # ["S", "T", "U", "T", "T"] — siste kamper
        tabellplass: int,
        runde_nr: int,
        antall_lag: int = 16,
    ):
        """
        Kalles etter hver kamprunde for hver klubb.
        resultater: liste med "S" (seier), "U" (uavgjort), "T" (tap)
        """
        if not resultater:
            return

        siste = resultater[-TAP_STREAK_LENGDE:]

        # --- Tapende rekke ---
        if (len(resultater) >= TAP_STREAK_LENGDE and
                all(r == "T" for r in siste)):
            self._publiser_lag_hendelse(
                HendelseType.TAPENDE_REKKE, klubb,
                viktighet="Høy",
                ekstra={"tap_rekke": TAP_STREAK_LENGDE},
            )

        # --- Vinnende rekke ---
        if (len(resultater) >= SEIER_STREAK_LENGDE and
                all(r == "S" for r in resultater[-SEIER_STREAK_LENGDE:])):
            self._publiser_lag_hendelse(
                HendelseType.VINNENDE_REKKE, klubb,
                viktighet="Normal",
                ekstra={"seier_rekke": SEIER_STREAK_LENGDE},
            )

        # --- Krise ---
        siste_8 = resultater[-KRISE_LENGDE:]
        if (len(resultater) >= KRISE_LENGDE and
                not any(r == "S" for r in siste_8)):
            self._publiser_lag_hendelse(
                HendelseType.KRISE, klubb,
                viktighet="Krise",
            )

        # --- Nedrykksfare (etter runde 20) ---
        if runde_nr >= NEDRYKK_RUNDE_GRENSE:
            nedrykk_grense = antall_lag - 2   # To siste plasser = nedrykk
            if tabellplass > nedrykk_grense:
                runder_igjen = 30 - runde_nr
                self._publiser_lag_hendelse(
                    HendelseType.NEDRYKKSFARE, klubb,
                    viktighet="Krise",
                    ekstra={"runder_igjen": runder_igjen},
                )

        # --- Opprykkssjanse ---
        if runde_nr >= NEDRYKK_RUNDE_GRENSE and tabellplass <= 2:
            self._publiser_lag_hendelse(
                HendelseType.OPPRYKKSSJANSE, klubb,
                viktighet="Høy",
            )

    def sjekk_tett_kampprogram(
        self,
        klubb,
        kommende_kampdatoer: list[datetime.date],
    ):
        """Kalles av kalender.py. Varsler hvis 3+ kamper på 8 dager."""
        if len(kommende_kampdatoer) < TETT_PROGRAM_KAMPER:
            return
        for i in range(len(kommende_kampdatoer) - TETT_PROGRAM_KAMPER + 1):
            vindu = kommende_kampdatoer[i:i + TETT_PROGRAM_KAMPER]
            spenn = (vindu[-1] - vindu[0]).days
            if spenn <= TETT_PROGRAM_DAGER:
                self._publiser_lag_hendelse(
                    HendelseType.TETT_KAMPPROGRAM, klubb,
                    viktighet="Normal",
                )
                break

    # =========================================================================
    # PUBLISERING — skjulte konsekvenser + synlige nyheter
    # =========================================================================
    def _publiser_spiller_hendelse(
        self,
        type: HendelseType,
        spiller,
        viktighet: str = "Normal",
        ekstra: Optional[dict] = None,
    ):
        """Håndterer konsekvenser og lager nyhet for spillerhendelser."""
        ekstra = ekstra or {}
        rolle  = spiller.hent_naavaerende_rolle() if hasattr(spiller, 'hent_naavaerende_rolle') else None
        klubb_navn = getattr(getattr(rolle, 'klubb', None), 'navn', "Ukjent klubb")
        ferdighet  = getattr(spiller, 'ferdighet', 0)

        # --- SKJULTE KONSEKVENSER ---
        if type == HendelseType.LAV_FORM_STREAK:
            viktighet = "Høy"
            if hasattr(spiller, '_presstoleranse'):
                spiller._presstoleranse = max(1, spiller._presstoleranse - 1)
            if hasattr(spiller, '_lojalitet'):
                spiller._lojalitet = max(1, spiller._lojalitet - 1)

        elif type == HendelseType.HØY_FORM_STREAK:
            if hasattr(spiller, '_presstoleranse'):
                spiller._presstoleranse = min(20, spiller._presstoleranse + 1)

        elif type == HendelseType.BENKEVARMER:
            viktighet = "Normal"
            if hasattr(spiller, '_lojalitet'):
                spiller._lojalitet = max(1, spiller._lojalitet - 2)
            if hasattr(spiller, '_egoisme'):
                spiller._egoisme = min(20, spiller._egoisme + 1)
            # Trigger opplev_hendelse for ekstra attributtdrift
            if hasattr(spiller, 'opplev_hendelse'):
                spiller.opplev_hendelse("sitter_på_benken_over_tid")

        elif type == HendelseType.LANGTIDSSKADET:
            viktighet = "Høy"
            if hasattr(spiller, '_presstoleranse'):
                spiller._presstoleranse = max(1, spiller._presstoleranse - 1)

        elif type == HendelseType.FRISKMELDT:
            viktighet = "Normal"

        # --- SYNLIG NYHET ---
        bruk_gemini = (
            type in GEMINI_HENDELSER and
            ferdighet >= GEMINI_FERDIGHET_GRENSE
        )
        kontekst = {
            "spiller":      spiller.etternavn if hasattr(spiller, 'etternavn') else str(spiller),
            "klubb":        klubb_navn,
            "klubb_tag":    klubb_navn.replace(" ", "").replace("/", ""),
            "skade_type":   getattr(spiller, 'skade_type', 'skade'),
            "dager":        getattr(spiller, 'skade_dager_igjen', 0),
            **ekstra,
        }

        if bruk_gemini:
            nyhet_data = generer_stordrama(
                hendelse_type=type.name,
                klubb_navn=klubb_navn,
                spiller_navn=getattr(spiller, 'etternavn', None),
                kontekst=kontekst,
            )
        else:
            from nyhetsgenerator import _hent_fallback
            nyhet_data = _hent_fallback(type.name, kontekst)

        hendelse = Hendelse(
            type=type,
            dato=self._dagens_dato or datetime.date.today(),
            objekt=spiller,
            nyhet=nyhet_data,
            viktighet=viktighet,
        )
        self.nyhets_ko.append(hendelse)
        self.historikk.append(hendelse)

    def _publiser_lag_hendelse(
        self,
        type: HendelseType,
        klubb,
        viktighet: str = "Normal",
        ekstra: Optional[dict] = None,
    ):
        """Håndterer konsekvenser og lager nyhet for lagshendelser."""
        ekstra = ekstra or {}
        klubb_navn = getattr(klubb, 'navn', str(klubb))

        # --- SKJULTE KONSEKVENSER ---
        if type == HendelseType.TAPENDE_REKKE:
            if hasattr(klubb, 'opplev_hendelse'):
                klubb.opplev_hendelse("manager_sparket")   # Uro øker
            if hasattr(klubb, '_intern_uro'):
                klubb._intern_uro = min(20, klubb._intern_uro + 1)

        elif type == HendelseType.KRISE:
            if hasattr(klubb, '_intern_uro'):
                klubb._intern_uro = min(20, klubb._intern_uro + 3)
            if hasattr(klubb, 'supporterbase'):
                klubb.supporterbase = max(1, klubb.supporterbase - 1)

        elif type == HendelseType.VINNENDE_REKKE:
            if hasattr(klubb, 'supporterbase'):
                klubb.supporterbase = min(20, klubb.supporterbase + 1)

        elif type == HendelseType.NEDRYKKSFARE:
            if hasattr(klubb, '_intern_uro'):
                klubb._intern_uro = min(20, klubb._intern_uro + 2)

        # --- SYNLIG NYHET ---
        bruk_gemini = type in GEMINI_HENDELSER
        kontekst = {
            "klubb":         klubb_navn,
            "klubb_tag":     klubb_navn.replace(" ", "").replace("/", ""),
            "turnering_tag": "Europa",
            **ekstra,
        }

        if bruk_gemini:
            nyhet_data = generer_stordrama(
                hendelse_type=type.name,
                klubb_navn=klubb_navn,
                kontekst=kontekst,
            )
        else:
            from nyhetsgenerator import _hent_fallback
            nyhet_data = _hent_fallback(type.name, kontekst)

        hendelse = Hendelse(
            type=type,
            dato=self._dagens_dato or datetime.date.today(),
            objekt=klubb,
            nyhet=nyhet_data,
            viktighet=viktighet,
        )
        self.nyhets_ko.append(hendelse)
        self.historikk.append(hendelse)

    # =========================================================================
    # INNBOKS — spillerens grensesnitt mot hendelsessystemet
    # =========================================================================
    def hent_uleste_nyheter(self) -> list[Hendelse]:
        """Returnerer alle uleste nyheter og markerer dem som lest."""
        uleste = [h for h in self.nyhets_ko if not h.lest]
        for h in uleste:
            h.lest = True
        return uleste

    def hent_krise_varsler(self) -> list[Hendelse]:
        """Returnerer alle ubehandlede krise-hendelser."""
        return [h for h in self.nyhets_ko if h.viktighet == "Krise" and not h.lest]

    def print_innboks(self, maks: int = 5):
        """Printer de siste nyhetene CM95-stil."""
        uleste = self.hent_uleste_nyheter()
        if not uleste:
            print("\n  📭 Ingen nye nyheter.")
            return

        print(f"\n  {'='*50}")
        print(f"  📬 INNBOKS — {len(uleste)} nye meldinger")
        print(f"  {'='*50}")
        for h in uleste[:maks]:
            nyhet = h.nyhet or {}
            viktig_ikon = {"Krise": "🚨", "Høy": "📰", "Normal": "📋", "Lav": "📎"}.get(
                h.viktighet, "📋"
            )
            dato_str = h.dato.strftime("%d.%m") if h.dato else ""
            print(f"\n  {viktig_ikon} [{dato_str}] {nyhet.get('overskrift', h.type.name)}")
            if nyhet.get('ingress'):
                print(f"     {nyhet['ingress']}")
            if nyhet.get('tweet'):
                print(f"     🐦 {nyhet['tweet']}")
        if len(uleste) > maks:
            print(f"\n  ... og {len(uleste) - maks} flere meldinger.")
        print(f"  {'='*50}\n")

    def tøm_gamle_nyheter(self, dager: int = 30):
        """Fjerner nyheter eldre enn N dager fra køen."""
        if not self._dagens_dato:
            return
        grense = self._dagens_dato - datetime.timedelta(days=dager)
        self.nyhets_ko = [
            h for h in self.nyhets_ko
            if h.dato and h.dato >= grense
        ]

    def __repr__(self):
        uleste = sum(1 for h in self.nyhets_ko if not h.lest)
        return (
            f"<HendelsesManager: {len(self.historikk)} hendelser, "
            f"{uleste} uleste>"
        )
