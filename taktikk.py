from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional

# =============================================================================
# POSISJONER
# =============================================================================
class Posisjon(Enum):
    """Alle spillerposisjoner i spillet."""
    # Keeper
    K    = "Keeper"
    # Forsvar
    HB   = "Høyre sideback"
    VB   = "Venstre sideback"
    HVB  = "Høyre vingback"
    VVB  = "Venstre vingback"
    MST  = "Midtstopper"
    # Midtbane
    DM   = "Defensiv midtbanespiller"
    SM   = "Sentral midtbanespiller"
    OM   = "Offensiv midtbanespiller"
    HV   = "Høyre ving"
    VV   = "Venstre ving"
    # Angrep
    SP   = "Spiss"
    HA   = "Høyre angrepsspiller"
    VA   = "Venstre angrepsspiller"

# Gruppering brukt av formasjonsvalidering
POSISJON_GRUPPE = {
    Posisjon.K:   "K",
    Posisjon.HB:  "F",
    Posisjon.VB:  "F",
    Posisjon.HVB: "F",   # Vingback teller som forsvar i formasjonskrav
    Posisjon.VVB: "F",
    Posisjon.MST: "F",
    Posisjon.DM:  "M",
    Posisjon.SM:  "M",
    Posisjon.OM:  "M",
    Posisjon.HV:  "M",
    Posisjon.VV:  "M",
    Posisjon.SP:  "A",
    Posisjon.HA:  "A",
    Posisjon.VA:  "A",
}

# Naturlige posisjonspar — hvilke posisjoner henger sammen?
# En spiller kan ha to posisjoner, men bare fra "kompatible" grupper
KOMPATIBLE_POSISJONER: dict[Posisjon, list[Posisjon]] = {
    Posisjon.K:   [],                                    # Keeper spiller bare keeper
    Posisjon.HB:  [Posisjon.HVB, Posisjon.MST],
    Posisjon.VB:  [Posisjon.VVB, Posisjon.MST],
    Posisjon.HVB: [Posisjon.HB,  Posisjon.HV],
    Posisjon.VVB: [Posisjon.VB,  Posisjon.VV],
    Posisjon.MST: [Posisjon.HB,  Posisjon.VB, Posisjon.DM],
    Posisjon.DM:  [Posisjon.MST, Posisjon.SM],
    Posisjon.SM:  [Posisjon.DM,  Posisjon.OM, Posisjon.HV, Posisjon.VV],
    Posisjon.OM:  [Posisjon.SM,  Posisjon.SP, Posisjon.HA, Posisjon.VA],
    Posisjon.HV:  [Posisjon.HVB, Posisjon.SM, Posisjon.HA],
    Posisjon.VV:  [Posisjon.VVB, Posisjon.SM, Posisjon.VA],
    Posisjon.SP:  [Posisjon.OM,  Posisjon.HA, Posisjon.VA],
    Posisjon.HA:  [Posisjon.HV,  Posisjon.OM, Posisjon.SP],
    Posisjon.VA:  [Posisjon.VV,  Posisjon.OM, Posisjon.SP],
}

# Straffefaktor ved å spille utenfor primærposisjon
# En spiller på sekundærposisjon spiller på PRIMÆR_STRAFF av sin ferdighet
SEKUNDAER_STRAFF = 0.85   # 15% reduksjon

# Å spille på en posisjon man ikke behersker i det hele tatt
UKJENT_POSISJON_STRAFF = 0.65   # 35% reduksjon


def posisjons_effektivitet(
    spiller_primær: Posisjon,
    spiller_sekundær: Optional[Posisjon],
    krevd_posisjon: Posisjon,
) -> float:
    """
    Returnerer en effektivitetsmultiplikator (0.65–1.0) basert på
    hvor godt spilleren passer til den krevde posisjonen.
    """
    if krevd_posisjon == spiller_primær:
        return 1.0
    if spiller_sekundær and krevd_posisjon == spiller_sekundær:
        return SEKUNDAER_STRAFF
    # Sjekk om posisjonen er kompatibel (nærliggende)
    kompatible = KOMPATIBLE_POSISJONER.get(spiller_primær, [])
    if krevd_posisjon in kompatible:
        return SEKUNDAER_STRAFF * 0.95   # Litt bedre enn ren sekundær
    return UKJENT_POSISJON_STRAFF


# =============================================================================
# FORMASJONER
# =============================================================================
@dataclass
class FormasjonSlot:
    """Én posisjon i en formasjon med krevd rolle og sonetilhørighet."""
    posisjon: Posisjon
    sone: str              # "forsvar", "midtbane", "angrep"
    vekt: float = 1.0      # Hvor viktig er denne plassen for lagets styrke?

@dataclass
class Formasjon:
    """
    En komplett formasjon med alle 11 posisjoner,
    taktiske vekter og mentalitetsprofil.
    """
    navn: str
    beskrivelse: str
    mentalitet: str
    slots: list[FormasjonSlot]

    # Taktiske vekter (1.0 = nøytral)
    vekt_angrep: float = 1.0
    vekt_midtbane: float = 1.0
    vekt_forsvar: float = 1.0

    # Matchup-modifikatorer (fylles av TAKTIKK_MATCHUP)
    matchup_bonus: dict[str, float] = field(default_factory=dict)

    @property
    def krav(self) -> dict[str, int]:
        """Teller antall spillere per gruppe (K/F/M/A) som formasjonen krever."""
        teller: dict[str, int] = {"K": 0, "F": 0, "M": 0, "A": 0}
        for slot in self.slots:
            gruppe = POSISJON_GRUPPE.get(slot.posisjon, "M")
            teller[gruppe] += 1
        return teller

    def valider_tropp(self, tropp: list) -> tuple[bool, str]:
        """
        Sjekker om en tropp kan spille denne formasjonen.
        Returnerer (True, "") eller (False, feilmelding).
        """
        krav = self.krav
        tilgjengelig = {"K": 0, "F": 0, "M": 0, "A": 0}
        for spiller in tropp:
            if hasattr(spiller, 'primær_posisjon'):
                gruppe = POSISJON_GRUPPE.get(spiller.primær_posisjon, "M")
                tilgjengelig[gruppe] += 1
        for gruppe, antall in krav.items():
            if tilgjengelig[gruppe] < antall:
                return False, (
                    f"Mangler {antall - tilgjengelig[gruppe]} "
                    f"{gruppe}-spillere for {self.navn}"
                )
        return True, ""

    def __repr__(self):
        return f"<Formasjon: {self.navn} — {self.mentalitet}>"


# =============================================================================
# TAKTIKK-KATALOG
# =============================================================================

# --- 4-3-3 ---
F_4_3_3 = Formasjon(
    navn="4-3-3",
    beskrivelse="Høyt press, kantdominans og offensiv intensitet.",
    mentalitet="Offensiv",
    vekt_angrep=1.15,
    vekt_midtbane=1.0,
    vekt_forsvar=0.85,
    slots=[
        FormasjonSlot(Posisjon.K,   "forsvar",  1.0),
        FormasjonSlot(Posisjon.HB,  "forsvar",  0.9),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.0),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.0),
        FormasjonSlot(Posisjon.VB,  "forsvar",  0.9),
        FormasjonSlot(Posisjon.SM,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.SM,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.SM,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.HV,  "angrep",   1.1),
        FormasjonSlot(Posisjon.SP,  "angrep",   1.0),
        FormasjonSlot(Posisjon.VV,  "angrep",   1.1),
    ],
)

# --- 4-2-3-1 ---
F_4_2_3_1 = Formasjon(
    navn="4-2-3-1",
    beskrivelse="Dobbel defensiv midtbane gir trygg plattform for offensivt spill.",
    mentalitet="Strukturert",
    vekt_angrep=1.05,
    vekt_midtbane=1.10,
    vekt_forsvar=1.10,
    slots=[
        FormasjonSlot(Posisjon.K,   "forsvar",  1.0),
        FormasjonSlot(Posisjon.HB,  "forsvar",  0.9),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.0),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.0),
        FormasjonSlot(Posisjon.VB,  "forsvar",  0.9),
        FormasjonSlot(Posisjon.DM,  "midtbane", 1.1),
        FormasjonSlot(Posisjon.DM,  "midtbane", 1.1),
        FormasjonSlot(Posisjon.HV,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.OM,  "midtbane", 1.1),
        FormasjonSlot(Posisjon.VV,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.SP,  "angrep",   1.0),
    ],
)

# --- 3-5-2 ---
F_3_5_2 = Formasjon(
    navn="3-5-2",
    beskrivelse="Tre midtstoppere og to vingbacks gir bred dekning og offensiv bredde.",
    mentalitet="Defensiv",
    vekt_angrep=0.85,
    vekt_midtbane=1.05,
    vekt_forsvar=1.15,
    slots=[
        FormasjonSlot(Posisjon.K,   "forsvar",  1.0),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.0),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.1),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.0),
        FormasjonSlot(Posisjon.HVB, "midtbane", 1.0),
        FormasjonSlot(Posisjon.SM,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.DM,  "midtbane", 1.1),
        FormasjonSlot(Posisjon.SM,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.VVB, "midtbane", 1.0),
        FormasjonSlot(Posisjon.SP,  "angrep",   1.0),
        FormasjonSlot(Posisjon.SP,  "angrep",   1.0),
    ],
)

# --- 4-4-2 ---
F_4_4_2 = Formasjon(
    navn="4-4-2",
    beskrivelse="Den klassiske formasjonen. Balansert og forutsigbar — vanskelig å overrumple.",
    mentalitet="Balansert",
    vekt_angrep=1.0,
    vekt_midtbane=1.0,
    vekt_forsvar=1.0,
    slots=[
        FormasjonSlot(Posisjon.K,   "forsvar",  1.0),
        FormasjonSlot(Posisjon.HB,  "forsvar",  0.9),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.0),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.0),
        FormasjonSlot(Posisjon.VB,  "forsvar",  0.9),
        FormasjonSlot(Posisjon.HV,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.SM,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.SM,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.VV,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.SP,  "angrep",   1.0),
        FormasjonSlot(Posisjon.SP,  "angrep",   1.0),
    ],
)

# --- 3-4-3 ---
F_3_4_3 = Formasjon(
    navn="3-4-3",
    beskrivelse="Maksimal offensiv kraft. Tre angripere og bred midtbane — høy risiko, høy belønning.",
    mentalitet="Svært offensiv",
    vekt_angrep=1.25,
    vekt_midtbane=1.0,
    vekt_forsvar=0.75,
    slots=[
        FormasjonSlot(Posisjon.K,   "forsvar",  1.0),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.0),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.1),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.0),
        FormasjonSlot(Posisjon.HVB, "midtbane", 1.0),
        FormasjonSlot(Posisjon.SM,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.SM,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.VVB, "midtbane", 1.0),
        FormasjonSlot(Posisjon.HV,  "angrep",   1.1),
        FormasjonSlot(Posisjon.SP,  "angrep",   1.0),
        FormasjonSlot(Posisjon.VV,  "angrep",   1.1),
    ],
)

# --- 5-3-2 ---
F_5_3_2 = Formasjon(
    navn="5-3-2",
    beskrivelse="Fem forsvarere og kompakt midtbane. Dødelig på kontring.",
    mentalitet="Defensiv",
    vekt_angrep=0.85,
    vekt_midtbane=0.95,
    vekt_forsvar=1.20,
    slots=[
        FormasjonSlot(Posisjon.K,   "forsvar",  1.0),
        FormasjonSlot(Posisjon.HVB, "forsvar",  1.0),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.0),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.1),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.0),
        FormasjonSlot(Posisjon.VVB, "forsvar",  1.0),
        FormasjonSlot(Posisjon.SM,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.SM,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.SM,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.SP,  "angrep",   1.0),
        FormasjonSlot(Posisjon.SP,  "angrep",   1.0),
    ],
)

# --- 4-1-4-1 ---
F_4_1_4_1 = Formasjon(
    navn="4-1-4-1",
    beskrivelse="Én ankermann beskytter forsvaret mens fire midtbanere dominerer planet.",
    mentalitet="Kontroll",
    vekt_angrep=0.90,
    vekt_midtbane=1.20,
    vekt_forsvar=1.10,
    slots=[
        FormasjonSlot(Posisjon.K,   "forsvar",  1.0),
        FormasjonSlot(Posisjon.HB,  "forsvar",  0.9),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.0),
        FormasjonSlot(Posisjon.MST, "forsvar",  1.0),
        FormasjonSlot(Posisjon.VB,  "forsvar",  0.9),
        FormasjonSlot(Posisjon.DM,  "midtbane", 1.2),  # Ankermannen
        FormasjonSlot(Posisjon.HV,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.SM,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.SM,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.VV,  "midtbane", 1.0),
        FormasjonSlot(Posisjon.SP,  "angrep",   1.0),
    ],
)

# Samledict — brukes av resten av spillet
TAKTIKK_KATALOG: dict[str, Formasjon] = {
    "4-3-3":   F_4_3_3,
    "4-2-3-1": F_4_2_3_1,
    "3-5-2":   F_3_5_2,
    "4-4-2":   F_4_4_2,
    "3-4-3":   F_3_4_3,
    "5-3-2":   F_5_3_2,
    "4-1-4-1": F_4_1_4_1,
}


# =============================================================================
# TAKTIKK MATCHUP
# Beskriver hvilke formasjoner som slår hverandre
# (hjemme_taktikk, borte_taktikk): (hjemme_modifikator, borte_modifikator)
# =============================================================================
TAKTIKK_MATCHUP: dict[tuple[str, str], tuple[float, float]] = {
    # 4-3-3 kantpress sliter mot fem bak
    ("4-3-3",   "5-3-2"):   (+0.00, +0.10),
    ("4-3-3",   "3-5-2"):   (+0.00, +0.08),
    # 5-3-2 kontring er effektiv mot åpne lag
    ("5-3-2",   "4-3-3"):   (+0.10, +0.00),
    ("5-3-2",   "3-4-3"):   (+0.15, -0.10),
    # 4-1-4-1 kveler angrepsspill i midtbanen
    ("4-1-4-1", "4-3-3"):   (+0.08, -0.05),
    ("4-1-4-1", "3-4-3"):   (+0.12, -0.08),
    # 3-4-3 overbelaster enhver forsvarslinje med bare tre bak
    ("3-4-3",   "4-4-2"):   (+0.10, -0.05),
    ("3-4-3",   "4-2-3-1"): (+0.08, -0.05),
    # 4-2-3-1 håndterer press godt takket være dobbel DM
    ("4-2-3-1", "4-3-3"):   (+0.07, -0.03),
    ("4-2-3-1", "3-4-3"):   (+0.10, -0.05),
    # 4-4-2 klassisk mot klassisk — ingen klar fordel
    ("4-4-2",   "4-4-2"):   (+0.00, +0.00),
}

def hent_matchup_modifikator(
    hjemme_taktikk: str,
    borte_taktikk: str,
) -> tuple[float, float]:
    """
    Returnerer (hjemme_mod, borte_mod) for et taktikk-møte.
    Returnerer (0.0, 0.0) hvis kombinasjonen ikke er definert.
    """
    return TAKTIKK_MATCHUP.get((hjemme_taktikk, borte_taktikk), (0.0, 0.0))


# =============================================================================
# MENTALITET-RESPONS
# Styrer AI-managerens taktiske reaksjoner basert på stillingen
# =============================================================================
MENTALITET_RESPONS: dict[str, dict[str, Optional[str]]] = {
    "Offensiv": {
        "leder_med_2":    None,          # Beholder offensiv taktikk
        "leder_med_1":    None,
        "uavgjort":       None,
        "taper_med_1":    "4-3-3",       # Mer press
        "taper_med_2":    "3-4-3",       # Alt inn
    },
    "Svært offensiv": {
        "leder_med_2":    "4-3-3",       # Litt mer forsiktig
        "leder_med_1":    None,
        "uavgjort":       None,
        "taper_med_1":    None,
        "taper_med_2":    None,          # Beholder — spiller alltid offensivt
    },
    "Balansert": {
        "leder_med_2":    "5-3-2",       # Sikrer seieren
        "leder_med_1":    "4-4-2",       # Stabiliserer
        "uavgjort":       None,
        "taper_med_1":    "4-3-3",       # Søker mål
        "taper_med_2":    "3-4-3",       # Desperat grep
    },
    "Strukturert": {
        "leder_med_2":    "4-1-4-1",     # Kontrollerer
        "leder_med_1":    "4-2-3-1",     # Holder strukturen
        "uavgjort":       None,
        "taper_med_1":    "4-3-3",
        "taper_med_2":    "3-4-3",
    },
    "Kontroll": {
        "leder_med_2":    "4-1-4-1",
        "leder_med_1":    "4-1-4-1",
        "uavgjort":       "4-1-4-1",     # Alltid kontroll
        "taper_med_1":    "4-2-3-1",     # Litt mer offensiv
        "taper_med_2":    "4-3-3",
    },
    "Defensiv": {
        "leder_med_2":    "5-3-2",
        "leder_med_1":    "5-3-2",
        "uavgjort":       "5-3-2",       # Defensiv uansett
        "taper_med_1":    "4-4-2",
        "taper_med_2":    "4-3-3",
    },
}

def hent_taktisk_respons(
    mentalitet: str,
    hjemme_maal: int,
    borte_maal: int,
    er_hjemmelag: bool,
) -> Optional[str]:
    """
    Returnerer en ny formasjon AI-manageren bør bytte til,
    eller None hvis gjeldende taktikk beholdes.
    """
    respons = MENTALITET_RESPONS.get(mentalitet, {})
    if er_hjemmelag:
        diff = hjemme_maal - borte_maal
    else:
        diff = borte_maal - hjemme_maal

    if diff >= 2:
        situasjon = "leder_med_2"
    elif diff == 1:
        situasjon = "leder_med_1"
    elif diff == 0:
        situasjon = "uavgjort"
    elif diff == -1:
        situasjon = "taper_med_1"
    else:
        situasjon = "taper_med_2"

    ny_taktikk = respons.get(situasjon)

    # Valider at formasjonen faktisk finnes i katalogen
    if ny_taktikk and ny_taktikk not in TAKTIKK_KATALOG:
        return None
    return ny_taktikk


# =============================================================================
# OPPSTILLING
# Binder en formasjon til konkrete spillere
# =============================================================================
@dataclass
class Oppstilling:
    """
    Et lags konkrete kampoppstilling:
    formasjon + hvilken spiller som spiller hvilken slot.
    """
    formasjon: Formasjon
    # slot_indeks → spiller-objekt
    plasseringer: dict[int, object] = field(default_factory=dict)

    def sett_spiller(self, slot_indeks: int, spiller):
        self.plasseringer[slot_indeks] = spiller

    def er_komplett(self) -> bool:
        return len(self.plasseringer) == 11

    def beregn_sone_styrke(self, sone: str) -> float:
        """
        Beregner lagets samlede styrke i en gitt sone
        ("forsvar", "midtbane", "angrep").
        Tar hensyn til spillernes posisjonelle effektivitet og slot-vekter.
        """
        total = 0.0
        teller = 0
        for i, slot in enumerate(self.formasjon.slots):
            if slot.sone != sone:
                continue
            spiller = self.plasseringer.get(i)
            if not spiller:
                continue
            ferdighet = getattr(spiller, 'ferdighet', 10)
            primær    = getattr(spiller, 'primær_posisjon', None)
            sekundær  = getattr(spiller, 'sekundær_posisjon', None)
            effektivitet = posisjons_effektivitet(primær, sekundær, slot.posisjon)
            total += ferdighet * effektivitet * slot.vekt
            teller += 1
        return total / teller if teller > 0 else 0.0

    def beregn_total_styrke(self) -> dict[str, float]:
        """Returnerer styrkeverdier for alle tre soner."""
        return {
            "forsvar":   self.beregn_sone_styrke("forsvar"),
            "midtbane":  self.beregn_sone_styrke("midtbane"),
            "angrep":    self.beregn_sone_styrke("angrep"),
        }

    def __repr__(self):
        komplett = "komplett" if self.er_komplett() else f"{len(self.plasseringer)}/11"
        return f"<Oppstilling: {self.formasjon.navn} ({komplett})>"
