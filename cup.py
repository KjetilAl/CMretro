import random
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum, auto

# =============================================================================
# REGIONER
# Brukes til geografisk trekning i tidlige runder
# =============================================================================
class Region(Enum):
    OST   = "Øst"
    SOR   = "Sør"
    VEST  = "Vest"
    MIDT  = "Midt-Norge"
    NORD  = "Nord"

# Hvilke fylker/områder tilhører hvilken region
REGION_MAPPING = {
    # Øst
    "Oslo":           Region.OST,
    "Viken":          Region.OST,
    "Innlandet":      Region.OST,
    "Østfold":        Region.OST,
    "Akershus":       Region.OST,
    # Sør
    "Vestfold":       Region.SOR,
    "Telemark":       Region.SOR,
    "Agder":          Region.SOR,
    # Vest
    "Rogaland":       Region.VEST,
    "Vestland":       Region.VEST,
    "Hordaland":      Region.VEST,
    # Midt
    "Møre og Romsdal":Region.MIDT,
    "Trøndelag":      Region.MIDT,
    # Nord
    "Nordland":       Region.NORD,
    "Troms":          Region.NORD,
    "Finnmark":       Region.NORD,
}

# Eliteserien-klubbers regioner (for cup-trekning fra runde 3)
KLUBB_REGION = {
    "Rosenborg":       Region.MIDT,
    "Molde":           Region.MIDT,
    "Brann":           Region.VEST,
    "Viking":          Region.VEST,
    "Bodø/Glimt":      Region.NORD,
    "Tromsø":          Region.NORD,
    "Vålerenga":       Region.OST,
    "Lillestrøm":      Region.OST,
    "Fredrikstad":     Region.OST,
    "Stabæk":          Region.OST,
    "Sarpsborg 08":    Region.OST,
    "Odd":             Region.SOR,
    "Start":           Region.SOR,
    "Aalesund":        Region.MIDT,
    "HamKam":          Region.OST,
    "Strømsgodset":    Region.OST,
}


# =============================================================================
# NON-LEAGUE LAG
# Lever i poolen under ligasystemet — kan rykke opp til 3. divisjon
# =============================================================================
@dataclass
class NonLeagueLag:
    """
    Amatør/non-league lag som deltar i cupen og kan rykke opp i ligasystemet.

    lod = 0: Ren amatørklubb — genererte spillere, enkel simulering
    lod = 1: I ligasystemet (3. divisjon) — får full LOD 1-behandling
    """
    id: int
    navn: str
    region: Region
    styrke: int = 5          # 1–20, lavere enn profesjonelle lag
    lod: int = 0
    sesonger_i_ligasystem: int = 0
    cup_deltakelser: int = 0
    spillere: list = field(default_factory=list)   # Genererte spillerobjekter

    def rykk_opp_til_ligasystem(self):
        self.lod = 1
        self.sesonger_i_ligasystem = 0
        print(f"[{self.navn}] Rykker opp til 3. divisjon! Blir LOD 1-lag.")

    def rykk_ned_fra_ligasystem(self):
        self.lod = 0
        print(f"[{self.navn}] Rykker ned fra 3. divisjon. Tilbake i non-league poolen.")

    def __repr__(self):
        status = "LOD 1" if self.lod == 1 else "Non-league"
        return f"<NonLeagueLag: {self.navn} ({self.region.value}), styrke {self.styrke}, {status}>"


# =============================================================================
# NON-LEAGUE POOL
# Holder alle amatørlag og håndterer opprykk/nedrykk fra ligasystemet
# =============================================================================
class NonLeaguePool:
    """
    Poolen av lag under ligasystemet.
    Disse lagene deltar i cupen og kjemper om opprykk til 3. divisjon.
    """

    # Eksempel på norske non-league lag fordelt på regioner
    STARTLAG = [
        # Øst
        ("Frigg Oslo",          Region.OST,  6),
        ("Kjelsås",             Region.OST,  6),
        ("Grorud",              Region.OST,  7),
        ("Lørenskog",           Region.OST,  5),
        ("Follo",               Region.OST,  6),
        ("Ås",                  Region.OST,  4),
        ("Nordstrand",          Region.OST,  5),
        ("Bærum",               Region.OST,  5),
        ("Kongsvinger",         Region.OST,  6),
        ("Raufoss",             Region.OST,  7),
        ("Gjøvik-Lyn",          Region.OST,  5),
        ("Elverum",             Region.OST,  5),
        # Sør
        ("Jerv",                Region.SOR,  7),
        ("Arendal",             Region.SOR,  6),
        ("Vindbjart",           Region.SOR,  5),
        ("Kristiansand",        Region.SOR,  5),
        ("Notodden",            Region.SOR,  6),
        ("Pors",                Region.SOR,  5),
        # Vest
        ("Sogndal",             Region.VEST, 7),
        ("Florø",               Region.VEST, 5),
        ("Hødd",                Region.VEST, 6),
        ("Sandnes Ulf",         Region.VEST, 7),
        ("Haugesund",           Region.VEST, 7),
        ("Egersund",            Region.VEST, 5),
        ("Stord",               Region.VEST, 4),
        # Midt
        ("Ranheim",             Region.MIDT, 7),
        ("Orkla",               Region.MIDT, 5),
        ("Sunndalsøra",         Region.MIDT, 4),
        ("Kristiansund",        Region.MIDT, 7),
        ("Steinkjer",           Region.MIDT, 5),
        ("Levanger",            Region.MIDT, 6),
        # Nord
        ("Harstad",             Region.NORD, 5),
        ("Narvik",              Region.NORD, 5),
        ("Alta",                Region.NORD, 6),
        ("Hammerfest",          Region.NORD, 4),
        ("Finnsnes",            Region.NORD, 4),
        ("Tromsdalen",          Region.NORD, 6),
    ]

    def __init__(self):
        self.lag: list[NonLeagueLag] = []
        self._neste_id = 1000
        self._populer_startlag()

    def _populer_startlag(self):
        for navn, region, styrke in self.STARTLAG:
            self.legg_til_lag(navn, region, styrke)

    def legg_til_lag(self, navn: str, region: Region, styrke: int = 5) -> NonLeagueLag:
        lag = NonLeagueLag(
            id=self._neste_id,
            navn=navn,
            region=region,
            styrke=styrke,
        )
        self.lag.append(lag)
        self._neste_id += 1
        return lag

    def hent_per_region(self, region: Region) -> list[NonLeagueLag]:
        return [l for l in self.lag if l.region == region and l.lod == 0]

    def hent_alle_amatorer(self) -> list[NonLeagueLag]:
        """Returnerer alle lag som IKKE er i ligasystemet."""
        return [l for l in self.lag if l.lod == 0]

    def motta_nedrykkslag(self, lag: NonLeagueLag):
        """Kalles av ligasystemet når et lag rykker ned fra 3. divisjon."""
        if lag not in self.lag:
            self.lag.append(lag)
        lag.rykk_ned_fra_ligasystem()

    def __repr__(self):
        amatorer = len(self.hent_alle_amatorer())
        i_liga = len([l for l in self.lag if l.lod == 1])
        return f"<NonLeaguePool: {amatorer} amatørlag, {i_liga} i ligasystemet>"


# =============================================================================
# CUPKAMP
# =============================================================================
@dataclass
class CupKamp:
    """Én kamp i NM-cupen."""
    hjemme: object        # Klubb, NonLeagueLag eller UtenlandskKlubb
    borte: object
    runde: int            # 1–7 (7 = finale)
    nøytralbane: bool = False   # Semifinale og finale

    hjemme_maal: Optional[int] = None
    borte_maal: Optional[int] = None
    spilt: bool = False
    ekstraomganger: bool = False
    straffer: bool = False

    def registrer_resultat(
        self,
        hjemme_maal: int,
        borte_maal: int,
        ekstraomganger: bool = False,
        straffer: bool = False,
    ):
        self.hjemme_maal = hjemme_maal
        self.borte_maal = borte_maal
        self.ekstraomganger = ekstraomganger
        self.straffer = straffer
        self.spilt = True

    @property
    def vinner(self) -> Optional[object]:
        """Cup har alltid en vinner — straffer avgjør ved uavgjort."""
        if not self.spilt:
            return None
        if self.hjemme_maal > self.borte_maal:
            return self.hjemme
        return self.borte   # Inkluderer straffescenario

    @property
    def inneholder_eliteserielag(self) -> bool:
        from klubb import Klubb
        return isinstance(self.hjemme, Klubb) or isinstance(self.borte, Klubb)

    def simuler_lod0(self):
        """Enkel simulering for kamper uten Eliteserien/OBOS-lag."""
        hjemme_styrke = getattr(self.hjemme, 'styrke', 10)
        borte_styrke  = getattr(self.borte,  'styrke', 10)

        # Hjemmebanefordel
        if not self.nøytralbane:
            hjemme_styrke += 2

        total = hjemme_styrke + borte_styrke
        hjemme_vinner = random.random() < (hjemme_styrke / total)

        if hjemme_vinner:
            self.registrer_resultat(
                random.randint(1, 4),
                random.randint(0, 2),
            )
        else:
            self.registrer_resultat(
                random.randint(0, 2),
                random.randint(1, 4),
            )

    def __repr__(self):
        h = getattr(self.hjemme, 'navn', str(self.hjemme))
        b = getattr(self.borte,  'navn', str(self.borte))
        runde_navn = CupTurnering.RUNDE_NAVN.get(self.runde, f"Runde {self.runde}")
        if self.spilt:
            ekstra = " (e.o.)" if self.ekstraomganger else ""
            ekstra += " (str.)" if self.straffer else ""
            return f"<CupKamp R{self.runde}: {h} {self.hjemme_maal}–{self.borte_maal} {b}{ekstra}>"
        return f"<CupKamp R{self.runde}: {h} vs {b}>"


# =============================================================================
# CUP-TURNERING
# Håndterer én komplett NM-cup-sesong (overlapper to kalenderår)
# =============================================================================
class CupTurnering:
    """
    NM-cupen. Starter med runde 1 i august (år N),
    og avsluttes med finale i mai (år N+1).

    Runde 1–3:  Non-league + 3. div + 2. div (geografisk trekning)
    Runde 3:    Eliteserien og OBOS trer inn
    Runde 4–7:  Fri trekning, nøytralbane fra semifinale
    """

    RUNDE_NAVN = {
        1: "1. runde",
        2: "2. runde",
        3: "3. runde",
        4: "4. runde",
        5: "5. runde",
        6: "Semifinale",
        7: "Finale",
    }

    # Antall lag som trer inn per runde (utover vinnere fra forrige runde)
    INNTREDEN = {
        1: [],            # Kun non-league + 3. div
        2: [],            # + 2. div trer inn
        3: [],            # + Eliteserien + OBOS trer inn
    }

    def __init__(self, start_aar: int):
        self.start_aar = start_aar       # År cupen starter (runde 1–3)
        self.finale_aar = start_aar + 1  # År semifinale og finale spilles

        self.runder: dict[int, list[CupKamp]] = {r: [] for r in range(1, 8)}
        self.gjenvaerende_lag: list = []
        self.vinner: Optional[object] = None

    # =========================================================================
    # TREKNING
    # =========================================================================
    def trekning_runde_1(
        self,
        non_league: list,
        div3_lag: list,
        maal_antall: int = 128,
    ) -> list[CupKamp]:
        """
        Geografisk trekning for runde 1.
        Non-league og 3. divisjon-lag trekkes mot hverandre innen samme region.
        Fyller opp til maal_antall lag totalt.
        """
        alle_lag = non_league + div3_lag
        random.shuffle(alle_lag)

        # Sorter per region
        per_region: dict[Region, list] = {r: [] for r in Region}
        for lag in alle_lag:
            region = lag.region if hasattr(lag, 'region') else Region.OST
            per_region[region].append(lag)

        kamper = []
        uparerte = []
        for region, lag_liste in per_region.items():
            random.shuffle(lag_liste)
            # Par opp lagene to og to
            for i in range(0, len(lag_liste) - 1, 2):
                kamp = CupKamp(
                    hjemme=lag_liste[i],
                    borte=lag_liste[i + 1],
                    runde=1,
                )
                kamper.append(kamp)
            # Odde lag pareres på tvers av regioner
            if len(lag_liste) % 2 == 1:
                uparerte.append(lag_liste[-1])

        # Par opp uparerte lag på tvers av regioner
        random.shuffle(uparerte)
        for i in range(0, len(uparerte) - 1, 2):
            kamper.append(CupKamp(
                hjemme=uparerte[i],
                borte=uparerte[i + 1],
                runde=1,
            ))
        if len(uparerte) % 2 == 1:
            self.gjenvaerende_lag.append(uparerte[-1])

        self.runder[1] = kamper
        print(f"[NM-cup] Runde 1 trukket: {len(kamper)} kamper.")
        return kamper

    def trekning_runde_2(self, div2_lag: list) -> list[CupKamp]:
        """
        Runde 2: Vinnere fra runde 1 + 2. divisjon.
        Fortsatt geografisk trekning.
        """
        vinnere_r1 = [k.vinner for k in self.runder[1] if k.spilt and k.vinner]
        alle = vinnere_r1 + list(self.gjenvaerende_lag) + div2_lag
        self.gjenvaerende_lag = []

        return self._geografisk_trekning(alle, runde=2)

    def trekning_runde_3(self, eliteserien_lag: list, obos_lag: list) -> list[CupKamp]:
        """
        Runde 3: Vinnere fra runde 2 + Eliteserien + OBOS.
        Eliteserien-lag trer inn her — fortsatt geografisk trekning.
        """
        vinnere_r2 = [k.vinner for k in self.runder[2] if k.spilt and k.vinner]
        alle = vinnere_r2 + list(self.gjenvaerende_lag) + eliteserien_lag + obos_lag
        self.gjenvaerende_lag = []

        return self._geografisk_trekning(alle, runde=3)

    def trekning_fri(self, runde: int) -> list[CupKamp]:
        """
        Fri trekning for runde 4, 5, semifinale og finale.
        Semifinale og finale spilles på nøytralbane.
        """
        forrige_runde = runde - 1
        vinnere = [k.vinner for k in self.runder[forrige_runde] if k.spilt and k.vinner]
        vinnere += list(self.gjenvaerende_lag)
        self.gjenvaerende_lag = []

        random.shuffle(vinnere)
        nøytral = runde >= 6   # Semifinale og finale

        kamper = []
        for i in range(0, len(vinnere) - 1, 2):
            kamp = CupKamp(
                hjemme=vinnere[i],
                borte=vinnere[i + 1],
                runde=runde,
                nøytralbane=nøytral,
            )
            kamper.append(kamp)

        self.runder[runde] = kamper
        runde_navn = self.RUNDE_NAVN.get(runde, f"Runde {runde}")
        print(f"[NM-cup] {runde_navn} trukket: {len(kamper)} kamper.")
        return kamper

    def _geografisk_trekning(self, lag_liste: list, runde: int) -> list[CupKamp]:
        """Trekker geografisk — prøver å pare lag fra samme region."""
        per_region: dict[Region, list] = {r: [] for r in Region}
        uten_region = []

        for lag in lag_liste:
            if hasattr(lag, 'region'):
                per_region[lag.region].append(lag)
            else:
                # Klubb fra liga.py — slå opp i KLUBB_REGION
                region = KLUBB_REGION.get(
                    getattr(lag, 'navn', ''),
                    Region.OST
                )
                per_region[region].append(lag)

        kamper = []
        uparerte = []

        for region, lag_i_region in per_region.items():
            random.shuffle(lag_i_region)
            for i in range(0, len(lag_i_region) - 1, 2):
                kamper.append(CupKamp(
                    hjemme=lag_i_region[i],
                    borte=lag_i_region[i + 1],
                    runde=runde,
                ))
            if len(lag_i_region) % 2 == 1:
                uparerte.append(lag_i_region[-1])

        # Par opp uparerte lag på tvers av regioner
        random.shuffle(uparerte)
        for i in range(0, len(uparerte) - 1, 2):
            kamper.append(CupKamp(
                hjemme=uparerte[i],
                borte=uparerte[i + 1],
                runde=runde,
            ))
        if len(uparerte) % 2 == 1:
            self.gjenvaerende_lag.append(uparerte[-1])

        self.runder[runde] = kamper
        runde_navn = self.RUNDE_NAVN.get(runde, f"Runde {runde}")
        print(f"[NM-cup] {runde_navn} trukket: {len(kamper)} kamper.")
        return kamper

    # =========================================================================
    # SIMULERING
    # =========================================================================
    def simuler_runde(self, runde: int) -> list[CupKamp]:
        """
        Simulerer alle kamper i en runde.
        Kamper med LOD 1-lag returneres til spillmotoren for detaljert simulering.
        Resten simuleres med LOD 0-metoden.
        """
        kamper = self.runder.get(runde, [])
        lod1_kamper = []

        for kamp in kamper:
            if kamp.inneholder_eliteserielag:
                lod1_kamper.append(kamp)
            elif not kamp.spilt:
                kamp.simuler_lod0()

        runde_navn = self.RUNDE_NAVN.get(runde, f"Runde {runde}")
        simulert = len(kamper) - len(lod1_kamper)
        print(
            f"[NM-cup] {runde_navn}: "
            f"{simulert} kamper simulert (LOD 0), "
            f"{len(lod1_kamper)} venter på LOD 1-simulering."
        )
        return lod1_kamper

    def registrer_lod1_resultat(self, kamp: CupKamp, hjemme_maal: int, borte_maal: int):
        """Kalles av kampsimulatoren etter en LOD 1-kamp er spilt."""
        kamp.registrer_resultat(hjemme_maal, borte_maal)

    def hent_vinner(self) -> Optional[object]:
        """Returnerer cupmesteren etter at finalen er spilt."""
        finale_kamper = self.runder.get(7, [])
        if finale_kamper and finale_kamper[0].spilt:
            self.vinner = finale_kamper[0].vinner
            return self.vinner
        return None

    # =========================================================================
    # STATISTIKK OG VISNING
    # =========================================================================
    def hent_gjenvaerende_lag(self, etter_runde: int) -> list:
        """Returnerer alle lag som fortsatt er med etter en gitt runde."""
        kamper = self.runder.get(etter_runde, [])
        return [k.vinner for k in kamper if k.spilt and k.vinner]

    def print_resultater(self, runde: int):
        runde_navn = self.RUNDE_NAVN.get(runde, f"Runde {runde}")
        print(f"\n{'='*55}")
        print(f"  NM-cup — {runde_navn} — Resultater")
        print(f"{'='*55}")
        for kamp in self.runder.get(runde, []):
            if kamp.spilt:
                print(f"  {kamp}")
            else:
                h = getattr(kamp.hjemme, 'navn', '?')
                b = getattr(kamp.borte,  'navn', '?')
                print(f"  {h} vs {b} (ikke spilt)")
        print(f"{'='*55}\n")

    def print_vei_til_finalen(self, lag) -> None:
        """Skriver ut et lags vei gjennom cupen."""
        lag_navn = getattr(lag, 'navn', str(lag))
        print(f"\n  {lag_navn}s vei i NM-cupen:")
        for runde_nr, kamper in self.runder.items():
            for kamp in kamper:
                if kamp.hjemme is lag or kamp.borte is lag:
                    print(f"    {kamp}")

    def __repr__(self):
        spilte = sum(
            1 for kamper in self.runder.values()
            for k in kamper if k.spilt
        )
        return (
            f"<CupTurnering: {self.start_aar}/{self.finale_aar}, "
            f"{spilte} kamper spilt>"
        )


# =============================================================================
# CUP-MOTOR — koordinerer cup med kalender og ligasystem
# =============================================================================
class CupMotor:
    """
    Koordinerer NM-cupen med resten av spillet.
    Holder styr på aktiv turnering og overlappende cup-sesonger.
    """

    def __init__(self, non_league_pool: NonLeaguePool):
        self.pool = non_league_pool
        self.aktiv_cup: Optional[CupTurnering] = None
        self.forrige_cup: Optional[CupTurnering] = None   # Vår-rundene fra fjorårets cup

    def start_ny_cup_sesong(self, aar: int) -> CupTurnering:
        """
        Starter ny cup-sesong (runde 1 i august).
        Den forrige cupen er fortsatt aktiv (vår-rundene ikke spilt ennå).
        """
        self.forrige_cup = self.aktiv_cup
        self.aktiv_cup = CupTurnering(start_aar=aar)
        print(f"\n[NM-cup] Ny cup-sesong {aar}/{aar+1} startet.")
        return self.aktiv_cup

    def kjor_runde_1(self, div3_lag: list) -> list[CupKamp]:
        """
        Runde 1: Non-league pool + 3. divisjon.
        Fyller opp til 256 lag totalt → 128 kamper.
        """
        amatorer = self.pool.hent_alle_amatorer()
        alle_lag = list(amatorer) + list(div3_lag)

        # Sikre at vi har nok lag — fyll opp med ekstra pool-lag om nødvendig
        maal = 256  # 256 lag → 128 kamper
        while len(alle_lag) < maal:
            ekstra = NonLeagueLag(
                id=9000 + len(alle_lag),
                navn=f"Lokalklubb {len(alle_lag)}",
                region=random.choice(list(Region)),
                styrke=random.randint(2, 5),
            )
            alle_lag.append(ekstra)

        # Trim til nærmeste potens av 2
        while len(alle_lag) > maal:
            alle_lag.pop()

        for lag in alle_lag:
            lag.cup_deltakelser += 1

        # Pass hele listen — trekning_runde_1 kombinerer non_league + div3_lag uansett
        div3_sett = {id(l) for l in div3_lag}
        return self.aktiv_cup.trekning_runde_1(
            non_league=[l for l in alle_lag if id(l) not in div3_sett],
            div3_lag=[l for l in alle_lag if id(l) in div3_sett],
            maal_antall=maal,
        )

    def kjor_runde_2(self, div2_lag: list) -> list[CupKamp]:
        return self.aktiv_cup.trekning_runde_2(div2_lag)

    def kjor_runde_3(self, eliteserien_lag: list, obos_lag: list) -> list[CupKamp]:
        """Runde 3: Eliteserien og OBOS trer inn."""
        return self.aktiv_cup.trekning_runde_3(eliteserien_lag, obos_lag)

    def kjor_fri_trekning(self, runde: int) -> list[CupKamp]:
        """Runde 4, 5, semifinale og finale — fri trekning."""
        return self.aktiv_cup.trekning_fri(runde)

    def avslutt_cup_sesong(self, liga_system) -> Optional[object]:
        """
        Kalles etter at finalen er spilt.
        Returnerer cupvinneren til ligasystemet for europaplass-tildeling.
        """
        if not self.forrige_cup:
            return None
        vinner = self.forrige_cup.hent_vinner()
        if vinner:
            navn = getattr(vinner, 'navn', str(vinner))
            print(f"\n🏆 NM-cup vinner: {navn}!")
        return vinner

    def __repr__(self):
        aktiv = str(self.aktiv_cup) if self.aktiv_cup else "Ingen"
        return f"<CupMotor: aktiv={aktiv}>"


# =============================================================================
# FABRIKKFUNKSJON
# =============================================================================
def opprett_cup_system() -> CupMotor:
    """Oppretter et komplett cup-system med non-league pool."""
    pool = NonLeaguePool()
    motor = CupMotor(pool)
    print(f"[CupMotor] Klar. {pool}")
    return motor
