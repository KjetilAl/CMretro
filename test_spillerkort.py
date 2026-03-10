with open("ui_pygame.py", "r") as f:
    text = f.read()

# ─────────────────────────────────────────────────────────────────────────────
# SKJERM: SPILLERKORT

new_class = """
# ─────────────────────────────────────────────────────────────────────────────
# SKJERM: SPILLERKORT
# ─────────────────────────────────────────────────────────────────────────────
class SpillerkortSkjerm(SkjermData):
    \"\"\"
    Fullskjerm spillerkort for én spiller. Vises når man klikker
    på en spiller i SpillerstallSkjerm eller LaguttakSkjerm.
    \"\"\"
    def __init__(self, spiller, spiller_liste: list, start_idx: int,
                 stat_register, on_tilbake: Callable):
        self.spiller_liste = spiller_liste
        self.idx = start_idx
        self.stat_register = stat_register
        self.on_tilbake = on_tilbake
        self.spiller = spiller

    def _tegn_portrett(self, surf, x, y, pos_str):
        # Tegner pikselsilhuett basert på posisjon
        pygame.draw.rect(surf, P.NAVY, (x, y, 90, 90))
        pygame.draw.rect(surf, P.BLÅL, (x, y, 90, 90), 2)

        hx, hy = x + 45, y + 20
        pygame.draw.circle(surf, P.KREMHVIT, (hx, hy), 12)  # Hode
        pygame.draw.rect(surf, P.KREMHVIT, (hx-18, hy+14, 36, 40)) # Kropp

        if pos_str == 'K':
            pygame.draw.circle(surf, P.GRØNN, (hx-22, hy+30), 8) # Hansker
            pygame.draw.circle(surf, P.GRØNN, (hx+22, hy+30), 8)
        elif pos_str in ['SP', 'HA', 'VA']:
            pygame.draw.circle(surf, P.HVIT, (hx+20, hy+40), 8) # Ball
            pygame.draw.circle(surf, P.SVART, (hx+20, hy+40), 8, 1)

    def _tegn_bar(self, surf, label, verdi, x, y, f):
        tegn_tekst(surf, label, (x, y), f, P.KREMHVIT)
        bar_x = x + 140
        pygame.draw.rect(surf, P.GRÅ_MØRK, (bar_x, y + 2, 100, 10))

        farge = P.GRØNN if verdi >= 14 else (P.GULT if verdi >= 10 else (P.ORANSJE if verdi >= 7 else P.RØD))
        bredde = max(0, min(100, int((verdi / 20.0) * 100)))
        if bredde > 0:
            pygame.draw.rect(surf, farge, (bar_x, y + 2, bredde, 10))
        tegn_tekst(surf, str(verdi), (bar_x + 106, y), f, P.HVIT)

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf, P.NAVY)
        f = Fonter.normal
        fb = Fonter.stor
        fs = Fonter.liten
        s = self.spiller

        pos = getattr(s, 'primær_posisjon', None)
        pos_str = pos.name if pos else '?'
        klubb_navn = "?"
        if hasattr(s, '_naavaerende_rolle') and s._naavaerende_rolle:
            klubb_navn = ""

        _tegn_topplinje(surf, s.fullt_navn, pos_str, klubb_navn)

        # Portrett
        self._tegn_portrett(surf, 20, 40, pos_str)

        # Identitet
        tegn_tekst(surf, f"Alder: {s.alder}", (130, 40), f, P.GRÅ_LYS)
        tegn_tekst(surf, "Nasjonalitet: NOR", (130, 60), f, P.GRÅ_LYS)

        kontr = getattr(s, 'kontrakt', None)
        aar = getattr(kontr, 'utlops_aar', '?') if kontr else 'Ingen'
        lonn = getattr(kontr, 'ukelonn', 0) if kontr else 0
        tegn_tekst(surf, f"Kontrakt utløper: {aar}", (130, 80), f, P.GRÅ_LYS)
        tegn_tekst(surf, f"Ukelønn: kr {lonn:,}", (130, 100), f, P.GRÅ_LYS)
        tegn_tekst(surf, f"Markedsverdi: kr {s.markedsverdi_nok:,}", (130, 120), f, P.GRÅ_LYS)

        # OVR-badge
        pygame.draw.rect(surf, P.GRÅ_PANEL, (480, 40, 80, 80))
        pygame.draw.rect(surf, P.BLÅL, (480, 40, 80, 80), 2)
        tegn_tekst(surf, "OVR", (502, 50), f, P.GRÅ_LYS)
        ovr = s.ferdighet
        farge = P.GRØNN if ovr >= 14 else (P.GULT if ovr >= 10 else P.RØD)
        t_ovr = Fonter.tittel.render(str(ovr), False, farge)
        surf.blit(t_ovr, (520 - t_ovr.get_width()//2, 70))

        tegn_linje_h(surf, P.GRÅ_MØRK, 20, 150, W_BASE - 40)

        # Tekniske ferdigheter (venstre)
        y0 = 160
        x0_v = 20
        self._tegn_bar(surf, "Skudd", s.skudd, x0_v, y0, f)
        self._tegn_bar(surf, "Pasning", s.pasning, x0_v, y0+20, f)
        self._tegn_bar(surf, "Dribling", s.dribling, x0_v, y0+40, f)
        self._tegn_bar(surf, "Takling", s.takling, x0_v, y0+60, f)
        self._tegn_bar(surf, "Hodespill", s.hodespill, x0_v, y0+80, f)
        self._tegn_bar(surf, "Teknikk", s.teknikk, x0_v, y0+100, f)
        self._tegn_bar(surf, "Dødball", s.dodball, x0_v, y0+120, f)
        self._tegn_bar(surf, "Keeper", s.keeperferdighet, x0_v, y0+140, f)

        # Fysiske & mentale (høyre)
        x0_h = 320
        self._tegn_bar(surf, "Fart", s.fart, x0_h, y0, f)
        self._tegn_bar(surf, "Utholdenhet", s.utholdenhet, x0_h, y0+20, f)
        self._tegn_bar(surf, "Fysikk", s.fysikk, x0_h, y0+40, f)
        self._tegn_bar(surf, "Kreativitet", s.kreativitet, x0_h, y0+60, f)
        self._tegn_bar(surf, "Aggressivitet", s.aggressivitet, x0_h, y0+80, f)
        self._tegn_bar(surf, "Mentalitet", s.mentalitet, x0_h, y0+100, f)

        # Sesongsstatistikk
        tegn_linje_h(surf, P.GRÅ_MØRK, 20, 320, W_BASE - 40)
        stat = None
        if hasattr(self.stat_register, '_data'):
            pid = getattr(s, 'id', str(id(s)))
            stat = self.stat_register._data.get(pid)

        if stat:
            stat_tekst = f"SESONG:  Kamper: {stat.kamper}   Mål: {stat.mål}   Assist: {stat.assist}   Snitt-rtg: {stat.snitt_rating:.1f}"
        else:
            stat_tekst = "SESONG:  Ingen kamper spilt"
        tegn_tekst(surf, stat_tekst, (20, 330), f, P.GULTL)

        # Knapper
        tegn_knapp(surf, (20, H_BASE-34, 100, 24), "◄ FORRIGE", f,
                   hovered=ui.mus_innenfor((20*SKALA, (H_BASE-34)*SKALA, 100*SKALA, 24*SKALA)))
        tegn_knapp(surf, (W_BASE//2-50, H_BASE-34, 100, 24), "TILBAKE", f,
                   hovered=ui.mus_innenfor(((W_BASE//2-50)*SKALA, (H_BASE-34)*SKALA, 100*SKALA, 24*SKALA)))
        tegn_knapp(surf, (W_BASE-120, H_BASE-34, 100, 24), "NESTE ►", f,
                   hovered=ui.mus_innenfor(((W_BASE-120)*SKALA, (H_BASE-34)*SKALA, 100*SKALA, 24*SKALA)))

    def håndter_event(self, event, ui):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.on_tilbake()
            elif event.key == pygame.K_LEFT:
                self.idx = (self.idx - 1) % len(self.spiller_liste)
                self.spiller = self.spiller_liste[self.idx]
            elif event.key == pygame.K_RIGHT:
                self.idx = (self.idx + 1) % len(self.spiller_liste)
                self.spiller = self.spiller_liste[self.idx]
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            if H_BASE-34 <= my <= H_BASE-10:
                if 20 <= mx <= 120:
                    self.idx = (self.idx - 1) % len(self.spiller_liste)
                    self.spiller = self.spiller_liste[self.idx]
                elif W_BASE//2-50 <= mx <= W_BASE//2+50:
                    self.on_tilbake()
                elif W_BASE-120 <= mx <= W_BASE-20:
                    self.idx = (self.idx + 1) % len(self.spiller_liste)
                    self.spiller = self.spiller_liste[self.idx]

# ─────────────────────────────────────────────────────────────────────────────
# SKJERM: ANDRE RESULTATER (rask gjennomkjøring)
# ─────────────────────────────────────────────────────────────────────────────
"""
text = text.replace("# ─────────────────────────────────────────────────────────────────────────────\n# SKJERM: ANDRE RESULTATER (rask gjennomkjøring)\n# ─────────────────────────────────────────────────────────────────────────────", new_class)

text = text.replace("""class SpillerstallSkjerm(SkjermData):
    def __init__(self, klubb, on_tilbake: Callable):
        self.klubb      = klubb
        self.on_tilbake = on_tilbake""", """class SpillerstallSkjerm(SkjermData):
    def __init__(self, klubb, on_tilbake: Callable, on_spillerkort: Callable = None):
        self.klubb      = klubb
        self.on_tilbake = on_tilbake
        self.on_spillerkort = on_spillerkort""")

text = text.replace("""                if 4 <= mx <= W_BASE-16 and ry <= my < ry+rad_h:
                    self._valgt = idx if self._valgt != idx else -1""", """                if 4 <= mx <= W_BASE-16 and ry <= my < ry+rad_h:
                    if self._valgt == idx:
                        if hasattr(self, 'on_spillerkort') and self.on_spillerkort:
                            self.on_spillerkort(self._alle_spillere[idx], self._alle_spillere, idx)
                    else:
                        self._valgt = idx""")


text = text.replace("""class LaguttakSkjerm(SkjermData):
    \"\"\"
    To kolonner: startellever (venstre) + bane med formasjon (høyre).
    Under: benk. Klikk for å velge og bytte.
    \"\"\"

    def __init__(self, builder, motstandernavn: str, on_ferdig: Callable):
        self.builder       = builder
        self.motstandernavn = motstandernavn
        self.on_ferdig     = on_ferdig""", """class LaguttakSkjerm(SkjermData):
    \"\"\"
    To kolonner: startellever (venstre) + bane med formasjon (høyre).
    Under: benk. Klikk for å velge og bytte.
    \"\"\"

    def __init__(self, builder, motstandernavn: str, on_ferdig: Callable, on_spillerkort: Callable = None):
        self.builder       = builder
        self.motstandernavn = motstandernavn
        self.on_ferdig     = on_ferdig
        self.on_spillerkort = on_spillerkort""")

text = text.replace("""                        if self._valgt_benk >= 0:
                            self.builder.bytt_spiller(i, self._valgt_benk)
                            self._valgt_start = -1; self._valgt_benk = -1
                        else:
                            self._valgt_start = i if self._valgt_start != i else -1""", """                        if self._valgt_benk >= 0:
                            self.builder.bytt_spiller(i, self._valgt_benk)
                            self._valgt_start = -1; self._valgt_benk = -1
                        else:
                            if self._valgt_start == i:
                                if hasattr(self, 'on_spillerkort') and self.on_spillerkort:
                                    self.on_spillerkort(self.builder.startellever[i], self.builder.startellever, i)
                            else:
                                self._valgt_start = i""")

text = text.replace("""                        if self._valgt_start >= 0:
                            self.builder.bytt_spiller(self._valgt_start, j)
                            self._valgt_start = -1; self._valgt_benk = -1
                        else:
                            self._valgt_benk = j if self._valgt_benk != j else -1""", """                        if self._valgt_start >= 0:
                            self.builder.bytt_spiller(self._valgt_start, j)
                            self._valgt_start = -1; self._valgt_benk = -1
                        else:
                            if self._valgt_benk == j:
                                if hasattr(self, 'on_spillerkort') and self.on_spillerkort:
                                    self.on_spillerkort(self.builder.benk[j], self.builder.benk, j)
                            else:
                                self._valgt_benk = j""")


with open("ui_pygame.py", "w") as f:
    f.write(text)
