"""
spillmotor_pygame.py  —  Norsk Football Manager '95
Erstatter spillmotor.py sin terminal-I/O med pygame-basert UIMotor.

Alle _meny(), _input(), _vent() og print() er fjernet.
Logikken fra TroppBuilder og Spillmotor er beholdt intakt —
kun presentasjonslaget er byttet ut.
"""

from __future__ import annotations

import datetime
import random
import sys
from typing import Optional, Any

# ── Spill-moduler ──────────────────────────────────────────────────────────
from database     import last_database, hent_spilleklar_tropp
from kalender     import SpillKalender, KalenderHendelse
from kampmotor    import KampMotor
from hendelser    import HendelsesManager
from taktikk      import TAKTIKK_KATALOG, Oppstilling, Posisjon, POSISJON_GRUPPE
from liga         import LigaSystem, opprett_ligasystem, populer_ligasystem_fra_db
from person       import Person
from tabell       import Seriatabell, SpillerStatistikkRegister
from okonomi      import Kontrakt, SpillerMarked, AIManager, _minstelonn_krav
from cup          import opprett_cup_system

# ── UI ─────────────────────────────────────────────────────────────────────
from ui_pygame import (
    UIMotor,
    HovedmenySkjerm,
    VelgKlubbSkjerm,
    HubSkjerm,
    KampdagSkjerm,
    LaguttakSkjerm,
    SpillerstallSkjerm,
    TabellSkjerm,
    KamprapportSkjerm,
    InfoSkjerm,
    AndreResultaterSkjerm,
    SesongsSluttSkjerm,
    KlubbInfoSkjerm,
)

# =============================================================================
# KONSTANTER
# =============================================================================
SESONG_AAR     = 2025
BENK_STØRRELSE = 7
KOND_GOD       = 90.0
KOND_OK        = 75.0
KOND_LITEN     = 60.0


# =============================================================================
# TROPP-BUILDER  (uendret logikk fra spillmotor.py)
# =============================================================================
class TroppBuilder:
    def __init__(self, klubb, formasjon_navn: str = "4-3-3"):
        self.klubb          = klubb
        self.formasjon_navn = formasjon_navn
        self.startellever: list[Person] = []
        self.benk: list[Person]         = []
        self._bygg_forslag()

    def _bygg_forslag(self):
        formasjon = TAKTIKK_KATALOG.get(
            self.formasjon_navn, next(iter(TAKTIKK_KATALOG.values())))
        tropp = hent_spilleklar_tropp(self.klubb)

        plassert = set()
        ellever  = []

        sone_rekkefølge = {"forsvar": 0, "midtbane": 1, "angrep": 2}
        slots = sorted(
            formasjon.slots if hasattr(formasjon, 'slots') else [],
            key=lambda s: sone_rekkefølge.get(getattr(s, 'sone', 'midtbane'), 1)
        )

        for slot in slots:
            beste = self._finn_beste_for_slot(slot.posisjon, tropp, plassert)
            if beste:
                ellever.append(beste)
                plassert.add(id(beste))

        for s in tropp:
            if len(ellever) >= 11:
                break
            if id(s) not in plassert:
                ellever.append(s)
                plassert.add(id(s))

        self.startellever = ellever[:11]

        benk_kandidater = [
            s for s in sorted(tropp, key=lambda x: getattr(x, 'ferdighet', 0), reverse=True)
            if id(s) not in plassert
        ]
        self.benk = benk_kandidater[:BENK_STØRRELSE]

    def _finn_beste_for_slot(self, slot, tropp, plassert) -> Optional[Person]:
        from taktikk import KOMPATIBLE_POSISJONER
        kandidater = []
        for s in tropp:
            if id(s) in plassert:
                continue
            primær   = getattr(s, 'primær_posisjon', None)
            sekundær = getattr(s, 'sekundær_posisjon', None)
            if primær == slot:
                eff = 1.00
            elif sekundær == slot:
                eff = 0.85
            elif primær and slot in KOMPATIBLE_POSISJONER.get(primær, set()):
                eff = 0.81
            else:
                continue
            score = (getattr(s, 'ferdighet', 0) * eff
                     * (getattr(s, 'kondisjon', 100) / 100))
            kandidater.append((score, s))
        if not kandidater:
            return None
        return max(kandidater, key=lambda x: x[0])[1]

    def bytt_spiller(self, start_idx: int, benk_idx: int) -> bool:
        if not (0 <= start_idx < len(self.startellever)):
            return False
        if not (0 <= benk_idx < len(self.benk)):
            return False
        self.startellever[start_idx], self.benk[benk_idx] = \
            self.benk[benk_idx], self.startellever[start_idx]
        return True

    def bytt_formasjon(self, ny: str) -> bool:
        if ny not in TAKTIKK_KATALOG:
            return False
        self.formasjon_navn = ny
        self._bygg_forslag()
        return True

    def bygg_oppstilling(self) -> Oppstilling:
        formasjon = TAKTIKK_KATALOG[self.formasjon_navn]
        slots     = formasjon.slots if hasattr(formasjon, 'slots') else []
        plasseringer = {}
        for i, slot in enumerate(slots[:11]):
            if i < len(self.startellever):
                plasseringer[slot.posisjon] = self.startellever[i]
        return Oppstilling(formasjon=formasjon, plasseringer=plasseringer)


# =============================================================================
# PYGAME SPILLMOTOR
# =============================================================================
class SpillmotorPygame:
    """
    Koordinator — eier alle moduler, kjører pygame event-loop.
    Bruker UIMotor for all visning og input.
    """

    def __init__(self):
        self.ui              = UIMotor()
        self.klubber: dict   = {}
        self.spiller_klubb   = None
        self.kalender: SpillKalender = None
        self.liga: LigaSystem        = None
        self.hendelser               = HendelsesManager()
        self._kjører: bool           = False
        self._tabell                 = None
        self._stat_register          = SpillerStatistikkRegister()
        self._builder: Optional[TroppBuilder] = None   # Lagret mellom kamp og laguttak
        self.manager_fornavn         = ""
        self.manager_etternavn       = ""
        self.ui.manager_fornavn      = ""
        self.ui.manager_etternavn    = ""
        self._tabeller: dict[str, Seriatabell] = {}
        self._siste_resultat = None   # (h_navn, h_maal, b_navn, b_maal) etter sist spilte kamp
        self.cup_motor = None
        self.spillermarked = SpillerMarked()
        self._sesong_aar = SESONG_AAR

    # =========================================================================
    # OPPSTART
    # =========================================================================
    def start(self):
        """Inngangspunkt. Viser splash, deretter velg-klubb, deretter game loop."""
        valgt = {"ferdig": False}

        def _gå_til_velg():
            self.ui.bytt_skjerm(self._lag_velg_klubb_skjerm())

        def _avslutt():
            self.ui.avslutt()

        self.ui.tøm_og_sett(HovedmenySkjerm(on_start=_gå_til_velg,
                                              on_avslutt=_avslutt))

        # Kjør loop til database er lastet og klubb er valgt
        while self.ui.tikk():
            if self.spiller_klubb is not None:
                break

        if self.spiller_klubb is None:
            self._rydd_opp()
            return

        ferdig_manager = {"v": False}
        def _manager_ferdig(fornavn, etternavn):
            self.manager_fornavn = fornavn
            self.manager_etternavn = etternavn
            self.ui.manager_fornavn = fornavn
            self.ui.manager_etternavn = etternavn
            ferdig_manager["v"] = True

        from ui_pygame import OpprettManagerSkjerm
        self.ui.bytt_skjerm(OpprettManagerSkjerm(self.spiller_klubb.navn, _manager_ferdig))
        while self.ui.tikk():
            if ferdig_manager["v"]:
                break

        # Bygg ligasystem og kalender
        self._bygg_liga_og_kalender()

        # Kjør selve spillet
        self._kjører = True
        self._game_loop()
        self._rydd_opp()

    def _rydd_opp(self):
        import pygame
        pygame.quit()

    # ── Database + Velg klubb ─────────────────────────────────────────────
    def _lag_velg_klubb_skjerm(self) -> VelgKlubbSkjerm:
        """Laster database (første gang) og returnerer VelgKlubbSkjerm."""
        if not self.klubber:
            # Vis lasteinfo-skjerm mens database lastes
            self.ui.bytt_skjerm(InfoSkjerm(
                "LASTER DATABASE",
                ["Genererer spillere og klubber...", "Vennligst vent."],
                on_ferdig=lambda: None,
            ))
            self.ui.tikk()   # Vis lastebildet én frame

            self.klubber = last_database(sesong_aar=SESONG_AAR, verbose=False)

        DIVISJON_REKKEFØLGE = {
            'Eliteserien': 0, 'OBOS-ligaen': 1,
            'Div 2': 2, 'Div 3': 3,
        }

        # Grupper lag per divisjon
        klubber_per_div = {}
        for k in self.klubber.values():
            div = getattr(k, 'divisjon', 'Ukjent')
            klubber_per_div.setdefault(div, []).append(k)

        alle_lag_sortert = []
        for div in sorted(klubber_per_div.keys(), key=lambda d: DIVISJON_REKKEFØLGE.get(d, 99)):
            alle_lag_sortert.append(div)  # String-separator
            lag_i_div = sorted(klubber_per_div[div], key=lambda k: getattr(k, 'historisk_styrke', 0), reverse=True)
            alle_lag_sortert.extend(lag_i_div)

        def _valgt(klubb):
            self.spiller_klubb = klubb

        return VelgKlubbSkjerm(alle_lag_sortert, on_valgt=_valgt)

    def _bygg_liga_og_kalender(self):
        """Bygger ligasystem, kalender og tabell etter at klubb er valgt."""
        self.liga = opprett_ligasystem()
        populer_ligasystem_fra_db(self.liga, list(self.klubber.values()))

    # 1. GENERER STARTKONTRAKTER FOR ALLE SPILLERE
        for klubb in self.klubber.values():
            for spiller in klubb.spillerstall:
                if spiller.kontrakt is None:
                    spiller.kontrakt = Kontrakt(
                        ukelonn=_minstelonn_krav(spiller),
                        utlops_aar=self._sesong_aar + random.randint(1, 4),
                        signert_aar=self._sesong_aar,
                        spiller_verdi_ved_signering=spiller.markedsverdi_nok
                    )

        # 2. BYGG KALENDER
        self.kalender = SpillKalender(start_aar=self._sesong_aar)
        self.hendelser.sett_dato(datetime.date(self._sesong_aar, 1, 1))

        # Bygg kombinert terminliste
        kombinert = [[] for _ in range(len(self.liga.eliteserien.terminliste))]
        for r in range(len(self.liga.eliteserien.terminliste)):
            kombinert[r].extend(self.liga.eliteserien.terminliste[r])
            if r < len(self.liga.obos.terminliste):
                kombinert[r].extend(self.liga.obos.terminliste[r])
            for avd in self.liga.div_2:
                if r < len(avd.terminliste):
                    kombinert[r].extend(avd.terminliste[r])
            for avd in self.liga.div_3:
                if r < len(avd.terminliste):
                    kombinert[r].extend(avd.terminliste[r])

        self.kalender.populer_serierunder(kombinert)

        # 3. OPPRETT TABELLER (Hver avdeling får sin egen, med eget statistikkregister)
        avdelinger = [self.liga.eliteserien, self.liga.obos] + self.liga.div_2 + self.liga.div_3
        for avd in avdelinger:
            t = Seriatabell(avd.navn)
            t._statistikk_register = SpillerStatistikkRegister()
            for k in avd.lag:
                t.registrer_klubb(getattr(k, 'navn', '?'))
            self._tabeller[avd.navn] = t

        # 4. START CUPEN
        # Spillet begynner 1. januar, men NM-cupen overlapper to sesonger.
        # Runde 1–3 for den pågående 2024/2025-cupen er allerede spilt (høst 2024).
        # Vi bygger og simulerer disse rundene (alle LOD 0) slik at runde 4,
        # semifinale og finale kan trekkes normalt utover vinteren/våren 2025.
        from cup import CupTurnering
        self.cup_motor = opprett_cup_system()

        cup_pagar = CupTurnering(start_aar=self._sesong_aar - 1)
        _div3_lag  = [lag for avd in self.liga.div_3 for lag in avd.lag]
        _div2_lag  = [lag for avd in self.liga.div_2 for lag in avd.lag]
        _elite_lag = list(self.liga.eliteserien.lag)
        _obos_lag  = list(self.liga.obos.lag)

        self.cup_motor.aktiv_cup = cup_pagar
        self.cup_motor.kjor_runde_1(_div3_lag)
        for kamp in cup_pagar.runder[1]:
            kamp.simuler_lod0()
        self.cup_motor.kjor_runde_2(_div2_lag)
        for kamp in cup_pagar.runder[2]:
            kamp.simuler_lod0()
        self.cup_motor.kjor_runde_3(_elite_lag, _obos_lag)
        for kamp in cup_pagar.runder[3]:
            kamp.simuler_lod0()
        # aktiv_cup er nå cup_pagar (2024/2025) – runde 4+ trekkes via kalender-hendelser

    # =========================================================================
    # HUB / LANDING PAGE
    # =========================================================================
    def _finn_neste_kamp(self):
        """
        Finner neste kommende kamp for spillerens klubb i kalenderen.
        Returnerer (dato, kamp) eller None.
        """
        if not self.kalender:
            return None
        dato = self.kalender.dagens_dato
        slutt = datetime.date(dato.year, 12, 31)
        d = dato + datetime.timedelta(days=1)
        while d <= slutt:
            dag = self.kalender._dager.get(d)
            if dag:
                for ki in getattr(dag, 'kamper', []):
                    kamp = getattr(ki, 'kamp', ki)
                    if (getattr(kamp, 'hjemme', None) == self.spiller_klubb
                            or getattr(kamp, 'borte', None) == self.spiller_klubb):
                        if not getattr(kamp, 'spilt', False) and getattr(kamp, 'resultat', None) is None:
                            return (d, kamp)
            d += datetime.timedelta(days=1)
        return None

    def _vis_hub(self, siste_resultat=None):
        """
        Viser HubSkjerm og blokkerer til brukeren klikker «Fortsett».
        Brukes som landingsside mellom hendelser.
        """
        ferdig = {"v": False}

        def _fortsett():
            ferdig["v"] = True

        def _gå_innboks():
            uleste = [h for h in self.hendelser.nyhets_ko if not h.lest]
            if uleste:
                linjer = []
                for h in uleste[:10]:
                    linjer.append(getattr(h, 'tekst', str(h)))
                    h.lest = True
                self._vis_info("INNBOKS", linjer)
            else:
                self._vis_info("INNBOKS", ["Ingen nye meldinger."])

        def _gå_terminliste():
            self._vis_klubb_info(self.spiller_klubb, on_tilbake=lambda: None, start_fane=4)

        uleste_antall = sum(1 for h in self.hendelser.nyhets_ko if not h.lest)
        manager_str   = f"{self.manager_fornavn} {self.manager_etternavn}".strip()
        neste_kamp    = self._finn_neste_kamp()

        skjerm = HubSkjerm(
            spiller_klubb  = self.spiller_klubb,
            dato           = self.kalender.dagens_dato,
            tabeller       = self._tabeller,
            uleste_antall  = uleste_antall,
            manager_navn   = manager_str,
            neste_kamp     = neste_kamp,
            siste_resultat = siste_resultat,
            on_innboks     = _gå_innboks,
            on_spillerstall= lambda: self._vis_spillerstall(on_tilbake=lambda: None),
            on_tabell      = lambda: self._vis_tabell(on_tilbake=lambda: None),
            on_terminliste = _gå_terminliste,
            on_laguttak    = lambda: self._vis_laguttak(
                                TroppBuilder(self.spiller_klubb), "?", on_ferdig=lambda: None),
            on_klubbinfo   = lambda: self._vis_klubb_info(self.spiller_klubb, on_tilbake=lambda: None),
            on_fortsett    = _fortsett,
        )
        self.ui.bytt_skjerm(skjerm)

        while self._kjører and self.ui.tikk():
            if ferdig["v"]:
                break

    # =========================================================================
    # GAME LOOP
    # =========================================================================
    def _game_loop(self):
        """Tikker én dag om gangen. Stopper kun på hendelsesdager. Løkker i uendelig antall sesonger."""
        # Vis hub som startskjerm
        self._vis_hub()

        while self._kjører and self.ui.tikk():
            dag  = self.kalender.simuler_neste_dag()
            dato = self.kalender.dagens_dato
            self.hendelser.sett_dato(dato)

            self._hvil_alle(dag)

            if not dag.har_innhold:
                if self.kalender.er_siste_dag:
                    self._sesong_slutt()
                    if self._kjører:   # Spiller valgte å fortsette
                        self._ny_sesong()
                continue

            # Hendelsesdag — vis UI og vent
            self._vis_hendelsesdag(dag, dato)

            # Vis hub igjen etter hver hendelsesdag
            if self._kjører:
                self._vis_hub(siste_resultat=self._siste_resultat)

    def _hvil_alle(self, dag):
        # Trekk lønn og betal regninger hver mandag
        if self.kalender.dagens_dato.weekday() == 0:
            for klubb in self.klubber.values():
                klubb.betal_ukentlige_utgifter()

        for klubb in self.klubber.values():
            for spiller in klubb.spillerstall:
                var_skadet = getattr(spiller, 'skadet', False)
                if hasattr(spiller, 'hvil_en_dag'):
                    spiller.hvil_en_dag()
                if var_skadet and not getattr(spiller, 'skadet', False):
                    self.hendelser.sjekk_friskmelding(spiller)

    # =========================================================================
    # HENDELSESDAG
    # =========================================================================
    def _simuler_alle_andre_kamper(self, dag):
        """
        Simulerer alle kamper på denne dagen som ikke involverer
        spillerens klubb. Bruker KampMotor med AI-oppstillinger.
        Oppdaterer kamp.registrer_resultat() og tabell.
        """
        for ki in getattr(dag, 'kamper', []):
            # Pakk ut KampInfo-wrapper om nødvendig
            kamp = getattr(ki, 'kamp', ki)
            hjemme = getattr(kamp, 'hjemme', None)
            borte  = getattr(kamp, 'borte', None)
            if hjemme is None or borte is None:
                continue
            if hjemme == self.spiller_klubb or borte == self.spiller_klubb:
                continue
            if getattr(kamp, 'spilt', False) or getattr(kamp, 'resultat', None) is not None:
                continue
            # Cup-kamper mellom non-league/div3: bruk LOD-0-simulering
            if hasattr(kamp, 'simuler_lod0'):
                try:
                    kamp.simuler_lod0()
                except Exception:
                    pass
                continue
            try:
                h_builder = TroppBuilder(hjemme)
                b_builder = TroppBuilder(borte)
                h_opp     = h_builder.bygg_oppstilling()
                b_opp     = b_builder.bygg_oppstilling()
                motor     = KampMotor(tillat_ekstraomganger=False)
                resultat  = motor.spill_kamp(hjemme, borte, h_opp, b_opp)
                kamp.registrer_resultat(resultat.hjemme_maal, resultat.borte_maal)

                div_hjemme = getattr(hjemme, 'divisjon', 'Ukjent')
                if hasattr(self, '_tabeller') and div_hjemme in self._tabeller:
                    tabell = self._tabeller[div_hjemme]
                    tabell.registrer_resultat(resultat)
                    if hasattr(tabell, '_statistikk_register'):
                        tabell._statistikk_register.oppdater_fra_kampresultat(resultat)

                if hasattr(self, '_stat_register'):
                    self._stat_register.oppdater_fra_kampresultat(resultat)
            except Exception:
                pass

    def _vis_hendelsesdag(self, dag, dato: datetime.date):
        self._simuler_alle_andre_kamper(dag)

        har_kamp    = dag.har_kamper if hasattr(dag, 'har_kamper') else bool(dag.kamper)
        mine_kamper = []
        for k in dag.kamper:
            # Pakk ut KampInfo-wrapper om nødvendig
            inner = getattr(k, 'kamp', k)
            if (getattr(inner, 'hjemme', None) == self.spiller_klubb or
                    getattr(inner, 'borte', None) == self.spiller_klubb):
                mine_kamper.append(inner)

        # Vis uleste nyheter som InfoSkjerm
        uleste = [h for h in self.hendelser.nyhets_ko if not h.lest]
        if uleste:
            linjer = []
            for h in uleste[:6]:
                linjer.append(getattr(h, 'tekst', str(h)))
                h.lest = True
            self._vis_info("INNBOKS", linjer)

        if mine_kamper:
            for kamp in mine_kamper:
                self._håndter_kampdag(kamp, dato)
            return

        if dag.hendelser:
            self._håndter_kalender_hendelse(dag, dato)
            return

        if har_kamp:
            self._vis_andre_resultater(dag, dato)

    # =========================================================================
    # KALENDER-HENDELSE
    # =========================================================================
    def _håndter_kalender_hendelse(self, dag, dato: datetime.date):
        for hendelse in dag.hendelser:
            
            # --- AI OVERGANGER ---
            if hendelse in (KalenderHendelse.OVERGANG_1_AAPNER, KalenderHendelse.OVERGANG_2_AAPNER):
                self._vis_info("OVERGANGSVINDUET ÅPNER", ["AI-klubbene er nå aktive på markedet."])
                # La alle AI-klubber forsøke å forsterke laget
                for klubb in self.klubber.values():
                    if klubb != self.spiller_klubb:
                        ai = AIManager(klubb)
                        ai.kjøp_runde(self.spillermarked, SESONG_AAR)
            if hendelse == KalenderHendelse.SERIESTART:
                self._vis_info(
                    "SESONGEN STARTER!",
                    [f"{self.spiller_klubb.navn} er klare for Eliteserien {self._sesong_aar}.",
                     "", "Lykke til!"],
                )
                # --- CUP TREKNINGER ---
            elif hendelse == KalenderHendelse.CUP_RUNDE_1:
                # Start ny cup-sesong – den pågående cupen flyttes til forrige_cup
                self.cup_motor.start_ny_cup_sesong(self._sesong_aar)
                div3_lag = [lag for avd in self.liga.div_3 for lag in avd.lag]
                kamper = self.cup_motor.kjor_runde_1(div3_lag)
                dag.kamper.extend(kamper)
                self._vis_info("NM-CUP", ["1. runde av cupen er trukket!"])

            elif hendelse == KalenderHendelse.CUP_RUNDE_2:
                div2_lag = [lag for avd in self.liga.div_2 for lag in avd.lag]
                kamper = self.cup_motor.kjor_runde_2(div2_lag)
                dag.kamper.extend(kamper)
                self._vis_info("NM-CUP", ["2. runde av cupen er trukket!"])

            elif hendelse == KalenderHendelse.CUP_RUNDE_3:
                elite = self.liga.eliteserien.lag
                obos = self.liga.obos.lag
                kamper = self.cup_motor.kjor_runde_3(elite, obos)
                dag.kamper.extend(kamper)
                self._vis_info("NM-CUP", ["3. runde trukket. Eliteserien trer inn!"])

            elif hendelse in [KalenderHendelse.CUP_RUNDE_4, KalenderHendelse.CUP_RUNDE_5, KalenderHendelse.CUP_SEMIFINALE, KalenderHendelse.CUP_FINALE]:
                runde_nr = int(hendelse.name.split("_")[-1]) if "RUNDE" in hendelse.name else (6 if "SEMI" in hendelse.name else 7)
                kamper = self.cup_motor.kjor_fri_trekning(runde_nr)
                dag.kamper.extend(kamper)
                navn = self.cup_motor.aktiv_cup.RUNDE_NAVN.get(runde_nr, "Cuprunde")
                self._vis_info("NM-CUP", [f"Trekning fullført for {navn}."])
            elif hendelse in (KalenderHendelse.OVERGANG_1_LUKKER,
                               KalenderHendelse.OVERGANG_2_LUKKER):
                self._vis_info("OVERGANGSVINDUET LUKKER",
                                ["Overgangsvinduet er nå stengt."])
            elif hendelse == KalenderHendelse.SERIEFINALE:
                self._vis_info("SERIEFINALE",
                                ["Siste runde av sesongen spilles i dag!"])

    # =========================================================================
    # KAMPDAG
    # =========================================================================
    def _håndter_kampdag(self, kamp, dato: datetime.date):
        er_hjemme  = (kamp.hjemme == self.spiller_klubb)
        motstander = kamp.borte if er_hjemme else kamp.hjemme
        builder    = TroppBuilder(self.spiller_klubb)
        ferdig     = {"verdi": False}

        def _gå_laguttak():
            self._vis_laguttak(builder, motstander.navn, on_ferdig=_tilbake_til_kampdag)

        def _gå_spillerstall():
            self._vis_spillerstall(on_tilbake=_tilbake_til_kampdag)

        def _gå_tabell():
            self._vis_tabell(on_tilbake=_tilbake_til_kampdag)

        def _spill():
            self._spill_kamp(kamp, builder, motstander)
            ferdig["verdi"] = True

        def _tilbake_til_kampdag():
            self.ui.bytt_skjerm(
                KampdagSkjerm(
                    kamp=kamp, dato=dato,
                    spiller_klubb=self.spiller_klubb,
                    motstander=motstander,
                    on_laguttak=_gå_laguttak,
                    on_spill=_spill,
                    on_spillerstall=_gå_spillerstall,
                    on_tabell=_gå_tabell,
                )
            )

        _tilbake_til_kampdag()

        # Vent til kamp er spilt (eller bruker trykker ESC for å hoppe over)
        while self._kjører and self.ui.tikk():
            if ferdig["verdi"]:
                break

    def _vis_spillerkort(self, spiller, spiller_liste, idx, on_tilbake=None):
        from ui_pygame import SpillerkortSkjerm
        def _tilbake():
            self.ui.pop_skjerm()
            if on_tilbake:
                on_tilbake()

        def _forrige():
            skjerm.idx = (skjerm.idx - 1) % len(skjerm.spiller_liste)
            skjerm.spiller = skjerm.spiller_liste[skjerm.idx]

        def _neste():
            skjerm.idx = (skjerm.idx + 1) % len(skjerm.spiller_liste)
            skjerm.spiller = skjerm.spiller_liste[skjerm.idx]

        skjerm = SpillerkortSkjerm(
            spiller=spiller,
            spiller_liste=spiller_liste,
            start_idx=idx,
            stat_register=self._stat_register,
            on_tilbake=_tilbake,
            on_forrige=_forrige,
            on_neste=_neste
        )
        self.ui.push_skjerm(skjerm)

    def _vis_laguttak(self, builder: TroppBuilder, motstandernavn: str,
                       on_ferdig: callable):
        self.ui.push_skjerm(
            LaguttakSkjerm(builder, motstandernavn,
                            on_ferdig=lambda: self.ui.pop_skjerm() or on_ferdig(),
                            on_spillerkort=lambda s, l, i: self._vis_spillerkort(s, l, i))
        )

    def _vis_spillerstall(self, on_tilbake: callable):
        self.ui.push_skjerm(
            SpillerstallSkjerm(
                self.spiller_klubb,
                on_tilbake=lambda: self.ui.pop_skjerm() or on_tilbake(),
                on_spillerkort=lambda s, l, i: self._vis_spillerkort(s, l, i)
            )
        )

    def _vis_tabell(self, on_tilbake: callable):
        def _velg_klubb(klubb_navn: str):
            klubb = None
            for k in self.klubber.values():
                if getattr(k, 'navn', None) == klubb_navn:
                    klubb = k
                    break
            if klubb:
                self._vis_klubb_info(klubb, on_tilbake=lambda: None)

        self.ui.push_skjerm(
            TabellSkjerm(
                tabeller=self._tabeller,
                aktiv_divisjon=self.spiller_klubb.divisjon,
                spiller_klubb_navn=getattr(self.spiller_klubb, 'navn', ''),
                on_tilbake=lambda: self.ui.pop_skjerm() or on_tilbake(),
                on_velg_klubb=_velg_klubb,
            )
        )

    def _vis_klubb_info(self, klubb, on_tilbake: callable, start_fane: int = 0):
        """Push KlubbInfoSkjerm for any club."""
        # Collect terminliste entries involving this club from all avdelinger
        alle_avdelinger = (
            [self.liga.eliteserien, self.liga.obos]
            + list(self.liga.div_2)
            + list(self.liga.div_3)
        )
        terminliste = []
        for avd in alle_avdelinger:
            for runde_idx, runde in enumerate(getattr(avd, 'terminliste', [])):
                # terminliste is list of rounds, each round is a list of Kamp
                kamper_i_runde = runde if isinstance(runde, list) else [runde]
                for kamp in kamper_i_runde:
                    if kamp.hjemme == klubb or kamp.borte == klubb:
                        # Attach runde number for display
                        if not hasattr(kamp, 'runde'):
                            kamp.runde = runde_idx + 1
                        terminliste.append(kamp)

        tabell = self._tabeller.get(getattr(klubb, 'divisjon', ''))
        stat_register = (
            tabell._statistikk_register
            if tabell and hasattr(tabell, '_statistikk_register')
            else None
        )

        def _tilbake():
            self.ui.pop_skjerm()
            if on_tilbake:
                on_tilbake()

        self.ui.push_skjerm(
            KlubbInfoSkjerm(
                klubb=klubb,
                tabell=tabell,
                terminliste=terminliste,
                stat_register=stat_register,
                on_tilbake=_tilbake,
                on_spillerkort=lambda s, l, i: self._vis_spillerkort(s, l, i),
                start_fane=start_fane,
            )
        )

    # =========================================================================
    # SPILL KAMP
    # =========================================================================
    def _spill_kamp(self, kamp, builder: TroppBuilder, motstander):
        er_hjemme      = (kamp.hjemme == self.spiller_klubb)
        hjemme_klubb   = kamp.hjemme
        borte_klubb    = kamp.borte
        hjemme_builder = builder if er_hjemme else TroppBuilder(hjemme_klubb)
        borte_builder  = TroppBuilder(borte_klubb) if er_hjemme else builder

        hjemme_opp = hjemme_builder.bygg_oppstilling()
        borte_opp  = borte_builder.bygg_oppstilling()

        kamp_type = getattr(kamp, 'kamp_type', 'cup')
        motor    = KampMotor(tillat_ekstraomganger=(kamp_type == "cup"))
        resultat = motor.spill_kamp(
            hjemme_klubb, borte_klubb, hjemme_opp, borte_opp
        )

        kamp.registrer_resultat(resultat.hjemme_maal, resultat.borte_maal)

        # Lagre siste resultat for hub-visning
        self._siste_resultat = (
            getattr(hjemme_klubb, 'navn', resultat.hjemme_navn),
            resultat.hjemme_maal,
            getattr(borte_klubb, 'navn', resultat.borte_navn),
            resultat.borte_maal,
        )

        # Oppdater riktig tabell og statistikkregister
        if kamp_type == "serie" and getattr(kamp.hjemme, 'divisjon', None) in self._tabeller:
            aktiv_tabell = self._tabeller[kamp.hjemme.divisjon]
            aktiv_tabell.registrer_resultat(resultat)
            aktiv_tabell._statistikk_register.oppdater_fra_kampresultat(resultat)

            # Lagets resultat-historikk (brukes for styre-vurdering)
            if self.spiller_klubb in (kamp.hjemme, kamp.borte):
                lag_res = ("S" if resultat.vinner_navn == self.spiller_klubb.navn else "U" if resultat.hjemme_maal == resultat.borte_maal else "T")
                if not hasattr(self.spiller_klubb, '_resultat_historikk'):
                    self.spiller_klubb._resultat_historikk = []
                self.spiller_klubb._resultat_historikk.append(lag_res)

                self.hendelser.sjekk_lag_terskler(
                    klubb=self.spiller_klubb,
                    resultater=self.spiller_klubb._resultat_historikk,
                    tabellplass=aktiv_tabell.plass(self.spiller_klubb.navn),
                    runde_nr=len(self.spiller_klubb._resultat_historikk),
                )

        # Oppdater spillerstatistikk
        self._stat_register.oppdater_fra_kampresultat(resultat)

        # Hendelsesregistrering
        alle_spillere = builder.startellever + builder.benk
        for s in alle_spillere:
            rating  = resultat.statistikk.hent_rating(s)
            startet = s in builder.startellever
            self.hendelser.registrer_kampresultat(s, rating, startet)

        # Vis kamprapport (modal — venter til bruker klikker Fortsett)
        ferdig = {"v": False}

        def _ferdig():
            ferdig["v"] = True
            self.ui.pop_skjerm()

        self.ui.push_skjerm(
            KamprapportSkjerm(
                resultat=resultat,
                hjemme_spillere=hjemme_builder.startellever,
                borte_spillere=borte_builder.startellever,
                on_ferdig=_ferdig,
            )
        )
        while self._kjører and self.ui.tikk():
            if ferdig["v"]:
                break

    # =========================================================================
    # ANDRE RESULTATER
    # =========================================================================
    def _vis_andre_resultater(self, dag, dato: datetime.date):
        dato_str = dato.strftime('%d.%m')
        andre = []
        for k in dag.kamper:
            inner = getattr(k, 'kamp', k)
            hjemme = getattr(inner, 'hjemme', None)
            borte  = getattr(inner, 'borte', None)
            if (hjemme != self.spiller_klubb and borte != self.spiller_klubb
                    and getattr(inner, 'spilt', False)):
                andre.append(inner)
        if not andre:
            return

        resultater = []
        for k in andre[:14]:
            resultater.append((
                getattr(k.hjemme, 'kortnavn', getattr(k.hjemme, 'navn', '?')[:6]),
                getattr(k, 'hjemme_maal', 0),
                getattr(k.borte, 'kortnavn', getattr(k.borte, 'navn', '?')[:6]),
                getattr(k, 'borte_maal', 0),
            ))

        ferdig = {"v": False}

        def _ferdig():
            ferdig["v"] = True
            self.ui.pop_skjerm()

        self.ui.push_skjerm(
            AndreResultaterSkjerm(resultater, dato_str, on_ferdig=_ferdig)
        )
        while self._kjører and self.ui.tikk():
            if ferdig["v"]:
                break

    # =========================================================================
    # INFO-HJELPERE
    # =========================================================================
    def _vis_info(self, tittel: str, linjer: list[str]):
        """Blokker til bruker trykker Fortsett."""
        ferdig = {"v": False}

        def _ferdig():
            ferdig["v"] = True
            self.ui.pop_skjerm()

        self.ui.push_skjerm(InfoSkjerm(tittel, linjer, on_ferdig=_ferdig))
        while self._kjører and self.ui.tikk():
            if ferdig["v"]:
                break

    # =========================================================================
    # SESONG SLUTT / NY SESONG
    # =========================================================================
    def _sesong_slutt(self):
        ferdig = {"v": False}

        def _neste_sesong():
            ferdig["v"] = True
            self.ui.pop_skjerm()

        def _avslutt():
            ferdig["v"] = True
            self._kjører = False
            self.ui.pop_skjerm()

        hist = getattr(self.spiller_klubb, '_resultat_historikk', [])
        tabell = self._tabeller.get(
            getattr(self.spiller_klubb, 'divisjon', ''), self._tabell
        )
        self.ui.push_skjerm(
            SesongsSluttSkjerm(
                klubb_navn  = getattr(self.spiller_klubb, 'navn', '?'),
                resultater  = hist,
                tabell      = tabell,
                on_avslutt  = _avslutt,
                on_fortsett = _neste_sesong,
            )
        )
        while self.ui.tikk():
            if ferdig["v"]:
                break

    def _ny_sesong(self):
        """Starter ny sesong: øker årstall, nullstiller historikk og bygger ny kalender."""
        self._sesong_aar += 1
        if hasattr(self.spiller_klubb, '_resultat_historikk'):
            self.spiller_klubb._resultat_historikk = []
        self._bygg_liga_og_kalender()


# =============================================================================
# INNGANGSPUNKT
# =============================================================================
if __name__ == "__main__":
    motor = SpillmotorPygame()
    motor.start()
