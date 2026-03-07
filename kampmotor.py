import random
from dataclasses import dataclass, field
from typing import Optional
from taktikk import (
    TAKTIKK_KATALOG, Oppstilling, Formasjon,
    hent_matchup_modifikator, hent_taktisk_respons,
)

# =============================================================================
# KONSTANTER
# =============================================================================
ANTALL_INTERVALLER   = 18          # 18 × 5 min = 90 min
HALVTID_INTERVALL    = 9           # Halvtid etter intervall 9
HJEMMEBANE_FORDEL    = 1.10        # 10% boost til hjemmelagets midtbane
TRETTHET_GRENSE      = 75          # Spillere under dette byttet ut av AI
RØDT_KORT_FORSVAR    = 0.80        # Forsvarsstyrke ved 10 mot 11
RØDT_KORT_MIDTBANE   = 0.85        # Midtbanestyrke ved 10 mot 11
P_GULT_KORT          = 0.04        # Per intervall per lag
P_RØDT_KORT          = 0.005       # Per intervall per lag
P_SKADE              = 0.008       # Per intervall per lag
P_STRAFFE            = 0.015       # Per intervall ved sjanse
# In-game kondisjon-drop per halvtid (5-minutters intervall)
INGAME_DROP_PER_INTERVALL = 2.5    # Grunnverdi, justeres av utholdenhet
HALVTID_RESTITUSJON_MIN = 10.0   # % ved utholdenhet 1
HALVTID_RESTITUSJON_MAX = 20.0   # % ved utholdenhet 20
SKADE_KONDISJON_TERSKEL   = 60.0   # Under dette: forhøyet skaderisiko

MAAL_TYPER = [
    ("Heading",     0.15),
    ("Langskudd",   0.12),
    ("Nærkamp",     0.25),
    ("Kontring",    0.18),
    ("Innlegg",     0.20),
    ("Straffespark",0.10),
]


# =============================================================================
# KAMPSTATISTIKK
# =============================================================================
@dataclass
class KampStatistikk:
    ballbesittelse_hjemme: float = 0.0
    skudd_hjemme: int = 0
    skudd_borte: int = 0
    skudd_paa_maal_hjemme: int = 0
    skudd_paa_maal_borte: int = 0
    gule_kort_hjemme: int = 0
    gule_kort_borte: int = 0
    røde_kort_hjemme: int = 0
    røde_kort_borte: int = 0
    skader_hjemme: int = 0
    skader_borte: int = 0

    @property
    def ballbesittelse_borte(self) -> float:
        return 100.0 - self.ballbesittelse_hjemme

    def print(self):
        print(f"  Ballbesittelse:  {self.ballbesittelse_hjemme:.0f}% – "
              f"{self.ballbesittelse_borte:.0f}%")
        print(f"  Skudd:           {self.skudd_hjemme} – {self.skudd_borte}")
        print(f"  Skudd på mål:    {self.skudd_paa_maal_hjemme} – "
              f"{self.skudd_paa_maal_borte}")
        if self.gule_kort_hjemme or self.gule_kort_borte:
            print(f"  Gule kort:       {self.gule_kort_hjemme} – "
                  f"{self.gule_kort_borte}")
        if self.røde_kort_hjemme or self.røde_kort_borte:
            print(f"  Røde kort:       {self.røde_kort_hjemme} – "
                  f"{self.røde_kort_borte}")


# =============================================================================
# KAMPSHENDELSE
# =============================================================================
@dataclass
class KampHendelse:
    minutt: int
    type: str       # "mål", "gult_kort", "rødt_kort", "skade", "bytte"
    lag: str        # "hjemme" eller "borte"
    spiller: object
    detalj: str = ""

    def __repr__(self):
        spiller_navn = getattr(self.spiller, 'etternavn',
                        getattr(self.spiller, 'navn', '?'))
        ikoner = {
            "mål":       "⚽",
            "gult_kort": "🟨",
            "rødt_kort": "🟥",
            "skade":     "🚑",
            "bytte":     "🔄",
        }
        ikon = ikoner.get(self.type, "•")
        detalj = f" ({self.detalj})" if self.detalj else ""
        return f"  {self.minutt:>3} min  {ikon}  {spiller_navn}{detalj}"


# =============================================================================
# KAMPRESULTAT
# =============================================================================
@dataclass
class KampResultat:
    hjemme_navn: str
    borte_navn: str
    hjemme_maal: int = 0
    borte_maal: int = 0
    hendelser: list[KampHendelse] = field(default_factory=list)
    statistikk: KampStatistikk = field(default_factory=KampStatistikk)
    ekstraomganger: bool = False
    straffer: bool = False

    @property
    def vinner_navn(self) -> Optional[str]:
        if self.hjemme_maal > self.borte_maal:
            return self.hjemme_navn
        elif self.borte_maal > self.hjemme_maal:
            return self.borte_navn
        return None

    def print_kamprapport(self):
        print(f"\n{'='*55}")
        print(f"  {self.hjemme_navn:<20}  {self.hjemme_maal} – "
              f"{self.borte_maal}  {self.borte_navn}")
        if self.ekstraomganger:
            ekstra = " (str.)" if self.straffer else " (e.o.)"
            print(f"  {ekstra}")
        print(f"{'='*55}")
        if self.hendelser:
            print()
            for h in sorted(self.hendelser, key=lambda x: x.minutt):
                print(h)
        print()
        self.statistikk.print()
        print(f"{'='*55}\n")


# =============================================================================
# LAG-TILSTAND
# Dynamisk tilstand for ett lag gjennom en kamp
# =============================================================================
class LagTilstand:
    """
    Holder ett lags tilstand gjennom kampen:
    aktive spillere, røde kort, skader, gjeldende taktikk.
    """

    def __init__(self, klubb, oppstilling: Oppstilling, er_hjemmelag: bool):
        self.klubb = klubb
        self.oppstilling = oppstilling
        self.er_hjemmelag = er_hjemmelag
        self.navn = getattr(klubb, 'navn', str(klubb))

        # Aktive spillere (kopierer plasseringer)
        self.aktive_spillere: list = list(oppstilling.plasseringer.values())
        self.utbyttede_spillere: list = []
        self.skadede_spillere: list = []
        self.utvist_spillere: list = []

        # Bytter
        self.bytter_brukt: int = 0
        self.maks_bytter: int = 5

        # Gjeldende taktikk
        self.taktikk: Formasjon = oppstilling.formasjon
        self.spillertall: int = 11

        # Trøtthet per spiller (0–100, høyere = mer sliten)
        self.trøtthet: dict = {
            id(s): random.randint(10, 25)
            for s in self.aktive_spillere
        }

    # -------------------------------------------------------------------------
    # SONESTYRKER — dynamisk, oppdateres ved kort/skade/bytte
    # -------------------------------------------------------------------------
    def hent_effektiv_lagdel(self, sone_kode: str) -> float:
        """
        Beregner effektiv styrke for en sone.
        sone_kode: 'F' (forsvar), 'M' (midtbane), 'A' (angrep)
        """
        sone_navn = {"F": "forsvar", "M": "midtbane", "A": "angrep"}[sone_kode]
        base = self.oppstilling.beregn_sone_styrke(sone_navn)

        # Juster for røde kort
        if self.spillertall == 10:
            if sone_kode == "F":
                base *= RØDT_KORT_FORSVAR
            elif sone_kode == "M":
                base *= RØDT_KORT_MIDTBANE
        elif self.spillertall < 10:
            reduksjon = 1.0 - (0.07 * (11 - self.spillertall))
            base *= max(0.5, reduksjon)

        # Hjemmebanefordel på midtbanen
        if self.er_hjemmelag and sone_kode == "M":
            stadion = getattr(getattr(self.klubb, 'stadion', None), 'hjemmebane_fordel', 5)
            base *= HJEMMEBANE_FORDEL * (stadion / 10)

        # Taktisk vekt
        if sone_kode == "A":
            base *= self.taktikk.vekt_angrep
        elif sone_kode == "F":
            base *= self.taktikk.vekt_forsvar
        elif sone_kode == "M":
            base *= self.taktikk.vekt_midtbane

        return max(1.0, base)

    @property
    def taktikk_vekt_angrep(self) -> float:
        return self.taktikk.vekt_angrep

    # -------------------------------------------------------------------------
    # SPILLERVALG
    # -------------------------------------------------------------------------
    def velg_avslutter(self):
        """Velger en angriper eller offensiv midtbanespiller som avslutter."""
        from taktikk import Posisjon, POSISJON_GRUPPE
        kandidater = [
            s for s in self.aktive_spillere
            if hasattr(s, 'primær_posisjon') and
            POSISJON_GRUPPE.get(s.primær_posisjon, 'M') == 'A'
        ]
        if not kandidater:
            kandidater = self.aktive_spillere
        # Vektet etter ferdighet
        vekter = [getattr(s, 'ferdighet', 10) for s in kandidater]
        return random.choices(kandidater, weights=vekter, k=1)[0]

    def velg_keeper(self):
        """Returnerer keeperen."""
        from taktikk import Posisjon
        for s in self.aktive_spillere:
            if getattr(s, 'primær_posisjon', None) == Posisjon.K:
                return s
        return self.aktive_spillere[0] if self.aktive_spillere else None

    def velg_kortkandidат(self) -> Optional[object]:
        """Velger en tilfeldig utespiller (ikke keeper) for kort/skade."""
        kandidater = [
            s for s in self.aktive_spillere
            if getattr(s, 'primær_posisjon', None) is not None
        ]
        return random.choice(kandidater) if kandidater else None

    def finn_innbytter(self) -> Optional[object]:
        """Finner en frisk innbytter fra benken."""
        benk = getattr(self.klubb, '_alt_personell', [])
        brukte_ids = {id(s) for s in self.aktive_spillere + self.utbyttede_spillere}
        for spiller in benk:
            if id(spiller) not in brukte_ids:
                return spiller
        return None

    # -------------------------------------------------------------------------
    # HENDELSESHÅNDTERING
    # -------------------------------------------------------------------------
    def gi_rødt_kort(self, spiller) -> bool:
        if spiller in self.aktive_spillere:
            self.aktive_spillere.remove(spiller)
            self.utvist_spillere.append(spiller)
            self.spillertall -= 1
            return True
        return False

    def registrer_skade(self, spiller) -> Optional[object]:
        """Bytter ut skadet spiller hvis bytter gjenstår."""
        if spiller not in self.aktive_spillere:
            return None
        self.skadede_spillere.append(spiller)
        if self.bytter_brukt < self.maks_bytter:
            innbytter = self.finn_innbytter()
            if innbytter:
                self.aktive_spillere.remove(spiller)
                self.aktive_spillere.append(innbytter)
                self.bytter_brukt += 1
                return innbytter
            else:
                self.aktive_spillere.remove(spiller)
                self.spillertall -= 1
        return None

    def gjør_taktisk_bytte(self, ny_taktikk_navn: str) -> bool:
        """Bytter formasjon midt i kampen."""
        if ny_taktikk_navn in TAKTIKK_KATALOG:
            self.taktikk = TAKTIKK_KATALOG[ny_taktikk_navn]
            return True
        return False

    def oppdater_trøtthet(self):
        """Øker trøtthet for alle aktive spillere per intervall."""
        for spiller in self.aktive_spillere:
            nøkkel = id(spiller)
            self.trøtthet[nøkkel] = min(
                100,
                self.trøtthet.get(nøkkel, 20) + random.randint(3, 6)
            )

    def __repr__(self):
        return (
            f"<LagTilstand: {self.navn}, "
            f"{self.spillertall} spillere, "
            f"{self.taktikk.navn}>"
        )


# =============================================================================
# KAMPMOTOR
# =============================================================================
class KampMotor:
    """
    Simulerer én fotballkamp i detalj (LOD 1).

    Kampflyten:
        1. Forberedelse — sonestyrker, situasjonsfaktorer
        2. 18 × 5-minutters intervaller
        3. Halvtidsjustering
        4. Produser KampResultat
        5. Evt. ekstraomganger (cup)
    """

    def __init__(self, tillat_ekstraomganger: bool = False):
        self.tillat_ekstraomganger = tillat_ekstraomganger
        self.resultat: Optional[KampResultat] = None
        self._hjemme: Optional[LagTilstand] = None
        self._borte: Optional[LagTilstand] = None

    # =========================================================================
    # OFFENTLIG API
    # =========================================================================
    def spill_kamp(
        self,
        hjemme_klubb,
        borte_klubb,
        hjemme_oppstilling: Oppstilling,
        borte_oppstilling: Oppstilling,
    ) -> KampResultat:
        """
        Spiller en komplett kamp og returnerer KampResultat.
        Primærmetoden som kalles av kalender.py / cup.py.
        """
        self._hjemme = LagTilstand(hjemme_klubb, hjemme_oppstilling, er_hjemmelag=True)
        self._borte  = LagTilstand(borte_klubb,  borte_oppstilling,  er_hjemmelag=False)

        # Tilbakestill in-game kondisjon for alle spillere til persistent kondisjon
        for lag in [self._hjemme, self._borte]:
            for spiller in lag.aktive_spillere:
                if hasattr(spiller, 'tilbakestill_in_game_kondisjon'):
                    spiller.tilbakestill_in_game_kondisjon()

        hjemme_navn = getattr(hjemme_klubb, 'navn', str(hjemme_klubb))
        borte_navn  = getattr(borte_klubb,  'navn', str(borte_klubb))

        self.resultat = KampResultat(
            hjemme_navn=hjemme_navn,
            borte_navn=borte_navn,
            statistikk=KampStatistikk(),
        )

        # Hent matchup-modifikatorer
        hjemme_mod, borte_mod = hent_matchup_modifikator(
            self._hjemme.taktikk.navn,
            self._borte.taktikk.navn,
        )
        self._hjemme_matchup = hjemme_mod
        self._borte_matchup  = borte_mod

        # Spill 90 minutter
        self._spill_omgang(start=0, slutt=HALVTID_INTERVALL)
        self._halvtid()
        self._spill_omgang(start=HALVTID_INTERVALL, slutt=ANTALL_INTERVALLER)

        # Oppdater persistent kondisjon
        self._sluttspill()

        # Ekstraomganger (cup) hvis uavgjort
        if (self.tillat_ekstraomganger
                and self.resultat.hjemme_maal == self.resultat.borte_maal):
            self._ekstraomganger()

        return self.resultat

    # =========================================================================
    # KAMPLOOP
    # =========================================================================
    def _spill_omgang(self, start: int, slutt: int):
        for intervall in range(start, slutt):
            self._spill_intervall(intervall)
            self._sjekk_hendelser(intervall)
            self._hjemme.oppdater_trøtthet()
            self._borte.oppdater_trøtthet()

    def _spill_intervall(self, intervall: int):
        """
        Kjernen i simuleringen.
        Avgjør kontroll → sjanse → skudd → mål for hvert 5-minutters intervall.
        In-game kondisjon faller gradvis — svake spillere kollapser i 2. omgang.
        """
        # Oppdater in-game kondisjon for alle aktive spillere
        for lag in [self._hjemme, self._borte]:
            for spiller in lag.aktive_spillere:
                if hasattr(spiller, 'oppdater_in_game_kondisjon'):
                    spiller.oppdater_in_game_kondisjon(INGAME_DROP_PER_INTERVALL)
        m_hjemme = (self._hjemme.hent_effektiv_lagdel('M')
                    * (1 + self._hjemme_matchup))
        m_borte  = (self._borte.hent_effektiv_lagdel('M')
                    * (1 + self._borte_matchup))

        # --- P(kontroll) ---
        p_kontroll = m_hjemme / (m_hjemme + m_borte)

        if random.random() < p_kontroll:
            angriper, forsvarer = self._hjemme, self._borte
            self.resultat.statistikk.ballbesittelse_hjemme += (100 / ANTALL_INTERVALLER)
        else:
            angriper, forsvarer = self._borte, self._hjemme

        # --- P(sjanse | kontroll) ---
        a_styrke = angriper.hent_effektiv_lagdel('A')
        p_sjanse = (a_styrke / 20.0) * angriper.taktikk_vekt_angrep * 0.35

        if random.random() < p_sjanse:
            self._forsøk_mål(intervall, angriper, forsvarer)

            # Straffespark-sjanse
            if random.random() < P_STRAFFE:
                self._forsøk_straffe(intervall, angriper, forsvarer)

    def _forsøk_mål(self, intervall: int, angriper: LagTilstand, forsvarer: LagTilstand):
        """Behandler én sjanse — fra skuddvurdering til evt. mål."""
        a_styrke = angriper.hent_effektiv_lagdel('A')
        f_styrke = forsvarer.hent_effektiv_lagdel('F')

        # Skudd-statistikk
        if angriper.er_hjemmelag:
            self.resultat.statistikk.skudd_hjemme += 1
        else:
            self.resultat.statistikk.skudd_borte += 1

        # --- P(skudd på mål | sjanse) ---
        p_skudd = a_styrke / (a_styrke + f_styrke)
        if random.random() > p_skudd:
            return

        # Skudd på mål
        if angriper.er_hjemmelag:
            self.resultat.statistikk.skudd_paa_maal_hjemme += 1
        else:
            self.resultat.statistikk.skudd_paa_maal_borte += 1

        spiss  = angriper.velg_avslutter()
        keeper = forsvarer.velg_keeper()

        if not spiss or not keeper:
            return

        spiss_ferdighet  = getattr(spiss,  'ferdighet', 10)
        keeper_ferdighet = getattr(keeper, 'ferdighet', 10)

        # --- P(mål | skudd på mål) ---
        p_maal = spiss_ferdighet / (spiss_ferdighet + keeper_ferdighet)

        if random.random() < p_maal:
            minutt = (intervall * 5) + random.randint(1, 5)
            maal_type = self._trekk_maal_type()
            self._registrer_maal(minutt, angriper, spiss, maal_type)

    def _forsøk_straffe(self, intervall: int, angriper: LagTilstand, forsvarer: LagTilstand):
        """Straffespark i ordinær tid."""
        spiss  = angriper.velg_avslutter()
        keeper = forsvarer.velg_keeper()
        if not spiss or not keeper:
            return

        spiss_ferdighet  = getattr(spiss,  'ferdighet', 10)
        keeper_ferdighet = getattr(keeper, 'ferdighet', 10)

        # Straffer konverteres oftere
        p_maal = (spiss_ferdighet / (spiss_ferdighet + keeper_ferdighet)) * 1.3
        p_maal = min(0.92, p_maal)

        minutt = (intervall * 5) + random.randint(1, 5)
        if random.random() < p_maal:
            self._registrer_maal(minutt, angriper, spiss, "Straffespark")
        else:
            hendelse = KampHendelse(
                minutt=minutt,
                type="straffebom",
                lag="hjemme" if angriper.er_hjemmelag else "borte",
                spiller=spiss,
                detalj="Straffespark reddet/utenfor",
            )
            self.resultat.hendelser.append(hendelse)

    def _registrer_maal(
        self,
        minutt: int,
        angriper: LagTilstand,
        spiller,
        maal_type: str,
    ):
        er_hjemme = angriper.er_hjemmelag
        if er_hjemme:
            self.resultat.hjemme_maal += 1
            lag_str = "hjemme"
        else:
            self.resultat.borte_maal += 1
            lag_str = "borte"

        hendelse = KampHendelse(
            minutt=minutt,
            type="mål",
            lag=lag_str,
            spiller=spiller,
            detalj=maal_type,
        )
        self.resultat.hendelser.append(hendelse)

        # Attributtdrift — scorer vokser på suksess
        if hasattr(spiller, 'opplev_hendelse'):
            spiller.opplev_hendelse("vinner_viktig_kamp")

    def _trekk_maal_type(self) -> str:
        typer  = [t[0] for t in MAAL_TYPER]
        vekter = [t[1] for t in MAAL_TYPER]
        return random.choices(typer, weights=vekter, k=1)[0]

    # =========================================================================
    # HENDELSER (KORT, SKADER, BYTTER)
    # =========================================================================
    def _sjekk_hendelser(self, intervall: int):
        """Sjekker for tilfeldige hendelser hvert intervall."""
        for lag in [self._hjemme, self._borte]:
            lag_str = "hjemme" if lag.er_hjemmelag else "borte"
            minutt  = (intervall * 5) + random.randint(1, 5)

            # Gult kort
            if random.random() < P_GULT_KORT:
                spiller = lag.velg_kortkandidаt()
                if spiller:
                    if lag.er_hjemmelag:
                        self.resultat.statistikk.gule_kort_hjemme += 1
                    else:
                        self.resultat.statistikk.gule_kort_borte += 1
                    self.resultat.hendelser.append(KampHendelse(
                        minutt=minutt, type="gult_kort",
                        lag=lag_str, spiller=spiller,
                    ))

            # Rødt kort
            if random.random() < P_RØDT_KORT:
                spiller = lag.velg_kortkandidаt()
                if spiller and lag.gi_rødt_kort(spiller):
                    if lag.er_hjemmelag:
                        self.resultat.statistikk.røde_kort_hjemme += 1
                    else:
                        self.resultat.statistikk.røde_kort_borte += 1
                    self.resultat.hendelser.append(KampHendelse(
                        minutt=minutt, type="rødt_kort",
                        lag=lag_str, spiller=spiller,
                    ))

            # Skade — forhøyet risiko ved lav in-game kondisjon
            skade_multiplikator = 1.0
            # Sjekk om noen aktive spillere er under kritisk kondisjon
            kritiske = [
                s for s in lag.aktive_spillere
                if getattr(s, 'in_game_kondisjon', 100.0) < SKADE_KONDISJON_TERSKEL
            ]
            if kritiske:
                skade_multiplikator = max(
                    getattr(s, 'skaderisiko_multiplikator', 1.0)
                    for s in kritiske
                )
            if random.random() < P_SKADE * skade_multiplikator:
                spiller = lag.velg_kortkandidаt()
                if spiller:
                    # Påfør skaden med type og varighet
                    if hasattr(spiller, 'paadra_skade'):
                        spiller.paadra_skade()
                    innbytter = lag.registrer_skade(spiller)
                    if lag.er_hjemmelag:
                        self.resultat.statistikk.skader_hjemme += 1
                    else:
                        self.resultat.statistikk.skader_borte += 1
                    skade_tekst = getattr(spiller, 'skade_type', 'Skade')
                    self.resultat.hendelser.append(KampHendelse(
                        minutt=minutt, type="skade",
                        lag=lag_str, spiller=spiller,
                        detalj=skade_tekst,
                    ))
                    if innbytter:
                        self.resultat.hendelser.append(KampHendelse(
                            minutt=minutt, type="bytte",
                            lag=lag_str, spiller=innbytter,
                            detalj=f"Inn for {getattr(spiller, 'etternavn', '?')}",
                        ))

    # =========================================================================
    # HALVTID
    # =========================================================================
    def _halvtid(self):
        """
        Halvtidspause.
        1. Ekstra in-game kondisjon-drop for akkumulert tretthet
        2. AI-manager vurderer taktikk og bytter
        3. Sonestyrker beregnes på nytt for 2. omgang
        """
        for spiller in lag.aktive_spillere:
            if hasattr(spiller, 'utholdenhet'):
                restitusjon = HALVTID_RESTITUSJON_MIN + (
                    (spiller.utholdenhet - 1) / 19
                    * (HALVTID_RESTITUSJON_MAX - HALVTID_RESTITUSJON_MIN)
                )
                spiller.in_game_kondisjon = min(
                    spiller.kondisjon,   # Kan ikke overstige persistent kondisjon
                    spiller.in_game_kondisjon + restitusjon
                )
                
        for lag in [self._hjemme, self._borte]:
            for spiller in lag.aktive_spillere:
                if hasattr(spiller, 'oppdater_in_game_kondisjon'):
                    # Ekstra halvtids-drop: mer for spillere med lav utholdenhet
                    spiller.oppdater_in_game_kondisjon(HALVTID_EKSTRA_DROP)

            ny_taktikk = hent_taktisk_respons(
                mentalitet=lag.taktikk.mentalitet,
                hjemme_maal=self.resultat.hjemme_maal,
                borte_maal=self.resultat.borte_maal,
                er_hjemmelag=lag.er_hjemmelag,
            )
            if ny_taktikk and ny_taktikk != lag.taktikk.navn:
                lag.gjør_taktisk_bytte(ny_taktikk)

            # Bytter: AI sjekker in_game_kondisjon, ikke bare trøtthet-dict
            self._gjør_kondisjon_bytte(lag)

    def _gjør_kondisjon_bytte(self, lag: LagTilstand):
        """
        AI bytter ut spillere med lav in-game kondisjon.
        Grense: under 60% kondisjon ved halvtid → byttes.
        Simulerer naturlig squad rotation og beskyttelse av spillere.
        """
        if lag.bytter_brukt >= lag.maks_bytter:
            return
        for spiller in list(lag.aktive_spillere):
            if lag.bytter_brukt >= lag.maks_bytter:
                break
            ingame = getattr(spiller, 'in_game_kondisjon', 100.0)
            if ingame < SKADE_KONDISJON_TERSKEL:
                innbytter = lag.finn_innbytter()
                if innbytter:
                    lag.aktive_spillere.remove(spiller)
                    lag.aktive_spillere.append(innbytter)
                    lag.utbyttede_spillere.append(spiller)
                    lag.bytter_brukt += 1
                    lag_str = "hjemme" if lag.er_hjemmelag else "borte"
                    self.resultat.hendelser.append(KampHendelse(
                        minutt=46,
                        type="bytte",
                        lag=lag_str,
                        spiller=innbytter,
                        detalj=f"Inn for {getattr(spiller, 'etternavn', '?')} (tretthet)",
                    ))

    # =========================================================================
    # SLUTTSPILL — oppdater persistent kondisjon etter kampen
    # =========================================================================
    def _sluttspill(self):
        """
        Kalles etter 90 minutter (eller ekstraomganger).
        Trekker fra persistent kondisjon basert på minutter spilt.
        """
        for lag in [self._hjemme, self._borte]:
            for spiller in lag.aktive_spillere:
                if hasattr(spiller, 'spill_kamp_minutter'):
                    spiller.spill_kamp_minutter(90)
            for spiller, minutter in self._hent_innbytter_minutter(lag):
                if hasattr(spiller, 'spill_kamp_minutter'):
                    spiller.spill_kamp_minutter(minutter)

    def _hent_innbytter_minutter(self, lag: LagTilstand) -> list[tuple]:
        """Returnerer (spiller, minutter) for innbyttere basert på byttetidspunkt."""
        # Forenklet: innbyttere antas å spille 45 minutter i snitt
        return [(s, 45) for s in lag.utbyttede_spillere
                if s not in lag.aktive_spillere]

    # =========================================================================
    # EKSTRAOMGANGER (CUP)
    # =========================================================================
    def _ekstraomganger(self):
        """Spiller 2 × 15 minutter (6 intervaller) ved uavgjort i cup."""
        self.resultat.ekstraomganger = True
        print("  ⏱  Ekstraomganger!")

        for intervall in range(3):
            self._spill_intervall(ANTALL_INTERVALLER + intervall)

        if self.resultat.hjemme_maal == self.resultat.borte_maal:
            for intervall in range(3):
                self._spill_intervall(ANTALL_INTERVALLER + 3 + intervall)

        # Fortsatt uavgjort → straffespark
        if self.resultat.hjemme_maal == self.resultat.borte_maal:
            self._straffespark_konkurranse()

    def _straffespark_konkurranse(self):
        """Enkel straffespark-simulering: 5 skudd per lag."""
        self.resultat.straffer = True
        print("  🥅  Straffesparkskonkurranse!")

        hjemme_score = 0
        borte_score  = 0

        for runde in range(5):
            spiss_h  = self._hjemme.velg_avslutter()
            keeper_b = self._borte.velg_keeper()
            ferd_h   = getattr(spiss_h,  'ferdighet', 10)
            ferd_kb  = getattr(keeper_b, 'ferdighet', 10)
            if random.random() < min(0.90, ferd_h / (ferd_h + ferd_kb) * 1.3):
                hjemme_score += 1

            spiss_b  = self._borte.velg_avslutter()
            keeper_h = self._hjemme.velg_keeper()
            ferd_b   = getattr(spiss_b,  'ferdighet', 10)
            ferd_kh  = getattr(keeper_h, 'ferdighet', 10)
            if random.random() < min(0.90, ferd_b / (ferd_b + ferd_kh) * 1.3):
                borte_score += 1

        # Legg til straffemål i resultatet
        self.resultat.hjemme_maal += hjemme_score
        self.resultat.borte_maal  += borte_score

        # Sudden death hvis fortsatt likt
        runder = 0
        while self.resultat.hjemme_maal == self.resultat.borte_maal and runder < 20:
            ferd_h  = getattr(self._hjemme.velg_avslutter(), 'ferdighet', 10)
            ferd_kh = getattr(self._hjemme.velg_keeper(),    'ferdighet', 10)
            ferd_b  = getattr(self._borte.velg_avslutter(),  'ferdighet', 10)
            ferd_kb = getattr(self._borte.velg_keeper(),     'ferdighet', 10)
            if random.random() < 0.75:
                self.resultat.hjemme_maal += 1
            if random.random() < 0.75:
                self.resultat.borte_maal += 1
            runder += 1

        # Sikre at én vinner
        if self.resultat.hjemme_maal == self.resultat.borte_maal:
            self.resultat.hjemme_maal += 1
