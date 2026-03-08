from person import (
    Person, SpillerRolle, TrenerRolle, ManagerRolle,
    SKALA_MIN, SKALA_MAX
)
from dataclasses import dataclass

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
       
        def betal_ukentlige_utgifter(self):
        """Kalles av kalenderen én gang i uka."""
        total_lonn = sum(getattr(s, 'kontrakt', Kontrakt(0, 0, 0)).ukelonn for s in self.spillerstall)
        
        # Trekk fra saldo. Går saldoen i minus, kan styret gi deg sparken over tid.
        self.saldo -= total_lonn
        
        # Oppdater det synlige lønnsbudsjettet
        self.ukentlig_loennsbudsjett = total_lonn
        
        def motta_aarlig_sponsor(self):
        """Kalles ved sesongstart."""
        # En klubb i Eliteserien med mye historisk suksess får mest.
        base = {"Eliteserien": 15_000_000, "OBOS-ligaen": 4_000_000, "PostNord-ligaen": 500_000}.get(self.divisjon, 100_000)
        suksess_multiplikator = 1.0 + (self.historisk_suksess / 20.0) # Inntil dobbel pris for topplag
        
        sponsor_sum = int(base * suksess_multiplikator)
        self.saldo += sponsor_sum
        return sponsor_sum

        def beregn_billettinntekter(self, motstander_rykte: int, billettpris: int = 150):
        """Kalles når laget spiller hjemmekamp."""
        if not self.stadion: return 0
        
        # Beregn tilskuere basert på supporterbase (1-20) pluss motstanderens trekkplaster
        base_tilskuere = (self.supporterbase / 20.0) * self.stadion.kapasitet
        motstander_trekk = (motstander_rykte / 20.0) * 2000
        
        # Legg til litt tilfeldighet for vær/form
        import random
        faktiske_tilskuere = int(base_tilskuere + motstander_trekk + random.randint(-500, 1500))
        
        # Klamper verdien mellom 0 og max kapasitet
        faktiske_tilskuere = max(0, min(self.stadion.kapasitet, faktiske_tilskuere))
        
        inntekt = faktiske_tilskuere * billettpris
        self.saldo += inntekt
        return faktiske_tilskuere, inntekt
        
        def sjekk_rik_onkel(self):
        """Sjekkes månedlig eller når saldo er farlig lav."""
        if getattr(self, 'har_rik_eier', False) and self.saldo < 0:
            import random
            if random.random() < 0.20: # 20% sjanse for at han blar opp når det kniper
                redningspakke = abs(self.saldo) + random.randint(2_000_000, 10_000_000)
                self.saldo += redningspakke
                # Returner tekst som HendelsesManager kan sende som nyhet!
                return f"RIK ONKEL REDDER KLUBBEN: {self.navn} mottar {redningspakke:,} kr fra investorer!"
        return None
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
            
@dataclass
class Kontrakt:
    ukelonn: int
    utlops_aar: int      # F.eks. 2027
    spiller_verdi: int   # Markedsverdien ved signering

    @property
    def aar_igjen(self, dags_dato_aar: int) -> int:
        return max(0, self.utlops_aar - dags_dato_aar)
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
