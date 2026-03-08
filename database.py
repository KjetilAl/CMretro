"""
database.py — Databaselaget for norsk fotballmanagerspill.

Ansvar:
  1. Les lag.json og spillere.json
  2. Valider og fyll inn manglende data (0-felter og manglende spillere)
  3. Bygg ferdige Klubb- og Person-objekter klar til bruk i spillmotoren

Designprinsipp:
  - Aldri skriv til lag.json eller spillere.json automatisk.
  - Genererte spillere lagres i data/generert/spillere_generert.json
    slik at du kan inspisere og eventuelt flytte dem til hoved-filen.
"""

import json
import os
import random
import math
from pathlib import Path
from typing import Optional

from person import Person, SpillerRolle
from klubb import Klubb, Stadion
from taktikk import Posisjon, POSISJON_GRUPPE

# =============================================================================
# STIER
# =============================================================================
DATA_DIR      = Path(__file__).parent / "data"
LAG_FIL       = DATA_DIR / "lag.json"
SPILLERE_FIL  = DATA_DIR / "spillere.json"
GENERERT_DIR  = DATA_DIR / "generert"
GENERERT_FIL  = GENERERT_DIR / "spillere_generert.json"

# =============================================================================
# MINIMUMSKRAV PER POSISJONGRUPPE
# =============================================================================
MINIMUM_PER_GRUPPE = {
    "K": 2,
    "F": 6,
    "M": 6,
    "A": 4,
}
MINIMUM_TOTALT = sum(MINIMUM_PER_GRUPPE.values())   # 18

# Norske fornavn og etternavn for genererte spillere
FORNAVN = [
    "Magnus", "Erik", "Lars", "Ole", "Jonas", "Kristian", "Andreas", "Håkon",
    "Sander", "Tobias", "Mathias", "Martin", "Henrik", "Sindre", "Markus",
    "Steffen", "Joakim", "Eirik", "Torbjørn", "Vegard", "Petter", "Rune",
    "Espen", "Trond", "Øyvind", "Bjørn", "Stian", "Thomas", "Morten", "Geir",
]
ETTERNAVN = [
    "Hansen", "Johansen", "Olsen", "Larsen", "Andersen", "Pedersen", "Nilsen",
    "Kristiansen", "Jensen", "Karlsen", "Haugen", "Bakke", "Hagen", "Eriksen",
    "Berg", "Strand", "Moen", "Dahl", "Lund", "Sørensen", "Lie", "Holm",
    "Nygaard", "Berge", "Solberg", "Thorsen", "Aas", "Halvorsen", "Vold", "Ask",
]

# Posisjoner per gruppe — brukes ved generering
POSISJONER_PER_GRUPPE: dict[str, list[str]] = {
    "K": ["K"],
    "F": ["HB", "VB", "HVB", "VVB"],
    "M": ["MST", "DM", "SM", "OM"],
    "A": ["HV", "VV", "SP", "HA", "VA"],
}

# Sekundærposisjoner som er naturlige for primærposisjoner
NATURLIG_SEKUNDÆR: dict[str, list[str]] = {
    "HB":  ["HVB"],
    "VB":  ["VVB"],
    "HVB": ["HB", "MST"],
    "VVB": ["VB", "MST"],
    "MST": ["DM"],
    "DM":  ["MST", "SM"],
    "SM":  ["DM", "OM"],
    "OM":  ["SM", "HV", "VV"],
    "HV":  ["OM", "SP", "HA"],
    "VV":  ["OM", "SP", "VA"],
    "SP":  ["HV", "VV"],
    "HA":  ["HV", "SP"],
    "VA":  ["VV", "SP"],
    "K":   [],
}


# =============================================================================
# SANNSYNLIGHETSFORDELINGER
# =============================================================================
def _normalfordelt(gjennomsnitt: float, std: float,
                   minimum: int = 1, maksimum: int = 20) -> int:
    """
    Trekker en heltallsverdi fra en normalfordeling,
    klippet til [minimum, maksimum].
    """
    verdi = random.gauss(gjennomsnitt, std)
    return max(minimum, min(maksimum, round(verdi)))


def _ferdighet_for_lag(historisk_styrke: int) -> int:
    """
    Beregner ferdighetsgjennomsnitt og std basert på lagets historiske styrke.

    Styrke 20 (topplag):  snitt 16, std 2.0  → spillere 12–20
    Styrke 10 (midtlag):  snitt 10, std 2.5  → spillere  5–15
    Styrke  1 (bunnlag):  snitt  6, std 2.0  → spillere  2–10
    """
    snitt = 4.0 + (historisk_styrke / 20.0) * 13.0
    std   = 2.0 + (1.0 - abs(historisk_styrke - 10) / 10.0) * 0.5
    return _normalfordelt(snitt, std)


def _personlighet() -> dict[str, int]:
    """
    Genererer et sett personlighetsattributter.
    Normalfordelt rundt 10, std 3.5 — de fleste er middels.
    """
    return {
        "lojalitet":      _normalfordelt(10, 3.5),
        "egoisme":        _normalfordelt(10, 3.5),
        "presstoleranse": _normalfordelt(10, 3.5),
        "arbeidsvilje":   _normalfordelt(10, 3.5),
    }


def _utholdenhet(ferdighet: int) -> int:
    """
    Utholdenhet er svakt korrelert med ferdighet,
    men med mye variasjon — en god spiller kan ha dårlig utholdenhet.
    """
    snitt = 7.0 + (ferdighet / 20.0) * 6.0   # 7–13 avhengig av ferdighet
    return _normalfordelt(snitt, 3.0)


def _alder_for_posisjon(gruppe: str) -> int:
    """
    Keepere og forsvarsspillere er gjerne litt eldre.
    Angripere har bredere aldersfordeling.
    """
    if gruppe == "K":
        return _normalfordelt(28, 4, minimum=18, maksimum=38)
    elif gruppe == "F":
        return _normalfordelt(26, 4, minimum=17, maksimum=36)
    elif gruppe == "M":
        return _normalfordelt(25, 4, minimum=17, maksimum=35)
    else:
        return _normalfordelt(24, 4, minimum=17, maksimum=34)


# =============================================================================
# GENERERING AV ENKELTSPILLER
# =============================================================================
_brukte_navn: set[str] = set()
_id_teller: int = 0


def _generer_navn() -> tuple[str, str]:
    """Trekker et unikt for- og etternavn."""
    global _id_teller
    for _ in range(100):
        fornavn   = random.choice(FORNAVN)
        etternavn = random.choice(ETTERNAVN)
        nøkkel    = f"{fornavn}_{etternavn}"
        if nøkkel not in _brukte_navn:
            _brukte_navn.add(nøkkel)
            return fornavn, etternavn
    # Fallback med teller
    _id_teller += 1
    return "Spiller", f"Nr{_id_teller:03d}"


def _generer_spiller(
    lag_id: str,
    historisk_styrke: int,
    gruppe: str,
    spiller_id: Optional[str] = None,
) -> dict:
    """
    Genererer én komplett spillerdict klar til lagring og innlasting.
    """
    fornavn, etternavn = _generer_navn()
    primær = random.choice(POSISJONER_PER_GRUPPE[gruppe])
    sek_kandidater = NATURLIG_SEKUNDÆR.get(primær, [])
    sekundær = random.choice(sek_kandidater) if sek_kandidater and random.random() < 0.4 else None
    attributter = _generer_attributter_for_posisjon(gruppe, historisk_styrke)
    personl = _personlighet()
    
    # Sett potensial til å være minst like høyt som nåværende evne, ofte høyere for unge
    snitt_ferdighet = sum(attributter.values()) / len(attributter)
    alder = _alder_for_posisjon(gruppe)
    potensial_bonus = max(0, (25 - alder) // 2) + random.randint(0, 3)
    potensial = min(20, round(snitt_ferdighet + potensial_bonus))

    return {
        "id": sid,
        "fornavn": fornavn,
        "etternavn": etternavn,
        "alder": alder,
        "lag_id": lag_id,
        "primær_posisjon": primær,
        "sekundær_posisjon": sekundær,
        "potensial": potensial,
        "rykte": historisk_styrke + random.randint(-2, 2),
        **attributter,  # Pakker ut alle 14 ferdighetene!
        **personl,
        "_generert": True,
    }

def _generer_attributter_for_posisjon(gruppe: str, base_styrke: int) -> dict:
    """
    Genererer et sett med 14 ferdigheter.
    base_styrke er lagets historiske styrke (f.eks. 15 for Molde, 5 for amatører).
    """
    # Vi lager en mal der 1.0 er "normalt for dette laget", > 1.0 er spesialist
    profiler = {
        "K": {"keeperferdighet": 1.5, "fysikk": 1.2, "mentalitet": 1.2, "skudd": 0.2, "dribling": 0.2},
        "F": {"takling": 1.5, "hodespill": 1.3, "fysikk": 1.3, "aggressivitet": 1.2, "skudd": 0.5},
        "M": {"pasning": 1.5, "teknikk": 1.3, "kreativitet": 1.4, "utholdenhet": 1.3, "keeperferdighet": 0.1},
        "A": {"skudd": 1.5, "fart": 1.3, "dribling": 1.3, "teknikk": 1.2, "keeperferdighet": 0.1}
    }
    
    profil = profiler.get(gruppe, profiler["M"])
    attributter = {}
    
    alle_ferdigheter = [
        "skudd", "pasning", "dribling", "takling", "hodespill", "teknikk", 
        "dodball", "keeperferdighet", "fart", "utholdenhet", "fysikk", 
        "kreativitet", "aggressivitet", "mentalitet"
    ]
    
    for ferdighet in alle_ferdigheter:
        vekt = profil.get(ferdighet, 1.0) # Standard vekt er 1.0
        
        # Trekker et tall normalfordelt rundt lagets styrke * vekt
        snitt = base_styrke * vekt
        # Legg inn litt tilfeldig variasjon
        verdi = random.gauss(snitt, 2.5) 
        
        attributter[ferdighet] = max(1, min(20, round(verdi)))
        
    return attributter
# =============================================================================
# FYLL INN 0-VERDIER FOR EN EKSISTERENDE SPILLERDICT
# =============================================================================
def _fyll_inn_nullverdier(spiller_dict: dict, historisk_styrke: int) -> dict:
    """
    Erstatter 0-verdier med genererte verdier.
    Berører aldri felt som allerede har en verdi != 0.
    """
    d = dict(spiller_dict)

    if d.get("ferdighet", 0) == 0:
        d["ferdighet"] = _ferdighet_for_lag(historisk_styrke)

    if d.get("utholdenhet", 0) == 0:
        d["utholdenhet"] = _utholdenhet(d["ferdighet"])

    for felt in ("lojalitet", "egoisme", "presstoleranse", "arbeidsvilje"):
        if d.get(felt, 0) == 0:
            d[felt] = _normalfordelt(10, 3.5)

    return d


# =============================================================================
# BYGG PERSON-OBJEKT FRA DICT
# =============================================================================
def _bygg_person(d: dict, klubb: Klubb, sesong_aar: int) -> Person:
    """Konverterer en spillerdict til et Person-objekt med SpillerRolle."""
    person = Person(
        id            = d["id"],
        fornavn       = d["fornavn"],
        etternavn     = d["etternavn"],
        alder         = d["alder"],
        lojalitet     = d["lojalitet"],
        egoisme       = d["egoisme"],
        presstoleranse= d["presstoleranse"],
        arbeidsvilje  = d["arbeidsvilje"],
        utholdenhet   = d["utholdenhet"],
    )

    primær_pos = Posisjon[d["primær_posisjon"]]
    rolle = SpillerRolle(
        start_aar  = sesong_aar - random.randint(0, 3),
        klubb      = klubb,
        posisjon   = primær_pos,
        ferdighet  = d["ferdighet"],
    )
    # Sekundærposisjon lagres direkte på Person for bruk i taktikk
    if d.get("sekundær_posisjon"):
        person.sekundær_posisjon = Posisjon[d["sekundær_posisjon"]]
    else:
        person.sekundær_posisjon = None

    person.primær_posisjon = primær_pos
    person.ferdighet       = d["ferdighet"]
    person.legg_til_rolle(rolle)
    return person


# =============================================================================
# BYGG KLUBB-OBJEKT FRA DICT
# =============================================================================
def _bygg_klubb(d: dict) -> Klubb:
    stadion = Stadion(
        navn      = d["stadion_navn"],
        kapasitet = d["stadion_kapasitet"],
        standard  = d["stadion_standard"],
        byggeaar  = d["stadion_byggeaar"],
    )
    
    styrke = d.get("historisk_styrke", 10)
    divisjon = d.get("divisjon", "Eliteserien")
    
    # Dynamisk økonomi basert på divisjon + styrke
    base_budsjett = 0
    if divisjon == "Eliteserien": base_budsjett = 20_000_000
    elif divisjon == "OBOS-ligaen": base_budsjett = 5_000_000
    elif divisjon == "PostNord-ligaen": base_budsjett = 1_000_000
    else: base_budsjett = 250_000
    
    multiplikator = 1.0 + ((styrke - 10) / 3.33)
    budsjett = int(base_budsjett * max(0.5, multiplikator))
    lønn = int(budsjett * 0.05)

    supporterbase     = max(1, min(20, styrke - 1 + random.randint(-2, 2)))
    ambisjonsnivaa    = max(1, min(20, styrke - 2 + random.randint(-1, 1)))
    historisk_suksess = max(1, min(20, styrke + random.randint(-3, 3)))

    klubb = Klubb(
        id                      = d["id"],
        navn                    = d["navn"],
        kortnavn                = d.get("kortnamn", d.get("kortnavn", d["navn"][:3].upper())),
        grunnlagt_aar           = d.get("grunnlagt_aar", 1900),
        farger                  = d.get("farger", ["Blå", "Hvit"]),
        stadion                 = stadion,
        divisjon                = divisjon,
        budsjett                = budsjett,
        ukentlig_loennsbudsjett = lønn,
        gjeld                   = int(budsjett * 0.15), # Liten startgjeld for realisme
        supporterbase           = supporterbase,
        ambisjonsnivaa          = ambisjonsnivaa,
        historisk_suksess       = historisk_suksess,
        intern_uro              = random.randint(1, 10), # Litt tilfeldig drama fra start!
        okonomi_problem         = 1,
    )
    # Beholder ID-ene som strenger inntil videre, lette å koble senere
    klubb.rival_ider = d.get("rivaler", []) 
    klubb.historisk_styrke = styrke
    klubb.by = d.get("by", "")
    return klubb


# =============================================================================
# HOVED-API: last_database()
# =============================================================================
def last_database(
    sesong_aar: int = 2025,
    lag_fil: Path = LAG_FIL,
    spillere_fil: Path = SPILLERE_FIL,
    verbose: bool = True,
) -> dict[str, Klubb]:
    """
    Leser lag.json og spillere.json, fyller inn manglende data,
    og returnerer en dict { lag_id → Klubb } med ferdig befolkede spillerstall.

    Genererte spillere skrives til data/generert/spillere_generert.json
    for inspeksjon.
    """
    GENERERT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Les JSON ---
    with open(lag_fil, encoding="utf-8") as f:
        lag_liste: list[dict] = json.load(f)

    with open(spillere_fil, encoding="utf-8") as f:
        spillere_liste: list[dict] = json.load(f)

    # --- Bygg klubb-objekter ---
    klubber: dict[str, Klubb] = {}
    for lag_dict in lag_liste:
        klubb = _bygg_klubb(lag_dict)
        klubber[lag_dict["id"]] = klubb

    # --- Grupper eksisterende spillere per lag ---
    spillere_per_lag: dict[str, list[dict]] = {lid: [] for lid in klubber}
    for s in spillere_liste:
        lag_id = s.get("lag_id")
        if lag_id in spillere_per_lag:
            styrke = klubber[lag_id].historisk_styrke
            spillere_per_lag[lag_id].append(_fyll_inn_nullverdier(s, styrke))

    # --- Generer manglende spillere ---
    nye_genererte: list[dict] = []

    for lag_id, klubb in klubber.items():
        eksisterende = spillere_per_lag[lag_id]
        styrke       = klubb.historisk_styrke

        # Tell opp per gruppe
        antall_per_gruppe: dict[str, int] = {g: 0 for g in MINIMUM_PER_GRUPPE}
        for s in eksisterende:
            pos   = s.get("primær_posisjon", "")
            gruppe = POSISJON_GRUPPE.get(Posisjon[pos]) if pos in Posisjon.__members__ else None
            if gruppe in antall_per_gruppe:
                antall_per_gruppe[gruppe] += 1

        # Generer det som mangler
        for gruppe, minimum in MINIMUM_PER_GRUPPE.items():
            mangler = minimum - antall_per_gruppe[gruppe]
            for _ in range(mangler):
                ny = _generer_spiller(lag_id, styrke, gruppe)
                spillere_per_lag[lag_id].append(ny)
                nye_genererte.append(ny)

        if verbose:
            totalt = len(spillere_per_lag[lag_id])
            gen    = sum(1 for s in spillere_per_lag[lag_id] if s.get("_generert"))
            manuell = totalt - gen
            print(f"  {klubb.navn:<25} {totalt:>2} spillere "
                  f"({manuell} manuelle, {gen} genererte)")

    # --- Lagre genererte spillere for inspeksjon ---
    if nye_genererte:
        with open(GENERERT_FIL, "w", encoding="utf-8") as f:
            json.dump(nye_genererte, f, ensure_ascii=False, indent=2)
        if verbose:
            print(f"\n  ✓ {len(nye_genererte)} genererte spillere lagret i "
                  f"{GENERERT_FIL.relative_to(DATA_DIR.parent)}")

    # --- Bygg Person-objekter og legg til i klubbene ---
    for lag_id, klubb in klubber.items():
        for s_dict in spillere_per_lag[lag_id]:
            person = _bygg_person(s_dict, klubb, sesong_aar)
            klubb.legg_til_person(person)

    if verbose:
        print(f"\n  ✓ {len(klubber)} klubber lastet inn.")

    return klubber


# =============================================================================
# HJELPEFUNKSJONER FOR SPILLMOTOR
# =============================================================================
def hent_spillere_for_lag(klubb: Klubb) -> list[Person]:
    """Returnerer alle spillere i en klubb, sortert etter ferdighet."""
    return sorted(
        klubb.spillerstall,
        key=lambda s: getattr(s, 'ferdighet', 0),
        reverse=True,
    )


def hent_spilleklar_tropp(klubb: Klubb) -> list[Person]:
    """Returnerer spillere som er friske og over kondisjongrensen."""
    return [s for s in klubb.spillerstall if getattr(s, 'er_spilleklar', True)]


def foreslå_startellever(klubb: Klubb, formasjon_navn: str = "4-3-3 (Offensiv)") -> dict:
    """
    Foreslår beste startellever basert på tilgjengelige spillere og formasjon.
    Returnerer { posisjon_slot → Person }.

    Algoritme:
      1. Hent spilleklar tropp
      2. For hvert posisjon-slot i formasjonen:
         a. Finn spillere med primær- eller sekundærposisjon for sloten
         b. Sorter etter effektiv_ferdighet
         c. Velg den beste som ikke allerede er plassert
    """
    from taktikk import TAKTIKK_KATALOG, Posisjon, KOMPATIBLE_POSISJONER

    formasjon = TAKTIKK_KATALOG.get(formasjon_navn)
    if not formasjon:
        # Fallback til første tilgjengelige formasjon
        formasjon = next(iter(TAKTIKK_KATALOG.values()))

    tropp     = hent_spilleklar_tropp(klubb)
    plassert  = set()
    startellever: dict[str, Person] = {}

    # Sorter slots: keeper først, deretter forsvar, midtbane, angrep
    gruppe_rekkefølge = {"K": 0, "F": 1, "M": 2, "A": 3}
    slots = sorted(
        formasjon.slots,
        key=lambda slot: gruppe_rekkefølge.get(
            POSISJON_GRUPPE.get(slot, "M"), 2
        ),
    )

    for slot in slots:
        kandidater = []
        for spiller in tropp:
            if id(spiller) in plassert:
                continue
            primær   = getattr(spiller, 'primær_posisjon', None)
            sekundær = getattr(spiller, 'sekundær_posisjon', None)

            if primær == slot:
                effektivitet = 1.0
            elif sekundær == slot:
                effektivitet = 0.85
            elif primær and slot in KOMPATIBLE_POSISJONER.get(primær, set()):
                effektivitet = 0.81
            else:
                continue   # Ikke aktuell for denne sloten

            ferdighet  = getattr(spiller, 'ferdighet', 0)
            kondisjon  = getattr(spiller, 'kondisjon', 100.0)
            score      = ferdighet * effektivitet * (kondisjon / 100.0)
            kandidater.append((score, spiller))

        if kandidater:
            kandidater.sort(key=lambda x: x[0], reverse=True)
            valgt = kandidater[0][1]
            startellever[slot] = valgt
            plassert.add(id(valgt))

    return startellever


# =============================================================================
# TEST
# =============================================================================
if __name__ == "__main__":
    print("\nLaster database...\n")
    klubber = last_database(sesong_aar=2025)

    print("\nSpillerfordeling for tre lag:")
    for lag_id in ["bodoglimt", "molde", "kongsvinger"]:
        klubb  = klubber[lag_id]
        tropp  = hent_spillere_for_lag(klubb)
        print(f"\n  {klubb.navn}")
        for s in tropp[:5]:
            pos    = getattr(s, 'primær_posisjon', '?')
            kond   = f"{s.kondisjon:.0f}%"
            gen    = " [gen]" if not s.id.count('_') == 1 else ""
            print(f"    {s.etternavn:<18} {str(pos.name):<5} "
                  f"Ferdighet: {s.ferdighet:<3} Kond: {kond}{gen}")
        if len(tropp) > 5:
            print(f"    ... og {len(tropp)-5} til")
