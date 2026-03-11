"""
person.py  –  Norsk Football Manager '95
Spillermodellen. Alle ferdigheter er på skalaen 1–20.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
import random

# Globale skalagrenser — brukes på tvers av moduler
SKALA_MIN: int = 1
SKALA_MAX: int = 20


# ── Roller ────────────────────────────────────────────────────────────────────

class SpillerRolle:
    """Markør: personen er registrert som aktiv spiller i en klubb."""
    pass

class TrenerRolle:
    """Markør: personen er registrert som trener."""
    spesialitet: str = ""

    def __init__(self, spesialitet: str = "Generell"):
        self.spesialitet = spesialitet

class ManagerRolle:
    """Markør: personen er registrert som manager/hovedtrener."""
    pass


# ── Posisjoner ────────────────────────────────────────────────────────────────

class Posisjon(Enum):
    # Keeper
    K   = auto()
    # Forsvar
    MST = auto()   # Midtstopper
    HB  = auto()   # Høyreback
    VB  = auto()   # Venstrebak
    # Midtbane
    DM  = auto()   # Defensiv midtbane
    SM  = auto()   # Sentral midtbane
    OM  = auto()   # Offensiv midtbane
    HVB = auto()   # Høyre vingback
    VVB = auto()   # Venstre vingback
    HV  = auto()   # Høyre vinge
    VV  = auto()   # Venstre vinge
    # Angrep
    SP  = auto()   # Spiss
    HA  = auto()   # Høyre angriper
    VA  = auto()   # Venstre angriper


# Hvilke posisjoner hører til hvilken linje
FORSVAR   = {Posisjon.MST, Posisjon.HB,  Posisjon.VB}
MIDTBANE  = {Posisjon.DM,  Posisjon.SM,  Posisjon.OM,
             Posisjon.HVB, Posisjon.VVB, Posisjon.HV, Posisjon.VV}
ANGREP    = {Posisjon.SP,  Posisjon.HA,  Posisjon.VA}


# ── Skadetyper ────────────────────────────────────────────────────────────────

class SkadeType(Enum):
    INGEN        = "Ingen skade"
    FORSTUING    = "Forstuing"
    MUSKELSTREKK = "Muskelstrekk"
    BRUDD        = "Brudd"
    HJERNERYSTELSE = "Hjernerystelse"
    KORSBANDSKADE  = "Korsbåndskade"


SKADE_DAGER: dict[SkadeType, tuple[int, int]] = {
    SkadeType.FORSTUING:      (3,  10),
    SkadeType.MUSKELSTREKK:   (7,  21),
    SkadeType.BRUDD:          (21, 60),
    SkadeType.HJERNERYSTELSE: (5,  14),
    SkadeType.KORSBANDSKADE:  (90, 270),
}

# Sannsynlighet for at en skade er av en gitt type (summerer til 1.0)
SKADE_SANNSYNLIGHET: list[tuple[SkadeType, float]] = [
    (SkadeType.FORSTUING,       0.40),
    (SkadeType.MUSKELSTREKK,    0.30),
    (SkadeType.BRUDD,           0.12),
    (SkadeType.HJERNERYSTELSE,  0.10),
    (SkadeType.KORSBANDSKADE,   0.08),
]


# ── Vektmatrisen for ferdighet per posisjon ───────────────────────────────────
#
# Hvert oppslag er en dict  {attributtnavn: vekt}.
# OVR = sum(vekt * verdi) / sum(vekter)  →  garantert rettferdig sammenligning.

_OVR_VEKTER: dict[Posisjon, dict[str, int]] = {
    Posisjon.K: {
        "keeperferdighet": 4,
        "fysikk":          2,
        "mentalitet":      2,
        "pasning":         1,
        "fart":            1,
    },
    Posisjon.MST: {
        "takling":    4,
        "hodespill":  3,
        "fysikk":     2,
        "fart":       1,
        "pasning":    1,
        "mentalitet": 1,
    },
    Posisjon.HB: {
        "takling":   3,
        "fart":      3,
        "hodespill": 2,
        "pasning":   2,
        "fysikk":    1,
        "dribling":  1,
    },
    Posisjon.VB: {
        "takling":   3,
        "fart":      3,
        "hodespill": 2,
        "pasning":   2,
        "fysikk":    1,
        "dribling":  1,
    },
    Posisjon.DM: {
        "takling":      3,
        "pasning":      3,
        "utholdenhet":  2,
        "fysikk":       2,
        "mentalitet":   2,
        "teknikk":      1,
    },
    Posisjon.SM: {
        "pasning":     3,
        "teknikk":     3,
        "kreativitet": 2,
        "utholdenhet": 2,
        "takling":     1,
        "fart":        1,
    },
    Posisjon.OM: {
        "pasning":     3,
        "kreativitet": 3,
        "teknikk":     3,
        "skudd":       2,
        "dribling":    2,
        "fart":        1,
    },
    Posisjon.HVB: {
        "fart":      3,
        "takling":   3,
        "pasning":   2,
        "utholdenhet": 2,
        "dribling":  1,
        "hodespill": 1,
    },
    Posisjon.VVB: {
        "fart":      3,
        "takling":   3,
        "pasning":   2,
        "utholdenhet": 2,
        "dribling":  1,
        "hodespill": 1,
    },
    Posisjon.HV: {
        "fart":      4,
        "dribling":  3,
        "pasning":   2,
        "teknikk":   2,
        "skudd":     1,
        "kreativitet": 1,
    },
    Posisjon.VV: {
        "fart":      4,
        "dribling":  3,
        "pasning":   2,
        "teknikk":   2,
        "skudd":     1,
        "kreativitet": 1,
    },
    Posisjon.SP: {
        "skudd":     4,
        "hodespill": 3,
        "fart":      2,
        "teknikk":   2,
        "fysikk":    2,
        "dribling":  1,
    },
    Posisjon.HA: {
        "fart":      3,
        "skudd":     3,
        "dribling":  3,
        "teknikk":   2,
        "kreativitet": 2,
        "pasning":   1,
    },
    Posisjon.VA: {
        "fart":      3,
        "skudd":     3,
        "dribling":  3,
        "teknikk":   2,
        "kreativitet": 2,
        "pasning":   1,
    },
}

# Fallback for ukjent posisjon
_OVR_FALLBACK: dict[str, int] = {
    "pasning": 1, "takling": 1, "skudd": 1,
    "fart": 1, "teknikk": 1,
}


# ── Hjelpefunksjon: valider attributtverdi ────────────────────────────────────

def _sjekk_verdi(navn: str, verdi: int, min_v: int = 1, maks_v: int = 20) -> int:
    if not isinstance(verdi, int):
        raise TypeError(f"'{navn}' må være int, fikk {type(verdi).__name__}")
    if not min_v <= verdi <= maks_v:
        raise ValueError(f"'{navn}' må være {min_v}–{maks_v}, fikk {verdi}")
    return verdi


_FERDIGHET_ATTRS = (
    "skudd", "pasning", "dribling", "takling", "hodespill",
    "teknikk", "dodball", "keeperferdighet",
    "fart", "utholdenhet", "fysikk",
    "kreativitet", "aggressivitet", "mentalitet",
)

_META_ATTRS = (
    "lojalitet", "egoisme", "presstoleranse",
    "arbeidsvilje", "potensial", "rykte",
)


# ── Person ────────────────────────────────────────────────────────────────────

class Person:
    """
    Representerer en spillbar person (spiller eller trener).

    Ferdigheter og meta-verdier er på skalaen 1–20.
    Kondisjon og in_game_kondisjon er prosent (0.0–100.0).
    """

    # ── Konstruktør ───────────────────────────────────────────────────────────

    def __init__(
        self,
        id: str,
        fornavn: str,
        etternavn: str,
        alder: int,
        # Tekniske ferdigheter
        skudd:           int = 10,
        pasning:         int = 10,
        dribling:        int = 10,
        takling:         int = 10,
        hodespill:       int = 10,
        teknikk:         int = 10,
        dodball:         int = 10,
        keeperferdighet: int = 10,
        # Fysiske ferdigheter
        fart:            int = 10,
        utholdenhet:     int = 10,
        fysikk:          int = 10,
        # Mentale ferdigheter
        kreativitet:     int = 10,
        aggressivitet:   int = 10,
        mentalitet:      int = 10,
        # Meta / skjulte verdier
        lojalitet:       int = 10,   # Påvirker kontraktvilje og klubbtilhørighet
        egoisme:         int = 10,   # Høy: skyter fremfor å passe; lav: lagorientert
        presstoleranse:  int = 10,   # Prestasjon under press (cup-finaler, nedrykk)
        arbeidsvilje:    int = 10,   # Treningsutbytte og kondisjonsnedgang
        potensial:       int = 10,   # Maksimal mulig OVR (1–20)
        rykte:           int = 10,   # Markedsverdi/kjennskap (1–20)
    ):
        # Identitet
        self.id        = id
        self.fornavn   = fornavn
        self.etternavn = etternavn

        if not isinstance(alder, int) or not 15 <= alder <= 45:
            raise ValueError(f"Alder må være 15–45, fikk {alder}")
        self.alder = alder

        # Valider og sett ferdigheter
        for navn, verdi in (
            ("skudd",           skudd),
            ("pasning",         pasning),
            ("dribling",        dribling),
            ("takling",         takling),
            ("hodespill",       hodespill),
            ("teknikk",         teknikk),
            ("dodball",         dodball),
            ("keeperferdighet", keeperferdighet),
            ("fart",            fart),
            ("utholdenhet",     utholdenhet),
            ("fysikk",          fysikk),
            ("kreativitet",     kreativitet),
            ("aggressivitet",   aggressivitet),
            ("mentalitet",      mentalitet),
        ):
            setattr(self, navn, _sjekk_verdi(navn, verdi))

        # Valider og sett meta-verdier
        for navn, verdi in (
            ("lojalitet",      lojalitet),
            ("egoisme",        egoisme),
            ("presstoleranse", presstoleranse),
            ("arbeidsvilje",   arbeidsvilje),
            ("potensial",      potensial),
            ("rykte",          rykte),
        ):
            setattr(self, navn, _sjekk_verdi(navn, verdi))

        # Tilstand
        self.kontrakt          = None
        self.form_historikk: list[str] = []
        self.kondisjon         = 100.0   # Sesongkondisjon (faller ved manglende hvile)
        self.in_game_kondisjon = 100.0   # Kampkondisjon   (nullstilles etter kamp)
        self.skadet            = False
        self.skade_dager_igjen = 0
        self.skade_type        = SkadeType.INGEN

        # Posisjoner og roller
        self.primær_posisjon:    Optional[Posisjon] = None
        self.sekundær_posisjon:  Optional[Posisjon] = None
        self.roller:             list[Posisjon]     = []

        # Klubb-rolle og kontrakt — settes eksternt av klubb/økonomi-modulen
        self._naavaerende_rolle = None   # SpillerRolle | TrenerRolle | ManagerRolle
        self.kontrakt           = None   # Kontrakt-objekt fra okonomi.py

    # ── Navn-hjelper ──────────────────────────────────────────────────────────

    @property
    def fullt_navn(self) -> str:
        return f"{self.fornavn} {self.etternavn}"

    @property
    def kortnavn(self) -> str:
        return f"{self.fornavn[0]}. {self.etternavn}"

    def hent_naavaerende_rolle(self):
        """Returnerer aktivt rolle-objekt (SpillerRolle, TrenerRolle, ManagerRolle eller None)."""
        return self._naavaerende_rolle

    def sett_rolle(self, rolle) -> None:
        """Setter personens aktive rolle i en klubb."""
        self._naavaerende_rolle = rolle

    # ── OVR / ferdighet ───────────────────────────────────────────────────────

    def _beregn_ovr(self, posisjon: Posisjon) -> int:
        """
        Beregner Overall Rating for en gitt posisjon.
        OVR = Σ(vekt × verdi) / Σ(vekter)  →  alltid sammenlignbart på tvers av posisjoner.
        """
        vekter = _OVR_VEKTER.get(posisjon, _OVR_FALLBACK)
        teller = sum(vekt * getattr(self, attr) for attr, vekt in vekter.items())
        nevner = sum(vekter.values())
        return max(1, min(20, round(teller / nevner)))

    @property
    def ferdighet(self) -> int:
        """OVR basert på primær posisjon. Returnerer 10 hvis ingen posisjon er satt."""
        if self.primær_posisjon is None:
            return 10
        return self._beregn_ovr(self.primær_posisjon)

    def ferdighet_for_posisjon(self, posisjon: Posisjon) -> int:
        """OVR for en vilkårlig posisjon – nyttig for å vurdere omstilling."""
        return self._beregn_ovr(posisjon)

    # ── Tilgjengelighet ───────────────────────────────────────────────────────

    @property
    def er_tilgjengelig(self) -> bool:
        """Kan spilleren velges til kamp?"""
        return not self.skadet and self.kondisjon > 30.0

    @property
    def effektiv_ferdighet(self) -> int:
        """
        OVR justert for kondisjon og skade.
        Kondisjon under 70 % gir gradvis reduksjon.
        """
        base = self.ferdighet
        if self.kondisjon < 70.0:
            faktor = 0.7 + 0.3 * (self.kondisjon / 70.0)
            base   = max(1, round(base * faktor))
        return base

    # ── Kondisjon ────────────────────────────────────────────────────────────

    def _kondisjon_nedgang_rate(self) -> float:
        """
        Daglig nedgangsrate for sesongkondisjon.
        Høy arbeidsvilje og utholdenhet demper nedgangen.
        """
        basis = 2.0
        demping = (self.arbeidsvilje + self.utholdenhet) / 40.0  # 0.05–1.0
        return basis * (1.0 - demping * 0.6)

    def bruk_i_kamp(self, minutter: int = 90) -> None:
        """Reduserer in_game_kondisjon og sesongkondisjon etter kamp."""
        andel = minutter / 90.0
        ig_nedgang = 40.0 * andel * (1.0 - self.utholdenhet / 40.0)
        self.in_game_kondisjon = max(0.0, self.in_game_kondisjon - ig_nedgang)

        sesong_nedgang = self._kondisjon_nedgang_rate() * andel
        self.kondisjon = max(0.0, self.kondisjon - sesong_nedgang)

    def hvil_en_dag(self) -> None:
        """
        Simulerer én dags hvile:
        - Sesongkondisjon stiger litt (påvirket av arbeidsvilje)
        - In-game kondisjon nullstilles
        - Skadedager telles ned
        """
        if self.skadet:
            self.skade_dager_igjen -= 1
            if self.skade_dager_igjen <= 0:
                self._bli_frisk()
        else:
            gjenoppretting = 3.0 + self.arbeidsvilje * 0.3
            self.kondisjon = min(100.0, self.kondisjon + gjenoppretting)

        self.in_game_kondisjon = 100.0

    def _bli_frisk(self) -> None:
        self.skadet            = False
        self.skade_dager_igjen = 0
        self.skade_type        = SkadeType.INGEN

    # ── Skader ────────────────────────────────────────────────────────────────

    def _trekk_skadetype(self) -> SkadeType:
        """Trekker skadetype vektet etter SKADE_SANNSYNLIGHET."""
        kast  = random.random()
        kumul = 0.0
        for skade, prob in SKADE_SANNSYNLIGHET:
            kumul += prob
            if kast <= kumul:
                return skade
        return SkadeType.FORSTUING

    def paadra_skade(self, skade_type: Optional[SkadeType] = None) -> SkadeType:
        """
        Påfører spilleren en skade.
        Hvis skade_type er None trekkes typen tilfeldig.
        Fysikk og presstoleranse reduserer antall dager noe.

        Returnerer skadetypen som ble pådratt.
        """
        if skade_type is None:
            skade_type = self._trekk_skadetype()

        min_d, maks_d = SKADE_DAGER[skade_type]
        dager = random.randint(min_d, maks_d)

        # Fysikk og presstoleranse gir inntil 20 % raskere heling
        reduksjon = 1.0 - 0.10 * (self.fysikk / 20.0) - 0.10 * (self.presstoleranse / 20.0)
        dager = max(min_d, round(dager * reduksjon))

        self.skadet            = True
        self.skade_type        = skade_type
        self.skade_dager_igjen = dager
        return skade_type

    def skaderisiko(self) -> float:
        """
        Returnerer sannsynligheten (0.0–1.0) for at spilleren pådrar seg skade
        i én kamp. Lav kondisjon og lav fysikk øker risikoen.
        """
        basis     = 0.05
        kondis_f  = max(0.0, (70.0 - self.kondisjon) / 70.0) * 0.10
        fysikk_f  = (20 - self.fysikk) / 20.0 * 0.05
        return min(0.50, basis + kondis_f + fysikk_f)

    # ── Utvikling ─────────────────────────────────────────────────────────────

    def tren(self, attributt: str, mengde: int = 1) -> bool:
        """
        Forsøk å forbedre ett attributt med 'mengde'.
        Arbeidsvilje og potensial avgjør om forbedringen lykkes.
        Returnerer True hvis attributtet økte.
        """
        if attributt not in _FERDIGHET_ATTRS:
            raise ValueError(f"'{attributt}' er ikke et gyldig treningsattributt")

        nåværende = getattr(self, attributt)
        if nåværende >= self.potensial:
            return False   # Nådd sitt potensial på dette attributtet

        suksess_sjanse = (self.arbeidsvilje / 20.0) * (1.0 - nåværende / 20.0)
        if random.random() < suksess_sjanse:
            setattr(self, attributt, min(20, nåværende + mengde))
            return True
        return False

    def ald_en_sesong(self) -> None:
        """
        Simulerer aldring ved sesongstart.
        - Spillere over 30 kan miste litt i fysiske attributter.
        - Mentale attributter holder seg lenger.
        - Potensial kan falle litt hvert år over 28.
        """
        self.alder += 1

        if self.alder > 30:
            for attr in ("fart", "utholdenhet", "fysikk"):
                if random.random() < 0.4:
                    ny = max(1, getattr(self, attr) - 1)
                    setattr(self, attr, ny)

        if self.alder > 28 and self.potensial > 1:
            if random.random() < 0.3:
                self.potensial = max(1, self.potensial - 1)

    # ── Markedsverdi ──────────────────────────────────────────────────────────

    @property
    def markedsverdi_nok(self) -> int:
        """
        Markedsverdi i NOK.
        - Eksponentiell OVR-kurve (ferdighet^3) gjør toppspillere ekstremt dyre
        - Potensial-bonus for unge spillere under 23 med uutnyttet potensial
        - Kontraktsfaktor: siste kontraktsår gir kraftig rabatt (Bosman-effekt)
        - Alder: topper på 26, faller gradvis mot 0,2× ved 38
        """
        ovr = self.ferdighet

        import math
        # Eksponentiell baseverdi kalibrert til målverdier
        basis = int(16000 * math.exp(0.3912 * ovr))

        # Potensialkurve: under 23 og utap for sitt potensial
        potensial_f = 1.0
        if self.alder <= 22 and self.potensial > ovr:
            potensial_f = 1.0 + (self.potensial - ovr) * 0.15

        # Alderskurve: topper 25-27, faller raskt etter 32
        alder_f = max(0.15, 1.0 - abs(self.alder - 26) * 0.045)

        # Kontraktsfaktor — beregnet av okonomi-modulen, eksponert her
        kontrakt_f = 1.0
        if self.kontrakt is not None:
            aar_igjen = getattr(self.kontrakt, "aar_igjen_fra", lambda y: 2)(1995)
            if aar_igjen == 0:
                kontrakt_f = 0.20   # Bosman: gratis neste sommer
            elif aar_igjen == 1:
                kontrakt_f = 0.60

        return round(basis * potensial_f * alder_f * kontrakt_f)

    # ── Streng-representasjon ─────────────────────────────────────────────────

    def __repr__(self) -> str:
        pos = self.primær_posisjon.name if self.primær_posisjon else "—"
        return (
            f"<Person {self.kortnavn!r}  "
            f"alder={self.alder}  pos={pos}  "
            f"OVR={self.ferdighet}  "
            f"kond={self.kondisjon:.0f}%"
            f"{' [SKADET]' if self.skadet else ''}>"
        )

    def __str__(self) -> str:
        return self.fullt_navn

    # ── Serialisering (enkel dict for lagring) ────────────────────────────────

    def til_dict(self) -> dict:
        d: dict = {
            "id": self.id, "fornavn": self.fornavn, "etternavn": self.etternavn,
            "alder": self.alder,
            "kondisjon": self.kondisjon,
            "in_game_kondisjon": self.in_game_kondisjon,
            "skadet": self.skadet,
            "skade_dager_igjen": self.skade_dager_igjen,
            "skade_type": self.skade_type.name,
            "primær_posisjon":   self.primær_posisjon.name   if self.primær_posisjon   else None,
            "sekundær_posisjon": self.sekundær_posisjon.name if self.sekundær_posisjon else None,
            "roller": [r.name for r in self.roller],
        }
        for attr in _FERDIGHET_ATTRS + _META_ATTRS:
            d[attr] = getattr(self, attr)
        return d

    @classmethod
    def fra_dict(cls, data: dict) -> "Person":
        ferdigheter = {k: data[k] for k in _FERDIGHET_ATTRS + _META_ATTRS if k in data}
        p = cls(
            id=data["id"], fornavn=data["fornavn"], etternavn=data["etternavn"],
            alder=data["alder"], **ferdigheter,
        )
        p.kondisjon          = data.get("kondisjon", 100.0)
        p.in_game_kondisjon  = data.get("in_game_kondisjon", 100.0)
        p.skadet             = data.get("skadet", False)
        p.skade_dager_igjen  = data.get("skade_dager_igjen", 0)
        p.skade_type         = SkadeType[data.get("skade_type", "INGEN")]
        if data.get("primær_posisjon"):
            p.primær_posisjon   = Posisjon[data["primær_posisjon"]]
        if data.get("sekundær_posisjon"):
            p.sekundær_posisjon = Posisjon[data["sekundær_posisjon"]]
        p.roller = []
        return p


# ── Fabrikk-funksjon ──────────────────────────────────────────────────────────

def lag_spiller(
    id: str,
    posisjon: Posisjon,
    ovr_mål: int = 10,
    variasjon: int = 3,
    potensial: Optional[int] = None,
    alder: Optional[int] = None,
    fornavn: Optional[str] = None,
    etternavn: Optional[str] = None,
    **kwargs  # <-- NYTT: Fanger opp personlighetsverdier fra databasen
) -> Person:
    """
    Genererer en spiller med tilfeldige men realistiske attributter
    sentrert rundt ovr_mål ± variasjon, tilpasset posisjonen.

    Navn trekkes automatisk fra navn.py-bankene hvis ikke oppgitt.
    potensial: hvis None settes det til ovr_mål + 0–4 (unge spillere kan vokse)
    """
    # Navn — trekk fra bank hvis ikke eksplisitt gitt
    if fornavn is None or etternavn is None:
        from navn import trekk_navn
        trukket_f, trukket_e = trekk_navn()
        if fornavn is None:
            fornavn = trukket_f
        if etternavn is None:
            etternavn = trukket_e

    # Alder — realistisk fordeling rundt 24
    if alder is None:
        alder = max(17, min(36, int(random.gauss(24, 4))))

    vekter = _OVR_VEKTER.get(posisjon, _OVR_FALLBACK)

    attrs: dict[str, int] = {}
    for attr in _FERDIGHET_ATTRS:
        vekt   = vekter.get(attr, 0)
        senter = ovr_mål + (vekt - 2)        # viktige attributter trekkes opp
        verdi  = senter + random.randint(-variasjon, variasjon)
        attrs[attr] = max(1, min(20, verdi))

    if potensial is None:
        potensial = min(20, ovr_mål + random.randint(0, max(0, 28 - alder) // 3))

    p = Person(
        id=id, fornavn=fornavn, etternavn=etternavn, alder=alder,
        potensial=potensial,
        rykte=max(1, min(20, ovr_mål + random.randint(-4, 2))),
        **attrs,
        **kwargs  # <-- NYTT: Sender personlighet videre til Person-klassen
    )
    p.primær_posisjon = posisjon
    return p
