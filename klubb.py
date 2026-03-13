"""
klubb.py  –  Norsk Football Manager '95
Klubb, stadion og alt personell.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
import random

from person import (
    Person, SpillerRolle, TrenerRolle, ManagerRolle,
    SKALA_MIN, SKALA_MAX,
)

if TYPE_CHECKING:
    from okonomi import Kontrakt   # bare for type-hints, unngår sirkulær import


# =============================================================================
# STADION
# =============================================================================

class Stadion:
    """
    Representerer klubbens hjemmebane.
    Standard påvirker hjemmebanefordel og billettinntekter.
    """

    STANDARD_NIVAA: dict[int, str] = {
        1: "Forfallent",
        2: "Enkelt",
        3: "Greit",
        4: "Moderne",
        5: "Imponerende",
    }

    def __init__(
        self,
        navn: str,
        kapasitet: int,
        standard: int,        # 1–5
        byggeaar: int,
    ) -> None:
        if not 1 <= standard <= 5:
            raise ValueError(f"Stadionstandard må være 1–5, fikk {standard}")

        self.navn      = navn
        self.kapasitet = kapasitet
        self.standard  = standard
        self.byggeaar  = byggeaar

    # ── Avledede verdier ──────────────────────────────────────────────────────

    @property
    def standard_tekst(self) -> str:
        return self.STANDARD_NIVAA.get(self.standard, "Ukjent")

    @property
    def hjemmebane_fordel(self) -> int:
        """Fordelsverdi 1–10 brukt av kampsimulatoren."""
        return round((self.standard / 5) * 10)

    @property
    def ukentlig_vedlikehold(self) -> int:
        """Kostnad øker med kapasitet og alder på anlegget."""
        alder_f = max(1, (1995 - self.byggeaar) // 10)
        return int((self.kapasitet / 1000) * alder_f * 500)

    # ── Handlinger ───────────────────────────────────────────────────────────

    def oppgrader(self) -> bool:
        """Forbedrer standarden ett nivå. Returnerer True hvis vellykket."""
        if self.standard < 5:
            self.standard += 1
            return True
        return False

    def __repr__(self) -> str:
        return (
            f"<Stadion {self.navn!r}  "
            f"kap={self.kapasitet:,}  "
            f"std={self.standard_tekst}>"
        )


# =============================================================================
# KLUBB
# =============================================================================

class Klubb:
    """
    Representerer en fotballklubb med identitet, økonomi, personell og kultur.

    Skjulte attributter (prefiks _) er ikke synlige for manageren direkte,
    men lekker ut gjennom hendelser, pressekonferanser og budsjettrapporter.
    """

    def __init__(
        self,
        id: str,
        navn: str,
        kortnavn: str,
        grunnlagt_aar: int,
        farger: list[str],
        stadion: Stadion,
        divisjon: str,
        # Økonomi
        saldo: int,
        ukentlig_loennsbudsjett: int,
        gjeld: int,
        # Kultur (1–20)
        supporterbase: int,
        ambisjonsnivaa: int,
        historisk_suksess: int,
        # Skjulte attributter (1–20)
        intern_uro: int,
        okonomi_problem: int,
        # Valgfri
        har_rik_eier: bool = False,
    ) -> None:
        # Identitet
        self.id            = id
        self.navn          = navn
        self.kortnavn      = kortnavn
        self.grunnlagt_aar = grunnlagt_aar
        self.farger        = farger
        self.stadion       = stadion
        self.divisjon      = divisjon
        self.rivaler:      list[str] = []

        # Økonomi
        self.saldo                   = saldo
        self.ukentlig_loennsbudsjett = ukentlig_loennsbudsjett
        self.gjeld                   = gjeld
        self.har_rik_eier            = har_rik_eier
        self.hovedsponsor: Optional[str] = None

        # Kultur
        self.supporterbase     = supporterbase
        self.ambisjonsnivaa    = ambisjonsnivaa
        self.historisk_suksess = historisk_suksess

        # Skjulte attributter
        self._intern_uro      = intern_uro
        self._okonomi_problem = okonomi_problem

        # Statistikk
        self.cup_deltakelser: int = 0

        # Personell — én enkelt kilde til sannhet
        self._alt_personell: list[Person] = []

    # =========================================================================
    # PERSONELL — properties filtrerer _alt_personell i sanntid
    # =========================================================================

    @property
    def spillerstall(self) -> list[Person]:
        return [
            p for p in self._alt_personell
            if isinstance(p.hent_naavaerende_rolle(), SpillerRolle)
        ]

    @property
    def trenerstab(self) -> list[Person]:
        return [
            p for p in self._alt_personell
            if isinstance(p.hent_naavaerende_rolle(), TrenerRolle)
        ]

    @property
    def naavaerende_manager(self) -> Optional[Person]:
        for p in self._alt_personell:
            if isinstance(p.hent_naavaerende_rolle(), ManagerRolle):
                return p
        return None

    def legg_til_person(self, person: Person, rolle=None) -> None:
        """
        Legger personen til klubben og setter rollen.
        rolle: SpillerRolle(), TrenerRolle(), ManagerRolle() eller None
        """
        if person not in self._alt_personell:
            self._alt_personell.append(person)
        if rolle is not None:
            person.sett_rolle(rolle)

    def fjern_person(self, person: Person) -> None:
        """Fjerner personen og nullstiller rollen deres."""
        self._alt_personell = [p for p in self._alt_personell if p.id != person.id]
        person.sett_rolle(None)
        person.kontrakt = None

    def finn_person(self, person_id: str) -> Optional[Person]:
        for p in self._alt_personell:
            if p.id == person_id:
                return p
        return None

    def legg_til_rival(self, klubb_id: str) -> None:
        if klubb_id not in self.rivaler:
            self.rivaler.append(klubb_id)

    # =========================================================================
    # ØKONOMI
    # =========================================================================

    @property
    def er_i_okonomisk_krise(self) -> bool:
        """Synlig signal til manageren — men ikke årsaken."""
        return self.saldo < 0 or self.gjeld > abs(self.saldo) * 2

    @property
    def total_ukentlig_loennskostnad(self) -> int:
        """Faktisk lønnskostnad basert på kontraktene i stallen."""
        total = 0
        for p in self.spillerstall:
            if p.kontrakt is not None:
                total += getattr(p.kontrakt, "ukelonn", 0)
        return total

    def betal_ukentlige_utgifter(self) -> dict:
        """
        Kalles av kalenderen én gang per uke (mandag).
        Returnerer en kvittering med beløp for hvert utgiftspost.
        """
        lonn        = self.total_ukentlig_loennskostnad
        vedlikehold = self.stadion.ukentlig_vedlikehold if self.stadion else 0

        # Skjult svinn ved alvorlige økonomiske problemer
        skjult_trekk = 0
        if self._okonomi_problem > 15:
            skjult_trekk = int(abs(self.saldo) * 0.03)
            self.gjeld  += skjult_trekk

        totalt = lonn + vedlikehold + skjult_trekk
        self.saldo -= totalt
        self.ukentlig_loennsbudsjett = lonn   # Synkroniser synlig budsjettlinje

        return {
            "lonn":         lonn,
            "vedlikehold":  vedlikehold,
            "skjult_trekk": skjult_trekk,
            "totalt":       totalt,
        }

    def motta_aarlig_sponsor(self) -> int:
        """
        Kalles ved sesongstart.
        Høyere divisjon og historisk suksess gir mer i sponsorinntekter.
        """
        basis = {
            "Eliteserien":       15_000_000,
            "OBOS-ligaen":        4_000_000,
            "PostNord-ligaen":      500_000,
        }.get(self.divisjon, 100_000)

        multiplikator = 1.0 + (self.historisk_suksess / 20.0)
        sponsor_sum   = int(basis * multiplikator)
        self.saldo   += sponsor_sum
        return sponsor_sum

    def beregn_billettinntekter(
        self,
        motstander_rykte: int,
        billettpris: int = 150,
    ) -> tuple[int, int]:
        """
        Kalles av kampmotoren ved hjemmekamp.
        Returnerer (faktiske_tilskuere, inntekt_nok).
        """
        if not self.stadion:
            return 0, 0

        base = (self.supporterbase / 20.0) * self.stadion.kapasitet
        motstander_trekk = (motstander_rykte / 20.0) * 2_000
        tilskuere = int(
            base + motstander_trekk + random.randint(-500, 1_500)
        )
        tilskuere = max(0, min(self.stadion.kapasitet, tilskuere))

        inntekt    = tilskuere * billettpris
        self.saldo += inntekt
        return tilskuere, inntekt

    def sjekk_rik_eier(self) -> Optional[str]:
        """
        Sjekkes månedlig eller når saldo er kritisk lav.
        Returnerer en nyhetsstreng hvis eieren griper inn, ellers None.
        """
        if self.har_rik_eier and self.saldo < 0:
            if random.random() < 0.20:
                pakke     = abs(self.saldo) + random.randint(2_000_000, 10_000_000)
                self.saldo += pakke
                return (
                    f"INVESTORINNGREP: {self.navn} mottar "
                    f"{pakke:,.0f} kr fra eier!"
                )
        return None

    # =========================================================================
    # HENDELSER — attributtdrift basert på sportslige resultater
    # =========================================================================

    def opplev_hendelse(self, hendelse_type: str) -> None:
        """
        Kalles av spillmotoren når viktige ting skjer.
        Påvirker kultur og skjult dynamikk over tid.
        """
        meldinger = {
            "nedrykk": (
                lambda: [
                    setattr(self, "supporterbase",
                            max(SKALA_MIN, self.supporterbase - 3)),
                    setattr(self, "_intern_uro",
                            min(SKALA_MAX, self._intern_uro + 2)),
                ],
                f"[{self.navn}] Rykker ned. Supporterbasen rystes.",
            ),
            "opprykk": (
                lambda: [
                    setattr(self, "supporterbase",
                            min(SKALA_MAX, self.supporterbase + 2)),
                    setattr(self, "_intern_uro",
                            max(SKALA_MIN, self._intern_uro - 1)),
                ],
                f"[{self.navn}] Opprykk! Euforisk stemning.",
            ),
            "seriemester": (
                lambda: [
                    setattr(self, "supporterbase",
                            min(SKALA_MAX, self.supporterbase + 2)),
                    setattr(self, "historisk_suksess",
                            min(SKALA_MAX, self.historisk_suksess + 1)),
                ],
                f"[{self.navn}] Seriemester! Legendarisk sesong.",
            ),
            "manager_sparket": (
                lambda: [
                    setattr(self, "_intern_uro",
                            min(SKALA_MAX, self._intern_uro + 3)),
                ],
                f"[{self.navn}] Manager sparket. Uro i garderoben.",
            ),
        }

        if hendelse_type in meldinger:
            effekt_fn, melding = meldinger[hendelse_type]
            effekt_fn()
            print(melding)

        # Klampe alle skala-verdier
        for attr in ("supporterbase", "historisk_suksess", "_intern_uro", "_okonomi_problem"):
            setattr(self, attr, max(SKALA_MIN, min(SKALA_MAX, getattr(self, attr))))

    # =========================================================================
    # REPRESENTASJON
    # =========================================================================

    def __repr__(self) -> str:
        manager = self.naavaerende_manager
        mgr_txt = f"{manager.fullt_navn}" if manager else "Ledig"
        return (
            f"<Klubb {self.navn!r} ({self.kortnavn})  "
            f"{self.divisjon}  "
            f"manager={mgr_txt}  "
            f"saldo={self.saldo:,.0f} kr>"
        )

    def __str__(self) -> str:
        return self.navn
