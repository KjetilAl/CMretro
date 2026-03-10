with open("ui_pygame.py", "r") as f:
    lines = f.readlines()

def replace_line_in_func(func_name, line_substr, new_line):
    in_func = False
    for i, line in enumerate(lines):
        if line.startswith(f"def {func_name}") or line.startswith(f"class {func_name}"):
            in_func = True
        elif line.startswith("def ") or line.startswith("class "):
            if not line.startswith(f"def {func_name}") and not line.startswith(f"class {func_name}"):
                in_func = False

        if in_func and line_substr in line:
            lines[i] = new_line + "\n"


# 1. SpillerstallSkjerm
replace_line_in_func("SpillerstallSkjerm", "self._SYNLIGE   = 12", "        self._SYNLIGE   = 13")
replace_line_in_func("SpillerstallSkjerm", "pygame.draw.rect(surf, P.BLÅL, (2, 13, W_BASE-4, 9))", "        pygame.draw.rect(surf, P.BLÅL, (4, 26, W_BASE-8, 18))")

replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, \"#\",      (2,   14), f, P.HVIT)", "        tegn_tekst(surf, \"#\",      (4,   28), f, P.HVIT)")
replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, \"NAVN\",   (12,  14), f, P.HVIT)", "        tegn_tekst(surf, \"NAVN\",   (24,  28), f, P.HVIT)")
replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, \"POS\",    (110, 14), f, P.HVIT)", "        tegn_tekst(surf, \"POS\",    (220, 28), f, P.HVIT)")
replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, \"FERD\",   (134, 14), f, P.HVIT)", "        tegn_tekst(surf, \"FERD\",   (268, 28), f, P.HVIT)")
replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, \"KOND\",   (156, 14), f, P.HVIT)", "        tegn_tekst(surf, \"KOND\",   (312, 28), f, P.HVIT)")
replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, \"RYKTE\",  (200, 14), f, P.HVIT)", "        tegn_tekst(surf, \"RYKTE\",  (400, 28), f, P.HVIT)")
replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, \"ALDER\",  (240, 14), f, P.HVIT)", "        tegn_tekst(surf, \"ALDER\",  (480, 28), f, P.HVIT)")
replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, \"KONTRAK\",(275, 14), f, P.HVIT)", "        tegn_tekst(surf, \"KONTRAK\",(550, 28), f, P.HVIT)")

replace_line_in_func("SpillerstallSkjerm", "rad_h  = 13", "        rad_h  = 26")
replace_line_in_func("SpillerstallSkjerm", "y0     = 24", "        y0     = 48")

replace_line_in_func("SpillerstallSkjerm", "er_h = (2 <= mx <= W_BASE-8 and ry <= my < ry+rad_h)", "            er_h = (4 <= mx <= W_BASE-16 and ry <= my < ry+rad_h)")

replace_line_in_func("SpillerstallSkjerm", "pygame.draw.rect(surf, P.BLÅL, (2, ry, W_BASE-10, rad_h-1))", "                pygame.draw.rect(surf, P.BLÅL, (4, ry, W_BASE-20, rad_h-2))")
replace_line_in_func("SpillerstallSkjerm", "pygame.draw.rect(surf, P.GRÅ_MØRK, (2, ry, W_BASE-10, rad_h-1))", "                pygame.draw.rect(surf, P.GRÅ_MØRK, (4, ry, W_BASE-20, rad_h-2))")
replace_line_in_func("SpillerstallSkjerm", "pygame.draw.rect(surf, (34, 34, 48), (2, ry, W_BASE-10, rad_h-1))", "                pygame.draw.rect(surf, (34, 34, 48), (4, ry, W_BASE-20, rad_h-2))")

replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, str(idx+1),  (2,   ry+2), f, P.GRÅ_MØRK)", "            tegn_tekst(surf, str(idx+1),  (4,   ry+4), f, P.GRÅ_MØRK)")
replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, navn[:18],   (12,  ry+2), f, tkf, max_bredde=95)", "            tegn_tekst(surf, navn[:18],   (24,  ry+4), f, tkf, max_bredde=190)")
replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, pos_s,       (110, ry+2), f, P.LYSBLÅ_UI)", "            tegn_tekst(surf, pos_s,       (220, ry+4), f, P.LYSBLÅ_UI)")
replace_line_in_func("SpillerstallSkjerm", "tegn_badge(surf, str(ferd),   (132, ry+1),", "            tegn_badge(surf, str(ferd),   (264, ry+2),")

replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, \"SKADET\", (156, ry+2), f, P.RØD)", "                tegn_tekst(surf, \"SKADET\", (312, ry+4), f, P.RØD)")
replace_line_in_func("SpillerstallSkjerm", "tegn_kondisjon_bar(surf, 156, ry+4, 42, kond)", "                tegn_kondisjon_bar(surf, 312, ry+8, 84, kond)")
replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, f\"{kond:.0f}%\", (200, ry+2), f,", "                tegn_tekst(surf, f\"{kond:.0f}%\", (400, ry+4), f,")

replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, str(rykte),  (240, ry+2), f, P.GULTL)", "            tegn_tekst(surf, str(rykte),  (480, ry+4), f, P.GULTL)")
replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, str(alder),  (260, ry+2), f, P.GRÅ_LYS)", "            tegn_tekst(surf, str(alder),  (520, ry+4), f, P.GRÅ_LYS)")
replace_line_in_func("SpillerstallSkjerm", "tegn_tekst(surf, kontr_s,     (278, ry+2), f, P.CYANL)", "            tegn_tekst(surf, kontr_s,     (556, ry+4), f, P.CYANL)")

replace_line_in_func("SpillerstallSkjerm", "tegn_scrollbar(surf, W_BASE-5, y0, self._SYNLIGE*rad_h,", "        tegn_scrollbar(surf, W_BASE-10, y0, self._SYNLIGE*rad_h,")

replace_line_in_func("SpillerstallSkjerm", "tegn_knapp(surf, (W_BASE//2-35, H_BASE-13, 70, 11), \"TILBAKE\",", "        tegn_knapp(surf, (W_BASE//2-70, H_BASE-26, 140, 22), \"TILBAKE\",")
replace_line_in_func("SpillerstallSkjerm", "hovered=ui.mus_innenfor(((W_BASE//2-35)*SKALA, (H_BASE-13)*SKALA,", "                   hovered=ui.mus_innenfor(((W_BASE//2-70)*SKALA, (H_BASE-26)*SKALA,")
replace_line_in_func("SpillerstallSkjerm", "70*SKALA, 11*SKALA)))", "                                             140*SKALA, 22*SKALA)))")

replace_line_in_func("SpillerstallSkjerm", "rad_h, y0 = 13, 24", "            rad_h, y0 = 26, 48")
replace_line_in_func("SpillerstallSkjerm", "if 2 <= mx <= W_BASE-8 and ry <= my < ry+rad_h:", "                if 4 <= mx <= W_BASE-16 and ry <= my < ry+rad_h:")
replace_line_in_func("SpillerstallSkjerm", "if (my >= (H_BASE-13) and", "            if (my >= (H_BASE-26) and")
replace_line_in_func("SpillerstallSkjerm", "(W_BASE//2-35)*SKALA <= event.pos[0] <= (W_BASE//2+35)*SKALA):", "                    (W_BASE//2-70)*SKALA <= event.pos[0] <= (W_BASE//2+70)*SKALA):")


# 2. TabellSkjerm
replace_line_in_func("TabellSkjerm", "tegn_knapp(surf, (2 + fi*80, 13, 78, 10), tekst, f,", "            tegn_knapp(surf, (4 + fi*160, 26, 156, 20), tekst, f,")
replace_line_in_func("TabellSkjerm", "ui.mus_innenfor(((2+fi*80)*SKALA, 13*SKALA, 78*SKALA, 10*SKALA))))", "                                 ui.mus_innenfor(((4+fi*160)*SKALA, 26*SKALA, 156*SKALA, 20*SKALA))))")

replace_line_in_func("TabellSkjerm", "tegn_knapp(surf, (W_BASE//2-30, H_BASE-13, 60, 11), \"TILBAKE\",", "        tegn_knapp(surf, (W_BASE//2-60, H_BASE-26, 120, 22), \"TILBAKE\",")
replace_line_in_func("TabellSkjerm", "hovered=ui.mus_innenfor(((W_BASE//2-30)*SKALA, (H_BASE-13)*SKALA,", "                   hovered=ui.mus_innenfor(((W_BASE//2-60)*SKALA, (H_BASE-26)*SKALA,")
replace_line_in_func("TabellSkjerm", "60*SKALA, 11*SKALA)))", "                                             120*SKALA, 22*SKALA)))")

replace_line_in_func("TabellSkjerm", "pygame.draw.rect(surf, P.BLÅL, (2, 24, W_BASE-4, 8))", "        pygame.draw.rect(surf, P.BLÅL, (4, 48, W_BASE-8, 16))")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"#\",  (2,  25), f, P.HVIT)", "        tegn_tekst(surf, \"#\",  (4,  50), f, P.HVIT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"KLUBB\", (14, 25), f, P.HVIT)", "        tegn_tekst(surf, \"KLUBB\", (28, 50), f, P.HVIT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"K\",  (142, 25), f, P.HVIT)", "        tegn_tekst(surf, \"K\",  (284, 50), f, P.HVIT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"S\",  (158, 25), f, P.HVIT)", "        tegn_tekst(surf, \"S\",  (316, 50), f, P.HVIT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"U\",  (172, 25), f, P.HVIT)", "        tegn_tekst(surf, \"U\",  (344, 50), f, P.HVIT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"T\",  (186, 25), f, P.HVIT)", "        tegn_tekst(surf, \"T\",  (372, 50), f, P.HVIT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"MF\", (200, 25), f, P.HVIT)", "        tegn_tekst(surf, \"MF\", (400, 50), f, P.HVIT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"MM\", (216, 25), f, P.HVIT)", "        tegn_tekst(surf, \"MM\", (432, 50), f, P.HVIT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"MD\", (232, 25), f, P.HVIT)", "        tegn_tekst(surf, \"MD\", (464, 50), f, P.HVIT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"P\",  (252, 25), f, P.HVIT)", "        tegn_tekst(surf, \"P\",  (504, 50), f, P.HVIT)")

replace_line_in_func("TabellSkjerm", "rad_h = 12", "        rad_h = 24")
replace_line_in_func("TabellSkjerm", "y0    = 34", "        y0    = 68")
replace_line_in_func("TabellSkjerm", "if ry + rad_h > H_BASE - 16:", "            if ry + rad_h > H_BASE - 32:")
replace_line_in_func("TabellSkjerm", "pygame.draw.rect(surf, farge_rad, (2, ry, W_BASE-4, rad_h-1))", "            pygame.draw.rect(surf, farge_rad, (4, ry, W_BASE-8, rad_h-2))")

replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, str(plass),          (2,   ry+2), f, P.GRÅ_LYS)", "            tegn_tekst(surf, str(plass),          (4,   ry+4), f, P.GRÅ_LYS)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, rad.klubb_navn[:18],  (14,  ry+2), f, tkf, max_bredde=125)", "            tegn_tekst(surf, rad.klubb_navn[:18],  (28,  ry+4), f, tkf, max_bredde=250)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, str(rad.kamp),        (142, ry+2), f, P.LYSBLÅ_UI)", "            tegn_tekst(surf, str(rad.kamp),        (284, ry+4), f, P.LYSBLÅ_UI)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, str(rad.seier),       (158, ry+2), f, P.GRØNN)", "            tegn_tekst(surf, str(rad.seier),       (316, ry+4), f, P.GRØNN)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, str(rad.uavgjort),    (172, ry+2), f, P.GULT)", "            tegn_tekst(surf, str(rad.uavgjort),    (344, ry+4), f, P.GULT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, str(rad.tap),         (186, ry+2), f, P.RØD)", "            tegn_tekst(surf, str(rad.tap),         (372, ry+4), f, P.RØD)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, str(rad.mål_for),     (200, ry+2), f, P.KREMHVIT)", "            tegn_tekst(surf, str(rad.mål_for),     (400, ry+4), f, P.KREMHVIT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, str(rad.mål_mot),     (216, ry+2), f, P.KREMHVIT)", "            tegn_tekst(surf, str(rad.mål_mot),     (432, ry+4), f, P.KREMHVIT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, md_s,                 (232, ry+2), f,", "            tegn_tekst(surf, md_s,                 (464, ry+4), f,")
replace_line_in_func("TabellSkjerm", "tegn_badge(surf, str(rad.poeng),        (252, ry+1),", "            tegn_badge(surf, str(rad.poeng),        (504, ry+2),")

replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"Ingen statistikk tilgjengelig ennå.\", (4, 40), f, P.GRÅ_LYS)", "            tegn_tekst(surf, \"Ingen statistikk tilgjengelig ennå.\", (8, 80), f, P.GRÅ_LYS)")

replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"#\",      (2,  25), f, P.HVIT)", "        tegn_tekst(surf, \"#\",      (4,  50), f, P.HVIT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"SPILLER\",(14, 25), f, P.HVIT)", "        tegn_tekst(surf, \"SPILLER\",(28, 50), f, P.HVIT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"K\",      (158,25), f, P.HVIT)", "        tegn_tekst(surf, \"K\",      (316,50), f, P.HVIT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"MÅL\",    (174,25), f, P.HVIT)", "        tegn_tekst(surf, \"MÅL\",    (348,50), f, P.HVIT)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, \"RTG\",    (200,25), f, P.HVIT)", "        tegn_tekst(surf, \"RTG\",    (400,50), f, P.HVIT)")

replace_line_in_func("TabellSkjerm", "ry = 34 + i * 12", "            ry = 68 + i * 24")
replace_line_in_func("TabellSkjerm", "if ry + 12 > H_BASE - 16:", "            if ry + 24 > H_BASE - 32:")
replace_line_in_func("TabellSkjerm", "pygame.draw.rect(surf, farge_rad, (2, ry, W_BASE-4, 11))", "            pygame.draw.rect(surf, farge_rad, (4, ry, W_BASE-8, 22))")

replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, str(i+1),        (2,  ry+2), f, P.GRÅ_LYS)", "            tegn_tekst(surf, str(i+1),        (4,  ry+4), f, P.GRÅ_LYS)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, stat.spiller_navn[:20], (14, ry+2), f, P.KREMHVIT, max_bredde=140)", "            tegn_tekst(surf, stat.spiller_navn[:20], (28, ry+4), f, P.KREMHVIT, max_bredde=280)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, str(stat.kamper), (158,ry+2), f, P.LYSBLÅ_UI)", "            tegn_tekst(surf, str(stat.kamper), (316,ry+4), f, P.LYSBLÅ_UI)")
replace_line_in_func("TabellSkjerm", "tegn_badge(surf, str(stat.mål),    (172,ry+1), P.GRØNN, P.HVIT, f)", "            tegn_badge(surf, str(stat.mål),    (344,ry+2), P.GRØNN, P.HVIT, f)")
replace_line_in_func("TabellSkjerm", "tegn_tekst(surf, f\"{stat.snitt_rating:.1f}\", (200,ry+2), f, P.GULT)", "            tegn_tekst(surf, f\"{stat.snitt_rating:.1f}\", (400,ry+4), f, P.GULT)")

replace_line_in_func("TabellSkjerm", "if 2+fi*80 <= mx <= 80+fi*80 and 13 <= my <= 23:", "                if 4+fi*160 <= mx <= 160+fi*160 and 26 <= my <= 46:")
replace_line_in_func("TabellSkjerm", "if (my >= H_BASE-13 and", "            if (my >= H_BASE-26 and")
replace_line_in_func("TabellSkjerm", "(W_BASE//2-30)*SKALA <= event.pos[0] <= (W_BASE//2+30)*SKALA):", "                    (W_BASE//2-60)*SKALA <= event.pos[0] <= (W_BASE//2+60)*SKALA):")


# 3. KamprapportSkjerm
replace_line_in_func("KamprapportSkjerm", "pygame.draw.rect(surf, (10, 20, 60), (4, 13, W_BASE-8, 22))", "        pygame.draw.rect(surf, (10, 20, 60), (8, 26, W_BASE-16, 44))")
replace_line_in_func("KamprapportSkjerm", "pygame.draw.rect(surf, P.BLÅLL, (4, 13, W_BASE-8, 22), 1)", "        pygame.draw.rect(surf, P.BLÅLL, (8, 26, W_BASE-16, 44), 2)")

replace_line_in_func("KamprapportSkjerm", "surf.blit(t_h, (6, 18))", "        surf.blit(t_h, (12, 36))")
replace_line_in_func("KamprapportSkjerm", "surf.blit(t_b, (W_BASE - t_b.get_width() - 6, 18))", "        surf.blit(t_b, (W_BASE - t_b.get_width() - 12, 36))")
replace_line_in_func("KamprapportSkjerm", "surf.blit(t_s, (W_BASE//2 - t_s.get_width()//2, 16))", "        surf.blit(t_s, (W_BASE//2 - t_s.get_width()//2, 32))")

replace_line_in_func("KamprapportSkjerm", "tegn_knapp(surf, (2 + fi*106, 37, 104, 9), navn, f,", "            tegn_knapp(surf, (4 + fi*212, 74, 208, 18), navn, f,")
replace_line_in_func("KamprapportSkjerm", "ui.mus_innenfor(((2+fi*106)*SKALA, 37*SKALA,", "                                 ui.mus_innenfor(((4+fi*212)*SKALA, 74*SKALA,")
replace_line_in_func("KamprapportSkjerm", "104*SKALA, 9*SKALA))))", "                                                   208*SKALA, 18*SKALA))))")

replace_line_in_func("KamprapportSkjerm", "innhold_y = 48", "        innhold_y = 96")
replace_line_in_func("KamprapportSkjerm", "innhold_h = H_BASE - innhold_y - 14", "        innhold_h = H_BASE - innhold_y - 28")

replace_line_in_func("KamprapportSkjerm", "tegn_knapp(surf, (W_BASE//2-35, H_BASE-13, 70, 11), \"FORTSETT\",", "        tegn_knapp(surf, (W_BASE//2-70, H_BASE-26, 140, 22), \"FORTSETT\",")
replace_line_in_func("KamprapportSkjerm", "hovered=ui.mus_innenfor(((W_BASE//2-35)*SKALA, (H_BASE-13)*SKALA,", "                   hovered=ui.mus_innenfor(((W_BASE//2-70)*SKALA, (H_BASE-26)*SKALA,")
replace_line_in_func("KamprapportSkjerm", "70*SKALA, 11*SKALA)))", "                                             140*SKALA, 22*SKALA)))")

replace_line_in_func("KamprapportSkjerm", "synlige   = h // 10", "        synlige   = h // 20")
replace_line_in_func("KamprapportSkjerm", "ry  = y0 + i * 10", "            ry  = y0 + i * 20")
replace_line_in_func("KamprapportSkjerm", "tegn_tekst(surf, f\"{hend.minutt:>3}'  [{lag_s}]  {navn[:16]}{detalj[:20]}\",", "            tegn_tekst(surf, f\"{hend.minutt:>3}'  [{lag_s}]  {navn[:16]}{detalj[:20]}\",")
replace_line_in_func("KamprapportSkjerm", "(4, ry), f, farge)", "                       (8, ry), f, farge)")
replace_line_in_func("KamprapportSkjerm", "tegn_tekst(surf, \"Ingen hendelser registrert.\", (4, y0+10), f, P.GRÅ_MØRK)", "            tegn_tekst(surf, \"Ingen hendelser registrert.\", (8, y0+20), f, P.GRÅ_MØRK)")
replace_line_in_func("KamprapportSkjerm", "tegn_scrollbar(surf, W_BASE-6, y0, h, len(hendelser), synlige, self._scroll)", "        tegn_scrollbar(surf, W_BASE-12, y0, h, len(hendelser), synlige, self._scroll)")

replace_line_in_func("KamprapportSkjerm", "pygame.draw.rect(surf, (28,28,44), (4, ry, W_BASE-8, 9))", "            pygame.draw.rect(surf, (28,28,44), (8, ry, W_BASE-16, 18))")
replace_line_in_func("KamprapportSkjerm", "tegn_tekst(surf, str(v_h), (midtre-40, ry+1), f, P.LYSBLÅ_UI)", "            tegn_tekst(surf, str(v_h), (midtre-80, ry+2), f, P.LYSBLÅ_UI)")
replace_line_in_func("KamprapportSkjerm", "tegn_tekst(surf, label,    (midtre - Fonter.liten.size(label)[0]//2, ry+1),", "            tegn_tekst(surf, label,    (midtre - Fonter.liten.size(label)[0]//2, ry+2),")
replace_line_in_func("KamprapportSkjerm", "tegn_tekst(surf, str(v_b), (midtre+30, ry+1), f, P.LYSBLÅ_UI)", "            tegn_tekst(surf, str(v_b), (midtre+60, ry+2), f, P.LYSBLÅ_UI)")

replace_line_in_func("KamprapportSkjerm", "rad(\"Ballbesittelse\",  f\"{bes_h}%\",  f\"{bes_b}%\",  y0+2)", "        rad(\"Ballbesittelse\",  f\"{bes_h}%\",  f\"{bes_b}%\",  y0+4)")
replace_line_in_func("KamprapportSkjerm", "rad(\"Sjanser\",         s.sjanser_hjemme,    s.sjanser_borte,    y0+13)", "        rad(\"Sjanser\",         s.sjanser_hjemme,    s.sjanser_borte,    y0+26)")
replace_line_in_func("KamprapportSkjerm", "rad(\"Skudd\",           s.skudd_hjemme,      s.skudd_borte,      y0+24)", "        rad(\"Skudd\",           s.skudd_hjemme,      s.skudd_borte,      y0+48)")
replace_line_in_func("KamprapportSkjerm", "rad(\"Skudd på mål\",    s.skudd_paa_maal_hjemme, s.skudd_paa_maal_borte, y0+35)", "        rad(\"Skudd på mål\",    s.skudd_paa_maal_hjemme, s.skudd_paa_maal_borte, y0+70)")
replace_line_in_func("KamprapportSkjerm", "rad(\"Gule kort\",       s.gule_kort_hjemme,  s.gule_kort_borte,  y0+46)", "        rad(\"Gule kort\",       s.gule_kort_hjemme,  s.gule_kort_borte,  y0+92)")
replace_line_in_func("KamprapportSkjerm", "rad(\"Røde kort\",       s.røde_kort_hjemme,  s.røde_kort_borte,  y0+57)", "        rad(\"Røde kort\",       s.røde_kort_hjemme,  s.røde_kort_borte,  y0+114)")

replace_line_in_func("KamprapportSkjerm", "pygame.draw.rect(surf, P.BLÅL, (4, y0+70, W_BASE-8, 8))", "        pygame.draw.rect(surf, P.BLÅL, (8, y0+140, W_BASE-16, 16))")
replace_line_in_func("KamprapportSkjerm", "surf.blit(t_h, (6, y0+71))", "        surf.blit(t_h, (12, y0+142))")
replace_line_in_func("KamprapportSkjerm", "surf.blit(t_b, (W_BASE - t_b.get_width() - 6, y0+71))", "        surf.blit(t_b, (W_BASE - t_b.get_width() - 12, y0+142))")

replace_line_in_func("KamprapportSkjerm", "synlige = h // 10", "        synlige = h // 20")
replace_line_in_func("KamprapportSkjerm", "pygame.draw.rect(surf, P.BLÅL, (2, y0, W_BASE-4, 8))", "        pygame.draw.rect(surf, P.BLÅL, (4, y0, W_BASE-8, 16))")
replace_line_in_func("KamprapportSkjerm", "tegn_tekst(surf, \"SPILLER\",  (4,  y0+1), f, P.HVIT)", "        tegn_tekst(surf, \"SPILLER\",  (8,  y0+2), f, P.HVIT)")
replace_line_in_func("KamprapportSkjerm", "tegn_tekst(surf, \"LAG\",      (150, y0+1), f, P.HVIT)", "        tegn_tekst(surf, \"LAG\",      (300, y0+2), f, P.HVIT)")
replace_line_in_func("KamprapportSkjerm", "tegn_tekst(surf, \"RATING\",   (190, y0+1), f, P.HVIT)", "        tegn_tekst(surf, \"RATING\",   (380, y0+2), f, P.HVIT)")

replace_line_in_func("KamprapportSkjerm", "ry     = y0 + 9 + i * 10", "            ry     = y0 + 18 + i * 20")
replace_line_in_func("KamprapportSkjerm", "pygame.draw.rect(surf, farge_rad, (2, ry, W_BASE-4, 9))", "            pygame.draw.rect(surf, farge_rad, (4, ry, W_BASE-8, 18))")

replace_line_in_func("KamprapportSkjerm", "tegn_tekst(surf, navn[:20], (4,  ry+1), f, P.KREMHVIT)", "            tegn_tekst(surf, navn[:20], (8,  ry+2), f, P.KREMHVIT)")
replace_line_in_func("KamprapportSkjerm", "tegn_tekst(surf, lag,       (150,ry+1), f, P.LYSBLÅ_UI)", "            tegn_tekst(surf, lag,       (300,ry+2), f, P.LYSBLÅ_UI)")
replace_line_in_func("KamprapportSkjerm", "tegn_badge(surf, f\"{rating:.1f}\", (190, ry+1), rtg_farge, P.SVART, f)", "            tegn_badge(surf, f\"{rating:.1f}\", (380, ry+2), rtg_farge, P.SVART, f)")

replace_line_in_func("KamprapportSkjerm", "tegn_scrollbar(surf, W_BASE-6, y0+9, h-9, len(alle), synlige, self._scroll)", "        tegn_scrollbar(surf, W_BASE-12, y0+18, h-18, len(alle), synlige, self._scroll)")

replace_line_in_func("KamprapportSkjerm", "if 2+fi*106 <= mx <= 106+fi*106 and 37 <= my <= 46:", "                if 4+fi*212 <= mx <= 212+fi*212 and 74 <= my <= 92:")
replace_line_in_func("KamprapportSkjerm", "if my >= H_BASE-13:", "            if my >= H_BASE-26:")

# 4. InfoSkjerm
replace_line_in_func("InfoSkjerm", "pygame.draw.rect(surf, (10, 18, 50, 200), (10, 20, W_BASE-20, 30))", "        pygame.draw.rect(surf, (10, 18, 50, 200), (20, 40, W_BASE-40, 60))")
replace_line_in_func("InfoSkjerm", "pygame.draw.rect(surf, P.BLÅLL, (10, 20, W_BASE-20, 30), 2)", "        pygame.draw.rect(surf, P.BLÅLL, (20, 40, W_BASE-40, 60), 4)")
replace_line_in_func("InfoSkjerm", "surf.blit(t, (W_BASE//2 - t.get_width()//2, 27))", "        surf.blit(t, (W_BASE//2 - t.get_width()//2, 54))")

replace_line_in_func("InfoSkjerm", "tegn_tekst(surf, linje, (14, 60 + i*12), f, P.KREMHVIT)", "            tegn_tekst(surf, linje, (28, 120 + i*24), f, P.KREMHVIT)")

replace_line_in_func("InfoSkjerm", "tegn_knapp(surf, (W_BASE//2-40, H_BASE-20, 80, 14), \"FORTSETT →\",", "        tegn_knapp(surf, (W_BASE//2-80, H_BASE-40, 160, 28), \"FORTSETT →\",")
replace_line_in_func("InfoSkjerm", "hovered=ui.mus_innenfor(((W_BASE//2-40)*SKALA, (H_BASE-20)*SKALA,", "                   hovered=ui.mus_innenfor(((W_BASE//2-80)*SKALA, (H_BASE-40)*SKALA,")
replace_line_in_func("InfoSkjerm", "80*SKALA, 14*SKALA)))", "                                             160*SKALA, 28*SKALA)))")

replace_line_in_func("InfoSkjerm", "if H_BASE-20 <= my <= H_BASE-6 and W_BASE//2-40 <= mx <= W_BASE//2+40:", "            if H_BASE-40 <= my <= H_BASE-12 and W_BASE//2-80 <= mx <= W_BASE//2+80:")


# 5. AndreResultaterSkjerm
replace_line_in_func("AndreResultaterSkjerm", "ry = 18 + i * 12", "            ry = 36 + i * 24")
replace_line_in_func("AndreResultaterSkjerm", "pygame.draw.rect(surf, farge_rad, (4, ry, W_BASE-8, 11))", "            pygame.draw.rect(surf, farge_rad, (8, ry, W_BASE-16, 22))")
replace_line_in_func("AndreResultaterSkjerm", "tegn_tekst(surf, h[:16],   (6,   ry+2), f, P.KREMHVIT)", "            tegn_tekst(surf, h[:16],   (12,   ry+4), f, P.KREMHVIT)")
replace_line_in_func("AndreResultaterSkjerm", "tegn_tekst(surf, score,    (W_BASE//2 - 12, ry+2), fb, P.GULT)", "            tegn_tekst(surf, score,    (W_BASE//2 - 24, ry+4), fb, P.GULT)")
replace_line_in_func("AndreResultaterSkjerm", "surf.blit(t_b, (W_BASE - t_b.get_width() - 6, ry+2))", "            surf.blit(t_b, (W_BASE - t_b.get_width() - 12, ry+4))")

replace_line_in_func("AndreResultaterSkjerm", "tegn_knapp(surf, (W_BASE//2-30, H_BASE-14, 60, 12), \"OK →\",", "        tegn_knapp(surf, (W_BASE//2-60, H_BASE-28, 120, 24), \"OK →\",")
replace_line_in_func("AndreResultaterSkjerm", "hovered=ui.mus_innenfor(((W_BASE//2-30)*SKALA, (H_BASE-14)*SKALA,", "                   hovered=ui.mus_innenfor(((W_BASE//2-60)*SKALA, (H_BASE-28)*SKALA,")
replace_line_in_func("AndreResultaterSkjerm", "60*SKALA, 12*SKALA)))", "                                             120*SKALA, 24*SKALA)))")


# 6. SesongsSluttSkjerm
replace_line_in_func("SesongsSluttSkjerm", "surf.blit(t1, (W_BASE//2 - t1.get_width()//2, 14))", "        surf.blit(t1, (W_BASE//2 - t1.get_width()//2, 28))")
replace_line_in_func("SesongsSluttSkjerm", "pygame.draw.rect(surf, P.BLÅL, (0, 30, W_BASE, 1))", "        pygame.draw.rect(surf, P.BLÅL, (0, 60, W_BASE, 2))")

replace_line_in_func("SesongsSluttSkjerm", "tegn_tekst(surf, self.klubb_navn, (8, 36), f, P.KREMHVIT)", "        tegn_tekst(surf, self.klubb_navn, (16, 72), f, P.KREMHVIT)")

replace_line_in_func("SesongsSluttSkjerm", "ry = 50 + i*12", "            ry = 100 + i*24")
replace_line_in_func("SesongsSluttSkjerm", "tegn_tekst(surf, label, (8, ry), fs, P.GRÅ_LYS)", "            tegn_tekst(surf, label, (16, ry), fs, P.GRÅ_LYS)")
replace_line_in_func("SesongsSluttSkjerm", "tegn_tekst(surf, verdi, (130, ry), f, P.GULT)", "            tegn_tekst(surf, verdi, (260, ry), f, P.GULT)")

replace_line_in_func("SesongsSluttSkjerm", "pygame.draw.rect(surf, (10, 18, 50), (4, 118, W_BASE-8, 16))", "            pygame.draw.rect(surf, (10, 18, 50), (8, 236, W_BASE-16, 32))")
replace_line_in_func("SesongsSluttSkjerm", "tegn_tekst(surf, f\"ENDELIG TABELLPLASS: {plass}. PLASS\",", "            tegn_tekst(surf, f\"ENDELIG TABELLPLASS: {plass}. PLASS\",")
replace_line_in_func("SesongsSluttSkjerm", "(8, 122), f, P.CYANL)", "                        (16, 244), f, P.CYANL)")

replace_line_in_func("SesongsSluttSkjerm", "tegn_knapp(surf, (W_BASE//2-40, H_BASE-20, 80, 14), \"AVSLUTT\",", "        tegn_knapp(surf, (W_BASE//2-80, H_BASE-40, 160, 28), \"AVSLUTT\",")
replace_line_in_func("SesongsSluttSkjerm", "hovered=ui.mus_innenfor(((W_BASE//2-40)*SKALA, (H_BASE-20)*SKALA,", "                   hovered=ui.mus_innenfor(((W_BASE//2-80)*SKALA, (H_BASE-40)*SKALA,")
replace_line_in_func("SesongsSluttSkjerm", "80*SKALA, 14*SKALA)))", "                                             160*SKALA, 28*SKALA)))")

replace_line_in_func("SesongsSluttSkjerm", "if H_BASE-20 <= my <= H_BASE-6:", "            if H_BASE-40 <= my <= H_BASE-12:")


with open("ui_pygame.py", "w") as f:
    f.writelines(lines)
