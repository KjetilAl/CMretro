import random
import csv
import math
from dataclasses import dataclass, field
from typing import Optional
from klubb import Klubb

# =============================================================================
# LAND → LIGA-MAPPING
# Brukes til å gruppere utenlandske lag i sine respektive ligaer
# =============================================================================
LAND_TIL_LIGA = {
    "England":          "Premier League",
    "Spain":            "La Liga",
    "Germany":          "Bundesliga",
    "Italy":            "Serie A",
    "France":           "Ligue 1",
    "Netherlands":      "Eredivisie",
    "Portugal":         "Primeira Liga",
    "Belgium":          "Pro League",
    "Scotland":         "Premiership",
    "Austria":          "Bundesliga (AUT)",
    "Turkey":           "Süper Lig",
    "Switzerland":      "Super League (SUI)",
    "Denmark":          "Superligaen",
    "Sweden":           "Allsvenskan",
    "Croatia":          "HNL",
    "Czech Republic":   "Fortuna Liga",
    "Serbia":           "SuperLiga",
    "Greece":           "Super League",
    "Hungary":          "OTP Bank Liga",
    "Poland":           "Ekstraklasa",
    "Romania":          "SuperLiga (ROU)",
    "Ukraine":          "Premier League (UKR)",
    "Russia":           "Premier League (RUS)",
    "Israel":           "Premier League (ISR)",
    "Azerbaijan":       "Premier League (AZE)",
    "Kazakhstan":       "Premier League (KAZ)",
    "Bulgaria":         "First League (BUL)",
    "Slovakia":         "Fortuna Liga (SVK)",
    "Slovenia":         "PrvaLiga",
    "Iceland":          "Úrvalsdeild",
    "Finland":          "Veikkausliiga",
    "Latvia":           "Virsliga",
    "Lithuania":        "A Lyga",
    "Estonia":          "Meistriliiga",
    "Armenia":          "Armenian Premier League",
    "Georgia":          "Erovnuli Liga",
    "Moldova":          "Divizia Naţională",
    "Belarus":          "Vysheyshaya Liga",
    "Albania":          "Kategoria Superiore",
    "Kosovo":           "Football Superleague",
    "North Macedonia":  "First Football League",
    "Montenegro":       "First League (MNE)",
    "Bosnia-Herzeg.":   "Premier League (BIH)",
    "Luxembourg":       "BGL Ligue",
    "Malta":            "Premier League (MLT)",
    "Cyprus":           "First Division (CYP)",
    "Faroe Islands":    "Faroese Premier League",
    "Northern Ireland": "NIFL Premiership",
    "Ireland":          "League of Ireland",
    "Wales":            "Cymru Premier",
    "Gibraltar":        "Gibraltar Premier Division",
    "Andorra":          "Primera Divisió",
    "San Marino":       "Campionato Sammarinese",
    "Liechtenstein":    "FL1 (LIE)",
    "Norway":           "Eliteserien",  # LOD=1, håndteres separat
}

# Landene vi aktivt simulerer europaligaer for
AKTIVE_LIGALAND = {
    "England", "Spain", "Germany", "Italy", "France",
    "Netherlands", "Portugal", "Belgium", "Scotland",
    "Austria", "Turkey", "Switzerland", "Denmark", "Sweden",
    "Croatia", "Czech Republic", "Serbia", "Greece",
}


# =============================================================================
# LOD 0 — UTENLANDSK KLUBB
# =============================================================================
@dataclass
class UtenlandskKlubb:
    """
    Representerer et utenlandsk lag i Europa-systemet (LOD = 0).
    Simuleres matematisk — ingen individuelle spillerattributter.
    """
    navn: str
    land: str
    uefa_koeffisient: float        # Historisk total fra UEFA-listen
    styrke: int = 10               # 1–20, beregnet fra koeffisient
    lod: int = 0

    # Brukes til roterende ligaplassering
    liga_plassering: Optional[int] = None
    i_europa: bool = False
    turnering: Optional[str] = None   # "CL", "EL", "ECL" eller None

    def __post_init__(self):
        self.styrke = self._beregn_styrke()

    def _beregn_styrke(self) -> int:
        """
        Konverterer UEFA-koeffisient til styrke på 1–20-skala.
        Topp (139 poeng = Real Madrid) → 20. Bunn (1 poeng) → 1.
        """
        MAKS_KOEFF = 139.0
        styrke = math.ceil((self.uefa_koeffisient / MAKS_KOEFF) * 20)
        return max(1, min(20, styrke))

    @property
    def liga(self) -> str:
        return LAND_TIL_LIGA.get(self.land, "Ukjent liga")

    def generer_kampstall(self) -> dict:
        """
        Genererer et midlertidig detaljert bilde av laget for én Europa-kamp.
        Brukes av kampsimulatoren når et norsk lag møter dette laget (LOD 1-kamp).
        """
        return {
            "navn":           self.navn,
            "styrke":         self.styrke,
            "angrepsstyrke":  max(1, self.styrke + random.randint(-2, 2)),
            "forsvarsstyrke": max(1, self.styrke + random.randint(-2, 2)),
            "form":           random.randint(1, 20),
            "hjemmebane":     random.randint(8, 14),
        }

    def __repr__(self):
        return (
            f"<UtenlandskKlubb: {self.navn} ({self.land}), "
            f"styrke: {self.styrke}/20, "
            f"koeff: {self.uefa_koeffisient}>"
        )


# =============================================================================
# LOD 0 — LIGA
# Simulerer én utenlandsk liga med roterende sluttplasseringer
# =============================================================================
class UtenlandskLiga:
    """
    En utenlandsk liga med fast sett av lag.
    Etter hver sesong roteres plasseringene vektet etter styrke,
    noe som bestemmer hvilke lag som kvalifiserer seg til Europa.
    """

    def __init__(self, navn: str, land: str, lag: list[UtenlandskKlubb]):
        self.navn = navn
        self.land = land
        self.lag = sorted(lag, key=lambda l: l.uefa_koeffisient, reverse=True)
        self.siste_tabell: list[UtenlandskKlubb] = []

    def simuler_sesong(self):
        """
        Trekker en vektet tilfeldig sluttabell.
        Sterkere lag har høyere sannsynlighet for toppplassering,
        men overraskelser kan skje.
        """
        vekter = [l.styrke ** 1.5 for l in self.lag]
        total = sum(vekter)
        sannsynligheter = [v / total for v in vekter]

        # Trekker uten tilbakelegging — simulerer sluttabell
        resterende = list(range(len(self.lag)))
        tabell = []
        gjenvaerende_prob = list(sannsynligheter)

        for _ in range(len(self.lag)):
            total_p = sum(gjenvaerende_prob[i] for i in resterende)
            r = random.random() * total_p
            kumulativ = 0
            valgt = resterende[0]
            for i in resterende:
                kumulativ += gjenvaerende_prob[i]
                if r <= kumulativ:
                    valgt = i
                    break
            tabell.append(self.lag[valgt])
            resterende.remove(valgt)

        self.siste_tabell = tabell
        for i, lag in enumerate(tabell):
            lag.liga_plassering = i + 1

    def hent_europa_kandidater(self) -> dict:
        """
        Returnerer hvilke lag som kvalifiserer seg til Europa basert på plassering.
        Forutsetter at simuler_sesong() er kjørt.
        """
        if not self.siste_tabell:
            return {}
        return {
            "CL":  self.siste_tabell[0] if len(self.siste_tabell) > 0 else None,
            "EL":  self.siste_tabell[1] if len(self.siste_tabell) > 1 else None,
            "ECL": self.siste_tabell[2] if len(self.siste_tabell) > 2 else None,
        }

    def __repr__(self):
        return f"<UtenlandskLiga: {self.navn}, {len(self.lag)} lag>"


# =============================================================================
# KAMPRESULTAT (EUROPA)
# =============================================================================
@dataclass
class EuropaKamp:
    """En kamp i europacupene — støtter LOD 0 og LOD 1."""
    hjemme: object    # Klubb (LOD 1) eller UtenlandskKlubb (LOD 0)
    borte: object
    runde: str
    hjemme_maal: Optional[int] = None
    borte_maal: Optional[int] = None
    spilt: bool = False

    def registrer_resultat(self, hjemme_maal: int, borte_maal: int):
        self.hjemme_maal = hjemme_maal
        self.borte_maal = borte_maal
        self.spilt = True

    @property
    def inneholder_norsk_lag(self) -> bool:
        """Brukes av kampsimulatoren til å velge LOD 1 vs LOD 0-simulering."""
        from klubb import Klubb
        return isinstance(self.hjemme, Klubb) or isinstance(self.borte, Klubb)

    def simuler_lod0(self):
        """
        Enkel matematisk simulering for kamper uten norske lag.
        Styrkeforskjell gir sannsynlighetsfordeling.
        """
        hjemme_styrke = (
            self.hjemme.styrke if hasattr(self.hjemme, 'styrke') else 10
        )
        borte_styrke = (
            self.borte.styrke if hasattr(self.borte, 'styrke') else 10
        )

        # Hjemmebanefordel: +1.5 styrkepoeng
        hjemme_forventning = (hjemme_styrke + 1.5) / 20 * 3
        borte_forventning = borte_styrke / 20 * 2.5

        hjemme_maal = max(0, round(random.gauss(hjemme_forventning, 1.0)))
        borte_maal  = max(0, round(random.gauss(borte_forventning, 1.0)))
        self.registrer_resultat(hjemme_maal, borte_maal)

    @property
    def vinner(self) -> Optional[object]:
        if not self.spilt:
            return None
        if self.hjemme_maal > self.borte_maal:
            return self.hjemme
        elif self.borte_maal > self.hjemme_maal:
            return self.borte
        return None

    def __repr__(self):
        h = self.hjemme.navn if hasattr(self.hjemme, 'navn') else str(self.hjemme)
        b = self.borte.navn  if hasattr(self.borte,  'navn') else str(self.borte)
        if self.spilt:
            return f"<EuropaKamp: {h} {self.hjemme_maal}–{self.borte_maal} {b}>"
        return f"<EuropaKamp: {h} vs {b} [{self.runde}]>"


# =============================================================================
# TURNERING
# Håndterer CL, EL og ECL med korrekte formater
# =============================================================================
class EuropaTurnering:
    """
    Én europacupturnering (CL, EL eller ECL).

    Format:
        CL/EL:  36 lag, 8 seriekamper (4H/4B), topp 8 → 8-delsfinale,
                9–24 → 16-delsfinale, 25–36 ute
        ECL:    36 lag, 6 seriekamper (3H/3B), samme sluttspillformat
    """

    FORMATER = {
        "CL":  {"seriekamper": 8, "premiepenger": 150_000_000, "prestisje": 1},
        "EL":  {"seriekamper": 8, "premiepenger":  40_000_000, "prestisje": 2},
        "ECL": {"seriekamper": 6, "premiepenger":  30_000_000, "prestisje": 3},
    }

    def __init__(self, kode: str, sesong: int):
        if kode not in self.FORMATER:
            raise ValueError(f"Ukjent turneringskode: {kode}")
        fmt = self.FORMATER[kode]
        self.kode = kode
        self.navn = {"CL": "Champions League", "EL": "Europa League",
                     "ECL": "Conference League"}[kode]
        self.sesong = sesong
        self.seriekamper = fmt["seriekamper"]
        self.premiepenger = fmt["premiepenger"]
        self.prestisje = fmt["prestisje"]

        self.deltakere: list = []             # Maks 36 lag (Klubb eller UtenlandskKlubb)
        self.serie_tabell: list[dict] = []    # [{"lag": ..., "poeng": 0, "maal_for": 0, ...}]
        self.kamper: list[EuropaKamp] = []
        self.fase: str = "Ikke startet"       # "Seriespill", "16-delsfinale", "8-delsfinale" ...

    def legg_til_deltaker(self, lag):
        if len(self.deltakere) >= 36:
            print(f"[{self.navn}] Allerede 36 deltakere — kan ikke legge til {lag.navn}.")
            return
        if lag not in self.deltakere:
            self.deltakere.append(lag)
            self.serie_tabell.append({
                "lag":      lag,
                "poeng":    0,
                "vunnet":   0,
                "uavgjort": 0,
                "tapt":     0,
                "maal_for": 0,
                "maal_mot": 0,
            })

    def _hent_tabellrad(self, lag) -> Optional[dict]:
        for rad in self.serie_tabell:
            if rad["lag"] is lag:
                return rad
        return None

    def _oppdater_tabell(self, kamp: EuropaKamp):
        if not kamp.spilt:
            return
        h = self._hent_tabellrad(kamp.hjemme)
        b = self._hent_tabellrad(kamp.borte)
        if h:
            h["maal_for"] += kamp.hjemme_maal
            h["maal_mot"] += kamp.borte_maal
            if kamp.hjemme_maal > kamp.borte_maal:
                h["vunnet"] += 1;  h["poeng"] += 3
            elif kamp.hjemme_maal == kamp.borte_maal:
                h["uavgjort"] += 1; h["poeng"] += 1
            else:
                h["tapt"] += 1
        if b:
            b["maal_for"] += kamp.borte_maal
            b["maal_mot"] += kamp.hjemme_maal
            if kamp.borte_maal > kamp.hjemme_maal:
                b["vunnet"] += 1;  b["poeng"] += 3
            elif kamp.hjemme_maal == kamp.borte_maal:
                b["uavgjort"] += 1; b["poeng"] += 1
            else:
                b["tapt"] += 1

    def sorter_tabell(self):
        self.serie_tabell.sort(
            key=lambda r: (
                r["poeng"],
                r["maal_for"] - r["maal_mot"],
                r["maal_for"]
            ),
            reverse=True
        )

    def generer_seriespill(self):
        """
        Trekker motstandere for seriespillet basert på seeding (styrke).
        Hvert lag spiller self.seriekamper kamper (halvparten hjemme, halvparten borte).
        """
        self.fase = "Seriespill"
        self.kamper = []
        n = len(self.deltakere)

        # Del inn i 4 seedinggrupper
        sorterte = sorted(
            self.deltakere,
            key=lambda l: l.styrke if hasattr(l, 'styrke') else 10,
            reverse=True
        )
        gruppe_storrelse = max(1, n // 4)
        grupper = [
            sorterte[i * gruppe_storrelse:(i + 1) * gruppe_storrelse]
            for i in range(4)
        ]

        # Hvert lag trekker 2 motstandere fra hver seedinggruppe
        for lag in self.deltakere:
            hjemme_kamper = 0
            borte_kamper = 0
            for gruppe in grupper:
                kandidater = [m for m in gruppe if m is not lag]
                random.shuffle(kandidater)
                valgte = kandidater[:2]
                for motstander in valgte:
                    if hjemme_kamper < self.seriekamper // 2:
                        self.kamper.append(EuropaKamp(lag, motstander, "Seriespill"))
                        hjemme_kamper += 1
                    else:
                        self.kamper.append(EuropaKamp(motstander, lag, "Seriespill"))
                        borte_kamper += 1

    def simuler_seriespill(self):
        """Simulerer alle seriespillkamper. Norske kamper markeres — simuleres av kampmotor."""
        for kamp in self.kamper:
            if kamp.fase if hasattr(kamp, 'fase') else False:
                continue
            if not kamp.inneholder_norsk_lag:
                kamp.simuler_lod0()
                self._oppdater_tabell(kamp)
            # Norske kamper returneres til spillmotoren for LOD 1-simulering

        self.sorter_tabell()
        print(f"\n[{self.navn} {self.sesong}] Seriespill ferdig.")
        self._print_mini_tabell()

    def hent_norske_kamper(self) -> list[EuropaKamp]:
        """Returnerer alle kamper som involverer norske lag — for LOD 1-simulering."""
        return [k for k in self.kamper if k.inneholder_norsk_lag and not k.spilt]

    def generer_sluttspill(self) -> dict:
        """
        Genererer 16-delsfinaler og plasserer lag 1–8 i direkteplass til 8-delsfinale.
        Returnerer en dict med kampene som skal spilles.
        """
        self.sorter_tabell()
        lag_etter_plassering = [rad["lag"] for rad in self.serie_tabell]

        direkte_til_8del = lag_etter_plassering[:8]
        til_16del_seedet = lag_etter_plassering[8:16]
        til_16del_useedet = lag_etter_plassering[16:24]
        ute = lag_etter_plassering[24:]

        print(f"\n[{self.navn}] {len(ute)} lag er ute etter seriespillet.")

        # Trekk 16-delsfinaler: seedet (9–16) vs useedet (17–24)
        random.shuffle(til_16del_useedet)
        sekstendelsfinaler = [
            EuropaKamp(til_16del_seedet[i], til_16del_useedet[i], "16-delsfinale")
            for i in range(min(len(til_16del_seedet), len(til_16del_useedet)))
        ]

        self.fase = "16-delsfinale"
        return {
            "direkte_til_8del":    direkte_til_8del,
            "sekstendelsfinaler":  sekstendelsfinaler,
            "ute":                 ute,
        }

    def _print_mini_tabell(self, antall: int = 10):
        print(f"  {'Lag':<30} {'P':>4} {'MF':>4} {'MM':>4} {'MD':>4}")
        print(f"  {'-'*50}")
        for i, rad in enumerate(self.serie_tabell[:antall], 1):
            navn = rad['lag'].navn if hasattr(rad['lag'], 'navn') else "?"
            md = rad['maal_for'] - rad['maal_mot']
            print(
                f"  {i:>2}. {navn:<28} "
                f"{rad['poeng']:>4} "
                f"{rad['maal_for']:>4} "
                f"{rad['maal_mot']:>4} "
                f"{md:>+4}"
            )

    def __repr__(self):
        return (
            f"<EuropaTurnering: {self.navn} {self.sesong}, "
            f"{len(self.deltakere)} deltakere, fase: {self.fase}>"
        )


# =============================================================================
# EUROPA-SYSTEMET — HOVEDMOTOR
# =============================================================================
class EuropaSystem:
    """
    Koordinerer alle europacupturneringer og utenlandske ligaer.

    Norsk sesong:  vår/høst (f.eks. 2026)
    Europa-sesong: høst/vår (f.eks. 2026/27)
    → Norske lag som kvalifiserer seg i desember 2026
      går inn i europeiske turneringer fra juli 2027.
    """

    def __init__(self, alle_utenlandske: list[UtenlandskKlubb]):
        self.alle_utenlandske = alle_utenlandske
        self.ligaer: dict[str, UtenlandskLiga] = self._bygg_ligaer()

        # Turneringer opprettes per sesong av fordel_plasser()
        self.aktive_turneringer: dict[str, EuropaTurnering] = {}

        # Norske billetter venter til neste europa-sesong
        self.norske_billetter: dict[int, dict] = {}   # sesong_aar → plasser

    def _bygg_ligaer(self) -> dict[str, UtenlandskLiga]:
        """Grupperer utenlandske lag i ligaer basert på land."""
        liga_dict: dict[str, list] = {}
        for lag in self.alle_utenlandske:
            liga_navn = lag.liga
            if liga_navn not in liga_dict:
                liga_dict[liga_navn] = []
            liga_dict[liga_navn].append(lag)

        return {
            navn: UtenlandskLiga(navn, lag[0].land if lag else "?", lag)
            for navn, lag in liga_dict.items()
        }

    def simuler_alle_ligaer(self):
        """Kjøres én gang per år — simulerer alle utenlandske ligasesonger."""
        print("\n=== Simulerer utenlandske ligaer (LOD 0) ===")
        for liga in self.ligaer.values():
            if liga.land in AKTIVE_LIGALAND:
                liga.simuler_sesong()
        print(f"  {len(self.ligaer)} ligaer simulert.")

    def fordel_norske_europaplasser(
        self,
        norsk_sesong_aar: int,
        seriemester: Klubb,
        serietoer: Klubb,
        serietreer: Klubb,
        seriefirer: Klubb,
        cupvinner: Klubb,
    ):
        """
        Kalles av LigaSystem etter at norsk sesong + cup er ferdig.
        Billettene aktiveres i europa-sesongen NESTE år.
        """
        europa_aar = norsk_sesong_aar + 1
        print(f"\n*** Norske Europa-billetter for sesongen {europa_aar}/{europa_aar+1} ***")

        cl_lag = [seriemester, serietoer]
        el_lag = []
        ecl_lag = []

        # Cupvinner: hvis allerede i CL, gis EL-plassen til serietreer
        if cupvinner not in cl_lag:
            el_lag.append(cupvinner)
        else:
            el_lag.append(serietreer)
            print(f"  NB: {cupvinner.kortnavn} har CL-plass — {serietreer.kortnavn} får EL-plassen.")

        # Conference League: serietreer + seriefirer (juster hvis noen allerede er plassert)
        for lag in [serietreer, seriefirer]:
            if lag not in cl_lag and lag not in el_lag:
                ecl_lag.append(lag)

        self.norske_billetter[europa_aar] = {
            "CL":  cl_lag,
            "EL":  el_lag,
            "ECL": ecl_lag,
        }

        for turnering, lag in self.norske_billetter[europa_aar].items():
            for l in lag:
                print(f"  → {l.kortnavn} ({l.navn}): {turnering}-kvalik")

    def opprett_sesongens_turneringer(self, europa_aar: int):
        """
        Oppretter CL, EL og ECL for gitt år og fyller dem med deltakere.
        Norske lag fra billetter + europeiske lag fra ligasimulering.
        """
        self.aktive_turneringer = {
            "CL":  EuropaTurnering("CL",  europa_aar),
            "EL":  EuropaTurnering("EL",  europa_aar),
            "ECL": EuropaTurnering("ECL", europa_aar),
        }

        # Legg til norske lag
        billetter = self.norske_billetter.get(europa_aar, {})
        for kode, lag_liste in billetter.items():
            for lag in lag_liste:
                self.aktive_turneringer[kode].legg_til_deltaker(lag)

        # Fyll opp med utenlandske lag fra ligasimulering
        self._fyll_med_utenlandske()
        print(f"\n[Europa {europa_aar}] Turneringer opprettet:")
        for t in self.aktive_turneringer.values():
            print(f"  {t}")

    def _fyll_med_utenlandske(self):
        """
        Henter topp-lag fra alle aktive ligaer og fordeler til CL, EL og ECL
        til hver turnering har 36 deltakere.
        """
        kandidater: dict[str, list[UtenlandskKlubb]] = {"CL": [], "EL": [], "ECL": []}

        for liga in self.ligaer.values():
            if not liga.siste_tabell:
                continue
            europa = liga.hent_europa_kandidater()
            if europa.get("CL"):
                kandidater["CL"].append(europa["CL"])
            if europa.get("EL"):
                kandidater["EL"].append(europa["EL"])
            if europa.get("ECL"):
                kandidater["ECL"].append(europa["ECL"])

        # Sorter etter styrke og fyll opp til 36
        for kode, turnering in self.aktive_turneringer.items():
            sorterte = sorted(
                kandidater.get(kode, []),
                key=lambda l: l.styrke,
                reverse=True
            )
            for lag in sorterte:
                if len(turnering.deltakere) >= 36:
                    break
                turnering.legg_til_deltaker(lag)

    def hent_norske_europakamper(self) -> list[EuropaKamp]:
        """Samler alle uavgjorte europakamper med norske lag — for LOD 1-simulering."""
        alle = []
        for t in self.aktive_turneringer.values():
            alle.extend(t.hent_norske_kamper())
        return alle

    def __repr__(self):
        aktive = len(self.aktive_turneringer)
        return (
            f"<EuropaSystem: {len(self.alle_utenlandske)} utenlandske lag, "
            f"{len(self.ligaer)} ligaer, "
            f"{aktive} aktive turneringer>"
        )


# =============================================================================
# FABRIKKFUNKSJON — last inn fra UEFA-koeffisient-CSV
# =============================================================================
def last_inn_utenlandske_lag(csv_fil: str) -> list[UtenlandskKlubb]:
    """
    Leser UEFA-koeffisientlisten og returnerer en liste med UtenlandskKlubb-objekter.
    Norske lag hoppes over (håndteres som LOD 1 av ligasystemet).
    """
    lag = []
    with open(csv_fil, encoding="utf-8-sig") as f:
        leser = csv.DictReader(f)
        for rad in leser:
            land = rad["Country"].strip()
            if land == "Norway":
                continue   # LOD 1 — håndteres av liga.py
            try:
                koeff = float(rad["Total"].replace(",", "."))
            except (ValueError, KeyError):
                continue
            lag.append(UtenlandskKlubb(
                navn=rad["Club"].strip(),
                land=land,
                uefa_koeffisient=koeff,
            ))
    print(f"[EuropaSystem] Lastet inn {len(lag)} utenlandske lag fra {csv_fil}.")
    return lag


def opprett_europasystem(csv_fil: str) -> EuropaSystem:
    """Fabrikkfunksjon — oppretter et komplett EuropaSystem fra CSV-filen."""
    utenlandske = last_inn_utenlandske_lag(csv_fil)
    return EuropaSystem(utenlandske)
