from person import (
    Person, SpillerRolle, TrenerRolle, ManagerRolle,
    SKALA_MIN, SKALA_MAX
)

# =============================================================================
# STADION
# =============================================================================
class Stadion:
    """
    Representerer klubbens hjemmebane.
    Standard påvirker hjemmebanefordel og inntekter fra kampdagen.
    """

    STANDARD_NIVAA = {
        1:  "Forfallent",
        2:  "Enkelt",
        3:  "Greit",
        4:  "Moderne",
        5:  "Imponerende",
    }

    def __init__(self, navn, kapasitet, standard, byggeaar):
        self.navn = navn
        self.kapasitet = kapasitet       # Antall tilskuere
        self.standard = standard         # 1–5, påvirker hjemmebanefordel
        self.byggeaar = byggeaar

        # Vedlikeholdskostnad øker med kapasitet og synker med nytt bygg
        self.ukentlig_vedlikehold = self._beregn_vedlikehold()

    def _beregn_vedlikehold(self):
        """Enkel formel: større og eldre stadion koster mer."""
        alder_faktor = max(1, (2025 - self.byggeaar) // 10)
        return int((self.kapasitet / 1000) * alder_faktor * 500)

    @property
    def standard_tekst(self):
        return self.STANDARD_NIVAA.get(self.standard, "Ukjent")

    @property
    def hjemmebane_fordel(self):
        """
        Returnerer en fordelsverdi (1–10) brukt av kampsimulatoren.
        Lav standard demper fordelen selv ved fullsatt stadion.
        """
        return round((self.standard / 5) * 10)

    def oppgrader(self):
        """Forbedrer standarden ett nivå hvis mulig."""
        if self.standard < 5:
            self.standard += 1
            self.ukentlig_vedlikehold = self._beregn_vedlikehold()
            print(f"[{self.navn}] Oppgradert til: {self.standard_tekst}")
        else:
            print(f"[{self.navn}] Er allerede på høyeste standard.")

    def __repr__(self):
        return (
            f"<Stadion: {self.navn}, "
            f"kap. {self.kapasitet:,}, "
            f"standard: {self.standard_tekst}>"
        )


# =============================================================================
# KLUBB
# =============================================================================
class Klubb:
    """
    Representerer en fotballklubb med identitet, økonomi, personell og kultur.

    Skjulte attributter (prefiks _) er ikke synlige for manageren direkte,
    men lekker ut gjennom hendelser, pressekonferanser og økonomirapporter.
    """

    def __init__(
        self,
        id,
        navn,
        kortnavn,
        grunnlagt_aar,
        farger,
        stadion,
        divisjon,
        budsjett,
        ukentlig_loennsbudsjett,
        gjeld,
        supporterbase,
        ambisjonsnivaa,
        historisk_suksess,
        intern_uro,
        okonomi_problem,
    ):
        # --- IDENTITET ---
        self.id = id
        self.navn = navn
        self.kortnavn = kortnavn          # F.eks. "RBK" — nyttig i tekstmenyer
        self.grunnlagt_aar = grunnlagt_aar
        self.farger = farger              # F.eks. ["Hvit", "Svart"]
        self.stadion = stadion            # Stadion-objekt
        self.divisjon = divisjon
        self.rivaler = []                 # Liste av klubb-id'er

        # --- ØKONOMI ---
        self.budsjett = budsjett
        self.ukentlig_loennsbudsjett = ukentlig_loennsbudsjett
        self.gjeld = gjeld
        self.hovedsponsor = None          # Kan bli et eget Sponsor-objekt senere

        # --- KULTUR / IDENTITET (Skala 1–20) ---
        self.supporterbase = supporterbase         # Påvirker hjemmekampfordel
        self.ambisjonsnivaa = ambisjonsnivaa       # Styrets forventninger
        self.historisk_suksess = historisk_suksess # Påvirker rykte og spillertiltrekning

        # --- SKJULTE ATTRIBUTTER (1–20) ---
        self._intern_uro = intern_uro              # Konflikter i styret
        self._okonomi_problem = okonomi_problem    # Skjult gjeld / mislighold

        # --- PERSONELL ---
        self._alt_personell = []   # Én enkelt kilde til sannhet om hvem som er i klubben

    # =========================================================================
    # PERSONELL — properties filtrerer _alt_personell i sanntid
    # =========================================================================
    @property
    def spillerstall(self):
        return [
            p for p in self._alt_personell
            if isinstance(p.hent_naavaerende_rolle(), SpillerRolle)
        ]

    @property
    def trenerstab(self):
        return [
            p for p in self._alt_personell
            if isinstance(p.hent_naavaerende_rolle(), TrenerRolle)
        ]

    @property
    def naavaerende_manager(self):
        for p in self._alt_personell:
            if isinstance(p.hent_naavaerende_rolle(), ManagerRolle):
                return p
        return None

    def legg_til_person(self, person: Person):
        """Legger en person til klubbens personelliste."""
        if person not in self._alt_personell:
            self._alt_personell.append(person)

    def fjern_person(self, person: Person):
        """Fjerner en person fra klubbens personelliste."""
        self._alt_personell = [p for p in self._alt_personell if p.id != person.id]

    def legg_til_rival(self, klubb_id: int):
        """Registrerer en rivalklubb."""
        if klubb_id not in self.rivaler:
            self.rivaler.append(klubb_id)

    # =========================================================================
    # ØKONOMI
    # =========================================================================
    def oppdater_okonomi(self):
        """
        Kalles ukentlig av spillmotoren.
        Skjulte økonomiske problemer spiser av budsjettet uten tydelig varsel.
        """
        # Skjult svinn ved alvorlige økonomiske problemer
        if self._okonomi_problem > 15:
            skjult_trekk = self.budsjett * 0.05   # 5% forsvinner stille
            self.budsjett -= skjult_trekk
            self.gjeld += skjult_trekk

        # Standard lønns- og vedlikeholdsutbetaling
        self.budsjett -= self.ukentlig_loennsbudsjett
        self.budsjett -= self.stadion.ukentlig_vedlikehold

    @property
    def er_i_ekonomisk_krise(self):
        """Synlig signal til manageren — men ikke årsaken."""
        return self.budsjett < 0 or self.gjeld > self.budsjett * 2

    # =========================================================================
    # HENDELSER — attributtdrift basert på sportslige resultater
    # =========================================================================
    def opplev_hendelse(self, hendelse_type):
        """
        Kalles av spillmotoren når noe viktig skjer med klubben.
        Påvirker kultur og skjult intern dynamikk over tid.
        """
        if hendelse_type == "nedrykk":
            self.supporterbase = max(SKALA_MIN, self.supporterbase - 3)
            self._intern_uro = min(SKALA_MAX, self._intern_uro + 2)
            print(f"[{self.navn}] Rykker ned. Supporterbasen rystes.")

        elif hendelse_type == "opprykk":
            self.supporterbase = min(SKALA_MAX, self.supporterbase + 2)
            self._intern_uro = max(SKALA_MIN, self._intern_uro - 1)
            print(f"[{self.navn}] Opprykk! Euforisk stemning.")

        elif hendelse_type == "seriemester":
            self.supporterbase = min(SKALA_MAX, self.supporterbase + 2)
            self.historisk_suksess = min(SKALA_MAX, self.historisk_suksess + 1)
            print(f"[{self.navn}] Seriemester! Legendarisk sesong.")

        elif hendelse_type == "manager_sparket":
            self._intern_uro = min(SKALA_MAX, self._intern_uro + 3)
            print(f"[{self.navn}] Manager sparket. Uro i garderoben.")

        # Klampe alle 1–20-verdier
        self.supporterbase = max(SKALA_MIN, min(SKALA_MAX, self.supporterbase))
        self.historisk_suksess = max(SKALA_MIN, min(SKALA_MAX, self.historisk_suksess))
        self._intern_uro = max(SKALA_MIN, min(SKALA_MAX, self._intern_uro))

    # =========================================================================
    # REPRESENTASJON
    # =========================================================================
    def __repr__(self):
        manager = self.naavaerende_manager
        manager_tekst = (
            f"{manager.fornavn} {manager.etternavn}" if manager else "Ledig"
        )
        return (
            f"<Klubb: {self.navn} ({self.kortnavn}), "
            f"{self.divisjon} — "
            f"Manager: {manager_tekst} — "
            f"Budsjett: {self.budsjett:,.0f} kr>"
        )
