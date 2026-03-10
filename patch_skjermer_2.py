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


# 1. KampdagSkjerm
replace_line_in_func("KampdagSkjerm", "pygame.draw.rect(surf, P.NAVY, (4, 14, W_BASE-8, 30))", "        pygame.draw.rect(surf, P.NAVY, (8, 28, W_BASE-16, 60))")
replace_line_in_func("KampdagSkjerm", "pygame.draw.rect(surf, P.BLÅL, (4, 14, W_BASE-8, 30), 1)", "        pygame.draw.rect(surf, P.BLÅL, (8, 28, W_BASE-16, 60), 2)")

replace_line_in_func("KampdagSkjerm", "surf.blit(t_h,  (8,  22))", "        surf.blit(t_h,  (16,  44))")
replace_line_in_func("KampdagSkjerm", "surf.blit(t_vs, (W_BASE//2 - t_vs.get_width()//2, 22))", "        surf.blit(t_vs, (W_BASE//2 - t_vs.get_width()//2, 44))")
replace_line_in_func("KampdagSkjerm", "surf.blit(t_b,  (W_BASE - t_b.get_width() - 8, 22))", "        surf.blit(t_b,  (W_BASE - t_b.get_width() - 16, 44))")

replace_line_in_func("KampdagSkjerm", "tegn_linje_h(surf, P.BLÅL, 4, 44, W_BASE-8)", "        tegn_linje_h(surf, P.BLÅL, 8, 88, W_BASE-16)")

replace_line_in_func("KampdagSkjerm", "meny_y = 52", "        meny_y = 104")
replace_line_in_func("KampdagSkjerm", "knapp_h = 18", "        knapp_h = 36")

replace_line_in_func("KampdagSkjerm", "er_hover = (10 <= mx <= W_BASE-10 and ry <= my < ry+knapp_h)", "            er_hover = (20 <= mx <= W_BASE-20 and ry <= my < ry+knapp_h)")
replace_line_in_func("KampdagSkjerm", "tegn_knapp(surf, (10, ry, W_BASE-20, knapp_h), tekst,", "            tegn_knapp(surf, (20, ry, W_BASE-40, knapp_h), tekst,")

replace_line_in_func("KampdagSkjerm", "tegn_linje_h(surf, P.GRÅ_MØRK, 4, H_BASE-22, W_BASE-8)", "        tegn_linje_h(surf, P.GRÅ_MØRK, 8, H_BASE-44, W_BASE-16)")
replace_line_in_func("KampdagSkjerm", "tegn_tekst(surf, \"ESC = INGEN KAMP DENNE RUNDEN\", (4, H_BASE-20), fs, P.GRÅ_MØRK)", "        tegn_tekst(surf, \"ESC = INGEN KAMP DENNE RUNDEN\", (8, H_BASE-40), fs, P.GRÅ_MØRK)")

replace_line_in_func("KampdagSkjerm", "meny_y   = 52", "        meny_y   = 104")
replace_line_in_func("KampdagSkjerm", "knapp_h  = 18", "        knapp_h  = 36")

replace_line_in_func("KampdagSkjerm", "if 10 <= mx <= W_BASE-10 and ry <= my < ry+knapp_h:", "                if 20 <= mx <= W_BASE-20 and ry <= my < ry+knapp_h:")


# 2. LaguttakSkjerm
replace_line_in_func("LaguttakSkjerm", "rad_h = 13", "        rad_h = 26")
replace_line_in_func("LaguttakSkjerm", "y0    = 14", "        y0    = 28")
replace_line_in_func("LaguttakSkjerm", "x0    = 2", "        x0    = 4")

replace_line_in_func("LaguttakSkjerm", "pygame.draw.rect(surf, farge, (x0, ry, 150, rad_h-1))", "            pygame.draw.rect(surf, farge, (x0, ry, 300, rad_h-2))")
replace_line_in_func("LaguttakSkjerm", "tegn_tekst(surf, f\"{i+1:>2}\", (x0+1, ry+2), f, P.GRÅ_LYS)", "            tegn_tekst(surf, f\"{i+1:>2}\", (x0+2, ry+4), f, P.GRÅ_LYS)")
replace_line_in_func("LaguttakSkjerm", "tegn_tekst(surf, navn[:14],   (x0+14, ry+2), f, tkf, max_bredde=74)", "            tegn_tekst(surf, navn[:14],   (x0+28, ry+4), f, tkf, max_bredde=148)")
replace_line_in_func("LaguttakSkjerm", "tegn_tekst(surf, pos_s,       (x0+90, ry+2), f, P.LYSBLÅ_UI)", "            tegn_tekst(surf, pos_s,       (x0+180, ry+4), f, P.LYSBLÅ_UI)")
replace_line_in_func("LaguttakSkjerm", "tegn_tekst(surf, str(ferd),   (x0+114, ry+2), f, P.GULT)", "            tegn_tekst(surf, str(ferd),   (x0+228, ry+4), f, P.GULT)")
replace_line_in_func("LaguttakSkjerm", "tegn_kondisjon_bar(surf, x0+126, ry+4, 22, kond, skadet)", "            tegn_kondisjon_bar(surf, x0+252, ry+8, 44, kond, skadet)")

replace_line_in_func("LaguttakSkjerm", "benk_y0 = y0 + 11 * rad_h + 4", "        benk_y0 = y0 + 11 * rad_h + 8")
replace_line_in_func("LaguttakSkjerm", "pygame.draw.rect(surf, P.BLÅL, (x0, benk_y0-1, 150, 8))", "        pygame.draw.rect(surf, P.BLÅL, (x0, benk_y0-2, 300, 16))")
replace_line_in_func("LaguttakSkjerm", "tegn_tekst(surf, \"── BENK ──\", (x0+2, benk_y0), Fonter.liten, P.HVIT)", "        tegn_tekst(surf, \"── BENK ──\", (x0+4, benk_y0), Fonter.liten, P.HVIT)")
replace_line_in_func("LaguttakSkjerm", "benk_y0 += 9", "        benk_y0 += 18")

replace_line_in_func("LaguttakSkjerm", "ry     = benk_y0 + j * (rad_h - 2)", "            ry     = benk_y0 + j * (rad_h - 4)")
replace_line_in_func("LaguttakSkjerm", "pygame.draw.rect(surf, farge, (x0, ry, 150, rad_h-2))", "            pygame.draw.rect(surf, farge, (x0, ry, 300, rad_h-4))")

replace_line_in_func("LaguttakSkjerm", "tegn_tekst(surf, f\"S{j+1}\", (x0+1, ry+1), f, P.GRÅ_MØRK)", "            tegn_tekst(surf, f\"S{j+1}\", (x0+2, ry+2), f, P.GRÅ_MØRK)")
replace_line_in_func("LaguttakSkjerm", "tegn_tekst(surf, navn[:14], (x0+14, ry+1), f, tkf, max_bredde=74)", "            tegn_tekst(surf, navn[:14], (x0+28, ry+2), f, tkf, max_bredde=148)")
replace_line_in_func("LaguttakSkjerm", "tegn_tekst(surf, pos_s,     (x0+90, ry+1), f, P.LYSBLÅ_UI)", "            tegn_tekst(surf, pos_s,     (x0+180, ry+2), f, P.LYSBLÅ_UI)")
replace_line_in_func("LaguttakSkjerm", "tegn_tekst(surf, str(ferd), (x0+114, ry+1), f, P.GULT)", "            tegn_tekst(surf, str(ferd), (x0+228, ry+2), f, P.GULT)")
replace_line_in_func("LaguttakSkjerm", "tegn_kondisjon_bar(surf, x0+126, ry+3, 22, kond, skadet)", "            tegn_kondisjon_bar(surf, x0+252, ry+6, 44, kond, skadet)")

replace_line_in_func("LaguttakSkjerm", "bane_rect = (156, 14, 162, 150)", "        bane_rect = (312, 28, 324, 300)")

replace_line_in_func("LaguttakSkjerm", "fv_y = 170", "        fv_y = 340")
replace_line_in_func("LaguttakSkjerm", "pygame.draw.rect(surf, P.NAVY, (156, fv_y, 162, 16))", "        pygame.draw.rect(surf, P.NAVY, (312, fv_y, 324, 32))")
replace_line_in_func("LaguttakSkjerm", "pygame.draw.rect(surf, P.BLÅL, (156, fv_y, 162, 16), 1)", "        pygame.draw.rect(surf, P.BLÅL, (312, fv_y, 324, 32), 2)")
replace_line_in_func("LaguttakSkjerm", "tegn_tekst(surf, \"◄\", (158, fv_y+3), fb, P.GULT)", "        tegn_tekst(surf, \"◄\", (316, fv_y+6), fb, P.GULT)")
replace_line_in_func("LaguttakSkjerm", "surf.blit(t_f, (156 + 82 - t_f.get_width()//2, fv_y+3))", "        surf.blit(t_f, (312 + 164 - t_f.get_width()//2, fv_y+6))")
replace_line_in_func("LaguttakSkjerm", "tegn_tekst(surf, \"►\", (306, fv_y+3), fb, P.GULT)", "        tegn_tekst(surf, \"►\", (612, fv_y+6), fb, P.GULT)")

replace_line_in_func("LaguttakSkjerm", "tegn_knapp(surf, (156, H_BASE-14, 162, 12), \"FERDIG / TILBAKE\",", "        tegn_knapp(surf, (312, H_BASE-28, 324, 24), \"FERDIG / TILBAKE\",")
replace_line_in_func("LaguttakSkjerm", "hovered=ui.mus_innenfor((156*SKALA, (H_BASE-14)*SKALA,", "                   hovered=ui.mus_innenfor((312*SKALA, (H_BASE-28)*SKALA,")
replace_line_in_func("LaguttakSkjerm", "162*SKALA, 12*SKALA)))", "                                            324*SKALA, 24*SKALA)))")

replace_line_in_func("LaguttakSkjerm", "pygame.draw.rect(surf, P.GULT, (x0, 0, 150, 1))  # gul toppstripel", "            pygame.draw.rect(surf, P.GULT, (x0, 0, 300, 2))  # gul toppstripel")

replace_line_in_func("LaguttakSkjerm", "rad_h  = 13", "        rad_h  = 26")
replace_line_in_func("LaguttakSkjerm", "y0     = 14", "        y0     = 28")
replace_line_in_func("LaguttakSkjerm", "benk_y0 = y0 + 11 * rad_h + 4 + 9", "        benk_y0 = y0 + 11 * rad_h + 8 + 18")

replace_line_in_func("LaguttakSkjerm", "if 170 <= my <= 186:", "            if 340 <= my <= 372:")
replace_line_in_func("LaguttakSkjerm", "if 156 <= mx <= 170:  # Venstre pil", "                if 312 <= mx <= 340:  # Venstre pil")
replace_line_in_func("LaguttakSkjerm", "if 305 <= mx <= 320:  # Høyre pil", "                if 610 <= mx <= 640:  # Høyre pil")
replace_line_in_func("LaguttakSkjerm", "if my >= H_BASE-14 and 156 <= mx <= 318:", "            if my >= H_BASE-28 and 312 <= mx <= 636:")
replace_line_in_func("LaguttakSkjerm", "if mx <= 152:", "            if mx <= 304:")
replace_line_in_func("LaguttakSkjerm", "ry = benk_y0 + j * (rad_h - 2)", "                    ry = benk_y0 + j * (rad_h - 4)")
replace_line_in_func("LaguttakSkjerm", "if ry <= my < ry + rad_h-2:", "                    if ry <= my < ry + rad_h-4:")


with open("ui_pygame.py", "w") as f:
    f.writelines(lines)
