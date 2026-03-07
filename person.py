import random

# =============================================================================
# SPILLKONSTANTER
# =============================================================================
SKALA_MIN = 1
SKALA_MAX = 20
MIDTPUNKT = 10.5
PRESS_BOOST_SJANSE = 0.20
UTAALMODIGHET_GRENSE = 12

# Fysikk-konstanter
KONDISJON_START         = 100.0
KONDISJON_KAMP_GRENSE   = 85.0   # Under dette bør AI ikke starte spilleren
KONDISJON_KRITISK       = 60.0   # Under dette: dobbel skaderisiko i kamp
RESTITUSJON_MIN         = 5.0    # % per dag ved utholdenhet 1
RESTITUSJON_MAX         = 15.0   # % per dag ved utholdenhet 20
KONDISJON_KOST_MIN      = 15.0   # % ved 90 min og utholdenhet 20
KONDISJON_KOST_MAKS     = 35.0   # % ved 90 min og utholdenhet 1

# Skadetyper med varighet i dager
SKADETYPER = [
    ("Strekk",          (7,  14), 0.45),   # (navn, (min_dager, maks_dager), sannsynlighet)
    ("Muskelskade",     (14, 28), 0.25),
    ("Forstuing",       (5,  10), 0.15),
    ("Brudd",           (28, 60), 0.05),
    ("Hjernerystelse",  (7,  21), 0.05),
    ("Sårskade",        (3,   7), 0.05),
]

# Rykte-ord: (negativt_ord, positivt_ord) for hver skjult attributt
RYKTE_ORD = {
    "_lojalitet":      ("Illojal",        "Lojal"),
    "_egoisme":        ("Selvoppofrende", "Selvgod"),
    "_presstoleranse": ("Nervøs",         "Jernvilje"),
    "_arbeidsvilje":   ("Lat",            "Arbeidssom"),
}


# =============================================================================
# ROLLE-KLASSENE
# =============================================================================
class Rolle:
    """Baseklasse for alle roller en person kan ha i karrieren sin."""

    def __init__(self, start_aar, klubb=None):
        self.start_aar = start_aar
        self.slutt_aar = None
        self.klubb = klubb
        self.er_aktiv = True

    def avslutt_rolle(self, slutt_aar):
        self.slutt_aar = slutt_aar
        self.er_aktiv = False

    def __repr__(self):
        status = "aktiv" if self.er_aktiv else f"avsluttet {self.slutt_aar}"
        return f"<{self.__class__.__name__}: {self.klubb} ({self.start_aar}–{status})>"


class SpillerRolle(Rolle):
    """En persons karriere som aktiv fotballspiller."""

    def __init__(self, start_aar, klubb, posisjon, ferdighet):
        super().__init__(start_aar, klubb)
        self.tittel = "Spiller"
        self.posisjon = posisjon       # f.eks. "Keeper", "Midtstopper", "Kantspiller"
        self.ferdighet = ferdighet     # 1-20, spillerens tekniske nivå


class TrenerRolle(Rolle):
    """Mellomsteget mellom spiller og manager."""

    def __init__(self, start_aar, klubb, spesialitet, person):
        super().__init__(start_aar, klubb)
        self.tittel = "Trener"
        self.spesialitet = spesialitet  # f.eks. "keepertrener", "fysisk", "taktikk"

        har_spilt = any(isinstance(r, SpillerRolle) for r in person.karriere_historikk)
        self.autoritet = 14 if har_spilt else 9


class ManagerRolle(Rolle):
    """Leder for et fotballag. Respekt i garderoben avhenger av karrierehistorikk."""

    def __init__(self, start_aar, klubb, foretrukket_taktikk, person):
        super().__init__(start_aar, klubb)
        self.tittel = "Manager"
        self.foretrukket_taktikk = foretrukket_taktikk  # f.eks. "4-3-3", "5-3-2"

        har_spilt = any(isinstance(r, SpillerRolle) for r in person.karriere_historikk)
        spilt_for_samme_klubb = any(
            isinstance(r, SpillerRolle) and r.klubb == klubb
            for r in person.karriere_historikk
        )

        if spilt_for_samme_klubb:
            self.respekt_i_garderoben = 18   # Klubblegende kommer hjem
        elif har_spilt:
            self.respekt_i_garderoben = 14   # Tidligere proffspiller
        else:
            self.respekt_i_garderoben = 8    # Teoretiker / journalist


# =============================================================================
# PERSON — GRUNNKLASSEN
# =============================================================================
class Person:
    """
    Grunnklasse for alle mennesker i spillet: spillere, trenere, managere,
    dommere, journalister, styremedlemmer, eiere, supporterledere m.fl.

    Skjulte attributter (prefiks _) er ikke synlige for spilleren direkte,
    men lekker ut gjennom hendelser og rykte.
    """

    def __init__(
        self,
        id,
        fornavn,
        etternavn,
        alder,
        lojalitet,
        egoisme,
        presstoleranse,
        arbeidsvilje,
    ):
        # --- Synlige basisattributter ---
        self.id = id
        self.fornavn = fornavn
        self.etternavn = etternavn
        self.alder = alder

        # --- Skjulte personlighetstrekk (1–20) ---
        self._lojalitet = lojalitet
        self._egoisme = egoisme
        self._presstoleranse = presstoleranse
        self._arbeidsvilje = arbeidsvilje

        # --- Karrieretidslinje ---
        self.karriere_historikk = []

    # -------------------------------------------------------------------------
    # KARRIERE
    # -------------------------------------------------------------------------
    def legg_til_rolle(self, ny_rolle):
        """Legger til en ny rolle i karrierehistorikken."""
        self.karriere_historikk.append(ny_rolle)

    def hent_naavaerende_rolle(self):
        """Returnerer den aktive rollen, eller None hvis personen er uten rolle."""
        if self.karriere_historikk and self.karriere_historikk[-1].er_aktiv:
            return self.karriere_historikk[-1]
        return None

    # -------------------------------------------------------------------------
    # RYKTE — beregnes automatisk fra skjulte attributter
    # -------------------------------------------------------------------------
    @property
    def rykte(self):
        """
        Det offentlig synlige ryktet til personen.
        Beregnes fra den attributten som avviker mest fra midtpunktet (10.5).
        Ved lik avstand vises alle toppkandidater (f.eks. "Lojal og Arbeidssom").
        En ny attributt må slå den forrige med minst 1 poeng for å overta alene.
        """
        attributter = {navn: getattr(self, navn) for navn in RYKTE_ORD}
        avstand = {navn: abs(verdi - MIDTPUNKT) for navn, verdi in attributter.items()}
        maks_avstand = max(avstand.values())

        vinnere = [
            navn for navn, avst in avstand.items()
            if maks_avstand - avst < 1
        ]

        rykte_ord = []
        for navn in vinnere:
            verdi = attributter[navn]
            negativ, positiv = RYKTE_ORD[navn]
            rykte_ord.append(positiv if verdi > MIDTPUNKT else negativ)

        return " og ".join(rykte_ord)

    # -------------------------------------------------------------------------
    # INTERN HJELPER — sikker oppdatering av attributter
    # -------------------------------------------------------------------------
    def _sett_attributt(self, navn, verdi):
        """Setter en skjult attributt og klamper verdien til lovlig skala."""
        setattr(self, navn, max(SKALA_MIN, min(SKALA_MAX, verdi)))

    def _klampe_alle(self):
        """Sikrer at alle skjulte attributter er innenfor 1–20 etter en hendelse."""
        for navn in RYKTE_ORD:
            self._sett_attributt(navn, getattr(self, navn))

    # -------------------------------------------------------------------------
    # FYSIKK — kondisjon og skader
    # -------------------------------------------------------------------------
    def hvil_en_dag(self):
        """Kalles av kalender.py hver dag. Bygger opp kondisjon gradvis."""
        if self.skadet:
            self.skade_dager_igjen -= 1
            if self.skade_dager_igjen <= 0:
                self.skadet = False
                self.skade_type = None
                self.skade_dager_igjen = 0
                # Friskmeldt spiller starter på 60% kondisjon
                self.kondisjon = max(self.kondisjon, 60.0)
            return   # Skadet spiller restituerer ikke kondisjon normalt

        if self.kondisjon < KONDISJON_START:
            # Restitusjon: 5% ved utholdenhet 1, 15% ved utholdenhet 20
            restitusjon = RESTITUSJON_MIN + (
                (self.utholdenhet - 1) / (SKALA_MAX - 1)
                * (RESTITUSJON_MAX - RESTITUSJON_MIN)
            )
            self.kondisjon = min(KONDISJON_START, self.kondisjon + restitusjon)

    def spill_kamp_minutter(self, minutter: float):
        """
        Kalles av kampmotor etter kampslutt.
        Trekker fra persistent kondisjon basert på minutter spilt og utholdenhet.
        En spiller med utholdenhet 20 mister 15% på 90 min.
        En spiller med utholdenhet 1 mister 35% på 90 min.
        """
        andel = minutter / 90.0
        kost = andel * (
            KONDISJON_KOST_MAKS - (
                (self.utholdenhet - 1) / (SKALA_MAX - 1)
                * (KONDISJON_KOST_MAKS - KONDISJON_KOST_MIN)
            )
        )
        self.kondisjon = max(0.0, self.kondisjon - kost)

    def tilbakestill_in_game_kondisjon(self):
        """Kalles av kampmotor ved kampstart. Setter in-game til persistent kondisjon."""
        self.in_game_kondisjon = self.kondisjon

    def oppdater_in_game_kondisjon(self, tretthet_drop: float):
        """
        Kalles av kampmotor hvert intervall og ved halvtid.
        In-game kondisjon faller raskere for spillere med lav utholdenhet.
        """
        justert_drop = tretthet_drop * (1.0 - (self.utholdenhet / (SKALA_MAX * 2)))
        self.in_game_kondisjon = max(0.0, self.in_game_kondisjon - justert_drop)

    @property
    def effektiv_ferdighet(self) -> float:
        """
        Returnerer ferdighetsjustert for in-game kondisjon.
        En spiller med ferdighet 20 og 50% kondisjon presterer som ferdighet 10.
        Skadet spiller kan ikke spille.
        """
        if self.skadet:
            return 0.0
        ferdighet = getattr(self, 'ferdighet', 10)
        return ferdighet * (self.in_game_kondisjon / 100.0)

    @property
    def er_spilleklar(self) -> bool:
        """Returnerer True hvis spilleren er frisk og over kondisjongrensen."""
        return not self.skadet and self.kondisjon >= KONDISJON_KAMP_GRENSE

    @property
    def skaderisiko_multiplikator(self) -> float:
        """
        Returnerer en multiplikator for skaderisiko basert på in-game kondisjon.
        Under 60%: dobbel risiko. Under 40%: tredobbel.
        """
        if self.in_game_kondisjon < 40.0:
            return 3.0
        elif self.in_game_kondisjon < KONDISJON_KRITISK:
            return 2.0
        return 1.0

    def paadrа_skade(self, skade_type: str = None, dager: int = None):
        """
        Setter spilleren som skadet.
        Kalles av kampmotor ved skadehendelse.
        """
        import random as _random
        if skade_type is None:
            # Trekk skadetype vektet etter sannsynlighet
            typer   = [s[0] for s in SKADETYPER]
            vekter  = [s[2] for s in SKADETYPER]
            skade_type = _random.choices(typer, weights=vekter, k=1)[0]

        if dager is None:
            varighet = next(s[1] for s in SKADETYPER if s[0] == skade_type)
            dager = _random.randint(*varighet)

        self.skadet            = True
        self.skade_type        = skade_type
        self.skade_dager_igjen = dager
        self.kondisjon         = max(0.0, self.kondisjon - 20.0)

    # -------------------------------------------------------------------------
    # ATTRIBUTTDRIFT — hendelser påvirker personligheten over tid
    # -------------------------------------------------------------------------
    def opplev_hendelse(self, hendelse_type):
        """
        Kalles av spillmotoren når noe viktig skjer med personen.
        Skjulte attributter drifter gradvis basert på hendelsestypen.
        """
        if hendelse_type == "sitter_på_benken_over_tid":
            if self._arbeidsvilje > UTAALMODIGHET_GRENSE:
                self._lojalitet -= 1
                self._egoisme += 1
                print(
                    f"[{self.fornavn} {self.etternavn}] "
                    f"Lojaliteten synker. Begynner å bli utålmodig."
                )

        elif hendelse_type == "vinner_viktig_kamp":
            if random.random() < PRESS_BOOST_SJANSE and self._presstoleranse < SKALA_MAX:
                self._presstoleranse += 1
                print(
                    f"[{self.fornavn} {self.etternavn}] "
                    f"Vokser på oppgaven. Presstoleranse øker."
                )

        self._klampe_alle()

    # -------------------------------------------------------------------------
    # REPRESENTASJON
    # -------------------------------------------------------------------------
    def __repr__(self):
        rolle = self.hent_naavaerende_rolle()
        rolle_tekst = rolle.tittel if rolle else "Uten rolle"
        return (
            f"<Person: {self.fornavn} {self.etternavn}, "
            f"{self.alder} år — {rolle_tekst} — Rykte: {self.rykte}>"
        )
