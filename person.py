import random

# =============================================================================
# SPILLKONSTANTER
# =============================================================================
SKALA_MIN = 1
SKALA_MAX = 20
MIDTPUNKT = 10.5
PRESS_BOOST_SJANSE = 0.20
UTAALMODIGHET_GRENSE = 12

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
