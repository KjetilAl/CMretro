from dataclasses import dataclass, field
from typing import Optional
from klubb import Klubb

# =============================================================================
# GEOGRAFISKE SONER
# Brukes til å plassere nedrykkslag i riktig avdeling fra nivå 3 og ned
# =============================================================================
GEOGRAFISK_SONE = {
    # Eksempeldata — fylles ut med alle klubber i databasen
    "Brann":             "vest",
    "Viking":            "vest",
    "Rosenborg":         "midt",
    "Molde":             "midt",
    "Tromsø":            "nord",
    "Bodø/Glimt":        "nord",
    "Vålerenga":         "ost",
    "Lillestrøm":        "ost",
    "Fredrikstad":       "ost",
    "Stabæk":            "ost",
    "Sarpsborg 08":      "ost",
    "Odd":               "sor",
    "Start":             "sor",
    "Aalesund":          "midt",
    "HamKam":            "ost",
    "Strømsgodset":      "ost",
}

# Hvilke soner hører til hvilken 2. divisjons-avdeling
DIV2_SONE_TIL_AVD = {
    "ost":  0,   # Avdeling A
    "sor":  0,
    "vest": 1,   # Avdeling B
    "midt": 1,
    "nord": 1,
}

# Hvilke soner hører til hvilken 3. divisjons-avdeling (6 avdelinger)
DIV3_SONE_TIL_AVD = {
    "ost_nord":  0,
    "ost_sor":   1,
    "sor":       2,
    "vest":      3,
    "midt":      4,
    "nord":      5,
}


# =============================================================================
# TABELLRAD
# =============================================================================
@dataclass
class TabellRad:
    """Én klubbs statistikk i en avdelingstabell."""
    klubb: Klubb
    kamper: int = 0
    vunnet: int = 0
    uavgjort: int = 0
    tapt: int = 0
    maal_for: int = 0
    maal_mot: int = 0

    @property
    def poeng(self) -> int:
        return self.vunnet * 3 + self.uavgjort

    @property
    def maaldifferanse(self) -> int:
        return self.maal_for - self.maal_mot

    def registrer_resultat(self, maal_for: int, maal_mot: int):
        """Oppdaterer tabellraden etter en kamp."""
        self.kamper += 1
        self.maal_for += maal_for
        self.maal_mot += maal_mot
        if maal_for > maal_mot:
            self.vunnet += 1
        elif maal_for == maal_mot:
            self.uavgjort += 1
        else:
            self.tapt += 1

    def __repr__(self):
        return (
            f"{self.klubb.navn:<25} "
            f"K:{self.kamper:>2}  "
            f"V:{self.vunnet:>2} U:{self.uavgjort:>2} T:{self.tapt:>2}  "
            f"M:{self.maal_for:>3}-{self.maal_mot:<3}  "
            f"MD:{self.maaldifferanse:>+4}  "
            f"P:{self.poeng:>3}"
        )


# =============================================================================
# KAMP
# =============================================================================
class Kamp:
    """
    Representerer én planlagt eller spilt kamp.
    Brukes både i seriespill og kvalifiseringskamper.
    """

    def __init__(self, hjemme: Klubb, borte: Klubb, kamp_type: str = "serie"):
        self.hjemme = hjemme
        self.borte = borte
        self.kamp_type = kamp_type   # "serie", "kvalik", "cup"
        self.hjemme_maal: Optional[int] = None
        self.borte_maal: Optional[int] = None
        self.spilt = False

    def registrer_resultat(self, hjemme_maal: int, borte_maal: int):
        self.hjemme_maal = hjemme_maal
        self.borte_maal = borte_maal
        self.spilt = True

    @property
    def vinner(self) -> Optional[Klubb]:
        if not self.spilt:
            return None
        if self.hjemme_maal > self.borte_maal:
            return self.hjemme
        elif self.borte_maal > self.hjemme_maal:
            return self.borte
        return None   # Uavgjort — ikke aktuelt i kvalik (krever ekstraomganger/straffar)

    def __repr__(self):
        if self.spilt:
            return f"<Kamp: {self.hjemme.kortnavn} {self.hjemme_maal}–{self.borte_maal} {self.borte.kortnavn}>"
        return f"<Kamp: {self.hjemme.kortnavn} vs {self.borte.kortnavn} [{self.kamp_type}]>"


# =============================================================================
# KVALIFISERINGSRUNDE
# =============================================================================
class KvalifiseringsRunde:
    """
    Håndterer ett trinn i et playoff-system.
    Støtter både enkeltkamper og hjemme/borte over to kamper.
    """

    def __init__(self, navn: str, to_kamper: bool = False):
        self.navn = navn
        self.to_kamper = to_kamper
        self.kamp_1: Optional[Kamp] = None
        self.kamp_2: Optional[Kamp] = None   # Returkamp ved to_kamper=True

    def sett_kamper(self, hjemme: Klubb, borte: Klubb):
        self.kamp_1 = Kamp(hjemme, borte, kamp_type="kvalik")
        if self.to_kamper:
            self.kamp_2 = Kamp(borte, hjemme, kamp_type="kvalik")

    @property
    def vinner(self) -> Optional[Klubb]:
        """
        Returnerer vinneren av runden.
        Ved to kamper: sammenlagtmål avgjør. Ved likt: bortemål, deretter straffar.
        """
        if not self.kamp_1 or not self.kamp_1.spilt:
            return None
        if not self.to_kamper:
            return self.kamp_1.vinner

        if not self.kamp_2 or not self.kamp_2.spilt:
            return None

        # Sammenlagtmål
        maal_hjemme = self.kamp_1.hjemme_maal + self.kamp_2.borte_maal
        maal_borte  = self.kamp_1.borte_maal  + self.kamp_2.hjemme_maal

        if maal_hjemme > maal_borte:
            return self.kamp_1.hjemme
        elif maal_borte > maal_hjemme:
            return self.kamp_1.borte
        else:
            # Bortemålsregelen (eller straffekonk — håndteres av spillmotor)
            bortemaal_hjemmelag = self.kamp_2.borte_maal
            bortemaal_bortelag  = self.kamp_1.borte_maal
            if bortemaal_hjemmelag > bortemaal_bortelag:
                return self.kamp_1.hjemme
            elif bortemaal_bortelag > bortemaal_hjemmelag:
                return self.kamp_1.borte
            return None   # Uavgjort — krever straffespark, spillmotor tar over

    def __repr__(self):
        return f"<KvalifiseringsRunde: {self.navn}>"


# =============================================================================
# AVDELING
# =============================================================================
class Avdeling:
    """
    Én avdeling i en divisjon — f.eks. Eliteserien, eller 2. divisjon avd. A.
    Holder tabellen og terminlisten for avdelingen.
    """

    def __init__(self, navn: str, nivaa: int):
        self.navn = navn
        self.nivaa = nivaa
        self.lag: list[Klubb] = []
        self.tabell: list[TabellRad] = []
        self.terminliste: list[Kamp] = []

    # --- Lagadministrasjon ---
    def legg_til_lag(self, lag_liste: list[Klubb]):
        for lag in lag_liste:
            if lag not in self.lag:
                self.lag.append(lag)
                self.tabell.append(TabellRad(klubb=lag))
                lag.divisjon = self.navn

    def fjern_lag(self, lag_liste: list[Klubb]):
        for lag in lag_liste:
            self.lag = [l for l in self.lag if l.id != lag.id]
            self.tabell = [r for r in self.tabell if r.klubb.id != lag.id]

    # --- Tabelloperasjoner ---
    def sorter_tabell(self):
        """Sorterer etter poeng → målforskjell → målscorte → alfabetisk."""
        self.tabell.sort(
            key=lambda r: (r.poeng, r.maaldifferanse, r.maal_for, r.klubb.navn),
            reverse=True
        )

    def hent_plass(self, plassering: int) -> Optional[Klubb]:
        """Returnerer klubben på gitt plassering (1-indeksert)."""
        self.sorter_tabell()
        if 1 <= plassering <= len(self.tabell):
            return self.tabell[plassering - 1].klubb
        return None

    def hent_rad(self, klubb: Klubb) -> Optional[TabellRad]:
        for rad in self.tabell:
            if rad.klubb.id == klubb.id:
                return rad
        return None

    def registrer_kampresultat(self, kamp: Kamp):
        """Oppdaterer tabellen etter at en kamp er spilt."""
        if not kamp.spilt:
            return
        rad_hjemme = self.hent_rad(kamp.hjemme)
        rad_borte  = self.hent_rad(kamp.borte)
        if rad_hjemme:
            rad_hjemme.registrer_resultat(kamp.hjemme_maal, kamp.borte_maal)
        if rad_borte:
            rad_borte.registrer_resultat(kamp.borte_maal, kamp.hjemme_maal)

    def generer_terminliste(self):
        """Genererer en enkel dobbeltrunde-terminliste (alle mot alle, hjemme og borte)."""
        self.terminliste = []
        for i, hjemme in enumerate(self.lag):
            for j, borte in enumerate(self.lag):
                if i != j:
                    self.terminliste.append(Kamp(hjemme, borte, kamp_type="serie"))

    def print_tabell(self):
        self.sorter_tabell()
        print(f"\n{'='*70}")
        print(f"  {self.navn}")
        print(f"{'='*70}")
        for i, rad in enumerate(self.tabell, 1):
            print(f"  {i:>2}. {rad}")
        print(f"{'='*70}\n")

    def __repr__(self):
        return f"<Avdeling: {self.navn}, {len(self.lag)} lag>"


# =============================================================================
# DIVISJON
# =============================================================================
class Divisjon:
    """
    Et nivå i ligasystemet. Kan ha én eller flere parallelle avdelinger.
    """

    def __init__(self, navn: str, nivaa: int, antall_avdelinger: int = 1):
        self.navn = navn
        self.nivaa = nivaa
        self.avdelinger: list[Avdeling] = [
            Avdeling(
                navn=navn if antall_avdelinger == 1 else f"{navn} avd. {chr(65+i)}",
                nivaa=nivaa
            )
            for i in range(antall_avdelinger)
        ]

    def __repr__(self):
        return (
            f"<Divisjon: {self.navn}, nivå {self.nivaa}, "
            f"{len(self.avdelinger)} avd.>"
        )


# =============================================================================
# LIGASYSTEM
# =============================================================================
class LigaSystem:
    """
    Toppnivå-klassen som koordinerer hele det norske ligasystemet.

    Nivåer:
        1 — Eliteserien       (1 avdeling, 16 lag)
        2 — OBOS-ligaen       (1 avdeling, 16 lag)
        3 — 2. divisjon       (2 avdelinger, 14 lag hver)
        4 — 3. divisjon       (6 avdelinger, 14 lag hver)
    """

    def __init__(
        self,
        eliteserien: Divisjon,
        obos: Divisjon,
        div_2: Divisjon,
        div_3: Divisjon,
    ):
        self.eliteserien = eliteserien.avdelinger[0]
        self.obos        = obos.avdelinger[0]
        self.div_2       = div_2.avdelinger          # Liste: [avd_A, avd_B]
        self.div_3       = div_3.avdelinger          # Liste: [avd_A ... avd_F]
        self.non_league: list[Klubb] = []            # Lag som har forlatt ligasystemet

        # Europaplasser fylles ut av spillmotoren etter sesongslutt
        self.europaplasser: dict = {
            "mesterliga_kvalik":    [],   # 1. og 2. plass Eliteserien
            "europaliga_kvalik":    [],   # Cupvinner
            "conference_kvalik":    [],   # 3. og 4. plass Eliteserien
        }

    # =========================================================================
    # HJELPEMETODER
    # =========================================================================
    def _flytt_lag(
        self,
        lag_liste: list[Klubb],
        fra: Avdeling,
        til: Avdeling
    ):
        fra.fjern_lag(lag_liste)
        til.legg_til_lag(lag_liste)

    def _geografisk_avdeling(
        self,
        klubb: Klubb,
        avdelinger: list[Avdeling],
        sone_kart: dict
    ) -> Avdeling:
        """Finner riktig avdeling basert på klubbens geografiske sone."""
        sone = GEOGRAFISK_SONE.get(klubb.navn, None)
        avd_indeks = sone_kart.get(sone, 0)   # Fallback: avdeling 0
        return avdelinger[avd_indeks]

    # =========================================================================
    # DIREKTE OPPRYKK OG NEDRYKK
    # Kjøres rett etter siste serierunde, før kvalifiseringskampene
    # =========================================================================
    def gjennomfoer_direkte_opp_nedrykk(self):
        print("\n" + "="*60)
        print("  DIREKTE OPPRYKK OG NEDRYKK")
        print("="*60)

        self.eliteserien.sorter_tabell()
        self.obos.sorter_tabell()
        for avd in self.div_2:
            avd.sorter_tabell()
        for avd in self.div_3:
            avd.sorter_tabell()

        # --- ELITESERIEN ↔ OBOS ---
        elite_ned = [self.eliteserien.hent_plass(15), self.eliteserien.hent_plass(16)]
        obos_opp  = [self.obos.hent_plass(1), self.obos.hent_plass(2)]

        self._flytt_lag(elite_ned, fra=self.eliteserien, til=self.obos)
        self._flytt_lag(obos_opp,  fra=self.obos, til=self.eliteserien)

        for lag in elite_ned: lag.opplev_hendelse("nedrykk")
        for lag in obos_opp:  lag.opplev_hendelse("opprykk")
        self.eliteserien.hent_plass(1) and self.eliteserien.tabell[0].klubb.opplev_hendelse("seriemester")

        print(f"  Ned fra Eliteserien: {[l.navn for l in elite_ned]}")
        print(f"  Opp til Eliteserien: {[l.navn for l in obos_opp]}")

        # --- OBOS ↔ 2. DIVISJON ---
        obos_ned     = [self.obos.hent_plass(15), self.obos.hent_plass(16)]
        div2_vinnere = [avd.hent_plass(1) for avd in self.div_2]

        self.obos.fjern_lag(obos_ned)
        for lag in obos_ned:
            maal_avd = self._geografisk_avdeling(lag, self.div_2, DIV2_SONE_TIL_AVD)
            maal_avd.legg_til_lag([lag])
            lag.opplev_hendelse("nedrykk")

        for i, vinner in enumerate(div2_vinnere):
            self.div_2[i].fjern_lag([vinner])
            self.obos.legg_til_lag([vinner])
            vinner.opplev_hendelse("opprykk")

        print(f"  Ned fra OBOS:        {[l.navn for l in obos_ned]}")
        print(f"  Opp til OBOS:        {[l.navn for l in div2_vinnere]}")

        # --- 2. DIVISJON ↔ 3. DIVISJON ---
        # Bunn 3 i hver 2. div-avdeling ned (6 lag), vinnere av 3. div opp (6 lag)
        div2_ned     = []
        div3_vinnere = []

        for avd in self.div_2:
            for plass in [12, 13, 14]:
                lag = avd.hent_plass(plass)
                if lag:
                    div2_ned.append((lag, avd))
                    lag.opplev_hendelse("nedrykk")

        for avd in self.div_3:
            vinner = avd.hent_plass(1)
            if vinner:
                div3_vinnere.append((vinner, avd))
                vinner.opplev_hendelse("opprykk")

        for lag, fra_avd in div2_ned:
            maal_avd = self._geografisk_avdeling(lag, self.div_3, DIV3_SONE_TIL_AVD)
            fra_avd.fjern_lag([lag])
            maal_avd.legg_til_lag([lag])

        for vinner, fra_avd in div3_vinnere:
            maal_avd = self._geografisk_avdeling(vinner, self.div_2, DIV2_SONE_TIL_AVD)
            fra_avd.fjern_lag([vinner])
            maal_avd.legg_til_lag([vinner])

        # --- 3. DIVISJON → NON-LEAGUE ---
        # Bunn 3 i hver av de 6 avdelingene forlater ligasystemet (18 lag)
        for avd in self.div_3:
            for plass in [12, 13, 14]:
                lag = avd.hent_plass(plass)
                if lag:
                    avd.fjern_lag([lag])
                    self.non_league.append(lag)
                    print(f"  {lag.navn} forlater ligasystemet (non-league).")

    # =========================================================================
    # KVALIFISERINGSKAMPER
    # Opprettes etter direkte opprykk/nedrykk er gjennomført
    # =========================================================================
    def generer_kvalifiseringer(self) -> dict:
        """
        Returnerer en dict med alle kvalifiseringsrunder som skal spilles.

        OBOS-playoff (3.–6. plass OBOS vs 14. plass Eliteserien):
            Runde 1: 5. vs 6. plass (enkeltkamp, hjemme for 5.)
            Runde 2: 4. plass hjemme vs vinner runde 1
            Runde 3: 3. plass hjemme vs vinner runde 2
            Finale:  Vinner runde 3 hjemme+borte vs 14. Eliteserien

        2. div-playoff (2. plass avd. A vs 2. plass avd. B vs 13. OBOS):
            Runde 1: Avd. A nr. 2 vs avd. B nr. 2 (enkeltkamp)
            Finale:  Vinner runde 1 hjemme+borte vs 13. OBOS
        """
        self.eliteserien.sorter_tabell()
        self.obos.sorter_tabell()

        # Lag som allerede er direkte rykket er fjernet fra tabellen —
        # indeksene her gjelder den gjenværende tabellen
        elite_14   = self.eliteserien.hent_plass(14)
        obos_13    = self.obos.hent_plass(13)
        obos_3     = self.obos.hent_plass(3)
        obos_4     = self.obos.hent_plass(4)
        obos_5     = self.obos.hent_plass(5)
        obos_6     = self.obos.hent_plass(6)
        div2_toer_a = self.div_2[0].hent_plass(2)
        div2_toer_b = self.div_2[1].hent_plass(2)

        # --- OBOS-PLAYOFF ---
        obos_r1 = KvalifiseringsRunde("OBOS playoff R1", to_kamper=False)
        obos_r1.sett_kamper(hjemme=obos_5, borte=obos_6)

        obos_r2 = KvalifiseringsRunde("OBOS playoff R2", to_kamper=False)
        # Hjemme: obos_4 — borte: vinner av R1 (settes av spillmotoren etter R1)

        obos_r3 = KvalifiseringsRunde("OBOS playoff R3", to_kamper=False)
        # Hjemme: obos_3 — borte: vinner av R2

        obos_finale = KvalifiseringsRunde("OBOS playoff finale", to_kamper=True)
        # Vinner av R3 vs elite_14

        # --- 2. DIV-PLAYOFF ---
        div2_r1 = KvalifiseringsRunde("2. div playoff R1", to_kamper=False)
        div2_r1.sett_kamper(hjemme=div2_toer_a, borte=div2_toer_b)

        div2_finale = KvalifiseringsRunde("2. div playoff finale", to_kamper=True)
        # Vinner av R1 vs obos_13

        return {
            "obos_playoff": {
                "r1":       obos_r1,        # 5. vs 6. plass
                "r2":       obos_r2,        # 4. plass venter
                "r3":       obos_r3,        # 3. plass venter
                "finale":   obos_finale,    # 14. Elite venter
                "venteliste": {
                    "r2": obos_4,
                    "r3": obos_3,
                    "finale": elite_14,
                }
            },
            "div2_playoff": {
                "r1":       div2_r1,        # 2. avd A vs 2. avd B
                "finale":   div2_finale,    # 13. OBOS venter
                "venteliste": {
                    "finale": obos_13,
                }
            },
        }

    # =========================================================================
    # EUROPAPLASSER
    # Registreres av spillmotoren — brukes av europa.py neste sesong
    # =========================================================================
    def registrer_europaplasser(self, cupvinner: Klubb):
        """Kalles av spillmotoren etter at cupen og serien er ferdigspilt."""
        self.eliteserien.sorter_tabell()
        self.europaplasser["mesterliga_kvalik"] = [
            self.eliteserien.hent_plass(1),
            self.eliteserien.hent_plass(2),
        ]
        self.europaplasser["europaliga_kvalik"] = [cupvinner]
        self.europaplasser["conference_kvalik"] = [
            self.eliteserien.hent_plass(3),
            self.eliteserien.hent_plass(4),
        ]
        print("\n  Europaplasser registrert:")
        for turnering, lag in self.europaplasser.items():
            print(f"    {turnering}: {[l.navn for l in lag if l]}")

    # =========================================================================
    # REPRESENTASJON
    # =========================================================================
    def __repr__(self):
        return (
            f"<LigaSystem: "
            f"Elite({len(self.eliteserien.lag)}) "
            f"OBOS({len(self.obos.lag)}) "
            f"2.div({sum(len(a.lag) for a in self.div_2)}) "
            f"3.div({sum(len(a.lag) for a in self.div_3)})>"
        )


# =============================================================================
# FABRIKKFUNKSJON
# Oppretter ligasystemet med riktig struktur — brukes ved spilloppstart
# =============================================================================
def opprett_ligasystem() -> LigaSystem:
    """Returnerer et tomt men korrekt strukturert ligasystem."""
    return LigaSystem(
        eliteserien=Divisjon("Eliteserien",  nivaa=1, antall_avdelinger=1),
        obos=        Divisjon("OBOS-ligaen", nivaa=2, antall_avdelinger=1),
        div_2=       Divisjon("2. divisjon", nivaa=3, antall_avdelinger=2),
        div_3=       Divisjon("3. divisjon", nivaa=4, antall_avdelinger=6),
    )
