import re

def multiply_matches(pattern, repl_func, text):
    return re.sub(pattern, repl_func, text)

# For _tegn_topplinje:
def repl_topplinje(m):
    return m.group(0).replace("12", "24").replace("11", "22").replace("2, 2", "4, 4").replace("2)", "4)")

# We should probably do it by replacing the whole function or specific lines. Let's just write replacing functions for specific blocks.

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

# 1. _tegn_topplinje
replace_line_in_func("_tegn_topplinje", "pygame.draw.rect(surf, P.NAVY, (0, 0, W_BASE, 12))", "    pygame.draw.rect(surf, P.NAVY, (0, 0, W_BASE, 24))")
replace_line_in_func("_tegn_topplinje", "pygame.draw.rect(surf, P.BLÅL, (0, 11, W_BASE, 1))", "    pygame.draw.rect(surf, P.BLÅL, (0, 23, W_BASE, 2))")
replace_line_in_func("_tegn_topplinje", "tegn_tekst(surf, venstre, (2, 2)", "    tegn_tekst(surf, venstre, (4, 4), font, P.GULT)")
replace_line_in_func("_tegn_topplinje", "surf.blit(mid_t, (W_BASE//2 - mid_t.get_width()//2, 2))", "    surf.blit(mid_t, (W_BASE//2 - mid_t.get_width()//2, 4))")
replace_line_in_func("_tegn_topplinje", "surf.blit(høyre_t, (W_BASE - høyre_t.get_width() - 2, 2))", "    surf.blit(høyre_t, (W_BASE - høyre_t.get_width() - 4, 4))")

# 2. _tegn_bunnlinje
replace_line_in_func("_tegn_bunnlinje", "pygame.draw.rect(surf, P.NAVY, (0, H_BASE-11, W_BASE, 11))", "    pygame.draw.rect(surf, P.NAVY, (0, H_BASE-22, W_BASE, 22))")
replace_line_in_func("_tegn_bunnlinje", "pygame.draw.rect(surf, P.BLÅL, (0, H_BASE-12, W_BASE, 1))", "    pygame.draw.rect(surf, P.BLÅL, (0, H_BASE-24, W_BASE, 2))")
replace_line_in_func("_tegn_bunnlinje", "tegn_tekst(surf, tekst, (3, H_BASE-9)", "    tegn_tekst(surf, tekst, (6, H_BASE-18), font, P.GRÅ_LYS)")

# 3. _tegn_bakgrunn
replace_line_in_func("_tegn_bakgrunn", "for y in range(0, H_BASE, 8):", "    for y in range(0, H_BASE, 16):")

# 4. HovedmenySkjerm
replace_line_in_func("HovedmenySkjerm", "tegn_bane(surf, (0, H_BASE-40, W_BASE, 40)", "        tegn_bane(surf, (0, H_BASE-80, W_BASE, 80), P.GRØNN, P.HVIT)")
replace_line_in_func("HovedmenySkjerm", "logo_rect = (20, 18, W_BASE-40, 70)", "        logo_rect = (40, 36, W_BASE-80, 140)")
replace_line_in_func("HovedmenySkjerm", "surf.blit(t1, (logo_rect[0] + (logo_rect[2]-t1.get_width())//2, 26))", "        surf.blit(t1, (logo_rect[0] + (logo_rect[2]-t1.get_width())//2, 52))")
replace_line_in_func("HovedmenySkjerm", "surf.blit(t2, (logo_rect[0] + (logo_rect[2]-t2.get_width())//2, 44))", "        surf.blit(t2, (logo_rect[0] + (logo_rect[2]-t2.get_width())//2, 88))")
replace_line_in_func("HovedmenySkjerm", "surf.blit(t3, (logo_rect[0] + (logo_rect[2]-t3.get_width())//2, 64))", "        surf.blit(t3, (logo_rect[0] + (logo_rect[2]-t3.get_width())//2, 128))")
replace_line_in_func("HovedmenySkjerm", "surf.blit(t4, ((W_BASE - t4.get_width())//2, 100))", "            surf.blit(t4, ((W_BASE - t4.get_width())//2, 200))")
replace_line_in_func("HovedmenySkjerm", "surf.blit(tv, ((W_BASE - tv.get_width())//2, H_BASE-50))", "        surf.blit(tv, ((W_BASE - tv.get_width())//2, H_BASE-100))")

replace_line_in_func("HovedmenySkjerm", "tegn_knapp(surf, (60, 118, 80, 14), \"START\"", "        tegn_knapp(surf, (120, 236, 160, 28), \"START\", Fonter.normal,")
replace_line_in_func("HovedmenySkjerm", "hovered=ui.mus_innenfor((60*SKALA, 118*SKALA, 80*SKALA, 14*SKALA)))", "                   hovered=ui.mus_innenfor((120*SKALA, 236*SKALA, 160*SKALA, 28*SKALA)))")
replace_line_in_func("HovedmenySkjerm", "tegn_knapp(surf, (180, 118, 80, 14), \"AVSLUTT\"", "        tegn_knapp(surf, (360, 236, 160, 28), \"AVSLUTT\", Fonter.normal,")
replace_line_in_func("HovedmenySkjerm", "hovered=ui.mus_innenfor((180*SKALA, 118*SKALA, 80*SKALA, 14*SKALA)))", "                   hovered=ui.mus_innenfor((360*SKALA, 236*SKALA, 160*SKALA, 28*SKALA)))")

replace_line_in_func("HovedmenySkjerm", "if 60 <= mx <= 140 and 118 <= my <= 132:", "            if 120 <= mx <= 280 and 236 <= my <= 264:")
replace_line_in_func("HovedmenySkjerm", "elif 180 <= mx <= 260 and 118 <= my <= 132:", "            elif 360 <= mx <= 520 and 236 <= my <= 264:")


# 5. VelgKlubbSkjerm
replace_line_in_func("VelgKlubbSkjerm", "self._SYNLIGE = 10", "        self._SYNLIGE = 11")

replace_line_in_func("VelgKlubbSkjerm", "pygame.draw.rect(surf, P.BLÅL, (2, 13, W_BASE-4, 10))", "        pygame.draw.rect(surf, P.BLÅL, (4, 26, W_BASE-8, 20))")
replace_line_in_func("VelgKlubbSkjerm", "tegn_tekst(surf, \"KLUBB\",        (4,   14), f, P.HVIT)", "        tegn_tekst(surf, \"KLUBB\",        (8,   28), f, P.HVIT)")
replace_line_in_func("VelgKlubbSkjerm", "tegn_tekst(surf, \"STJERNER\",     (130, 14), f, P.HVIT)", "        tegn_tekst(surf, \"STJERNER\",     (260, 28), f, P.HVIT)")
replace_line_in_func("VelgKlubbSkjerm", "tegn_tekst(surf, \"STADION\",      (200, 14), f, P.HVIT)", "        tegn_tekst(surf, \"STADION\",      (400, 28), f, P.HVIT)")

replace_line_in_func("VelgKlubbSkjerm", "rad_h    = 14", "        rad_h    = 28")
replace_line_in_func("VelgKlubbSkjerm", "y0       = 25", "        y0       = 50")

replace_line_in_func("VelgKlubbSkjerm", "er_hover  = (4 <= mx <= W_BASE-8 and ry <= my < ry+rad_h)", "            er_hover  = (8 <= mx <= W_BASE-16 and ry <= my < ry+rad_h)")
replace_line_in_func("VelgKlubbSkjerm", "pygame.draw.rect(surf, P.BLÅL, (4, ry, W_BASE-16, rad_h-1))", "                pygame.draw.rect(surf, P.BLÅL, (8, ry, W_BASE-32, rad_h-2))")
replace_line_in_func("VelgKlubbSkjerm", "pygame.draw.rect(surf, P.GRÅ_MØRK, (4, ry, W_BASE-16, rad_h-1))", "                pygame.draw.rect(surf, P.GRÅ_MØRK, (8, ry, W_BASE-32, rad_h-2))")
replace_line_in_func("VelgKlubbSkjerm", "pygame.draw.rect(surf, (38, 38, 52), (4, ry, W_BASE-16, rad_h-1))", "                pygame.draw.rect(surf, (38, 38, 52), (8, ry, W_BASE-32, rad_h-2))")

replace_line_in_func("VelgKlubbSkjerm", "tegn_tekst(surf, navn[:22],   (6,   ry+2), f, tkfarge, max_bredde=120)", "            tegn_tekst(surf, navn[:22],   (12,   ry+4), f, tkfarge, max_bredde=240)")
replace_line_in_func("VelgKlubbSkjerm", "tegn_tekst(surf, stjerner_str,(132,  ry+2), f, P.GULT)", "            tegn_tekst(surf, stjerner_str,(264,  ry+4), f, P.GULT)")
replace_line_in_func("VelgKlubbSkjerm", "tegn_tekst(surf, f\"{kap:,}\",  (200, ry+2), f, P.LYSBLÅ_UI)", "            tegn_tekst(surf, f\"{kap:,}\",  (400, ry+4), f, P.LYSBLÅ_UI)")

replace_line_in_func("VelgKlubbSkjerm", "tegn_scrollbar(surf, W_BASE-7, y0, synlige*rad_h,", "        tegn_scrollbar(surf, W_BASE-14, y0, synlige*rad_h,")

replace_line_in_func("VelgKlubbSkjerm", "tegn_knapp(surf, (W_BASE//2-40, H_BASE-24, 80, 13), \"VELG KLUBB\",", "        tegn_knapp(surf, (W_BASE//2-80, H_BASE-48, 160, 26), \"VELG KLUBB\",")
replace_line_in_func("VelgKlubbSkjerm", "hovered=aktiv and ui.mus_innenfor(", "                   hovered=aktiv and ui.mus_innenfor(")
replace_line_in_func("VelgKlubbSkjerm", "((W_BASE//2-40)*SKALA, (H_BASE-24)*SKALA, 80*SKALA, 13*SKALA)))", "                       ((W_BASE//2-80)*SKALA, (H_BASE-48)*SKALA, 160*SKALA, 26*SKALA)))")

replace_line_in_func("VelgKlubbSkjerm", "rad_h, y0 = 14, 25", "            rad_h, y0 = 28, 50")
replace_line_in_func("VelgKlubbSkjerm", "if 4 <= mx <= W_BASE-8 and ry <= my < ry+rad_h:", "                if 8 <= mx <= W_BASE-16 and ry <= my < ry+rad_h:")
replace_line_in_func("VelgKlubbSkjerm", "(W_BASE//2-40)*SKALA <= event.pos[0] <= (W_BASE//2+40)*SKALA and", "                    (W_BASE//2-80)*SKALA <= event.pos[0] <= (W_BASE//2+80)*SKALA and")
replace_line_in_func("VelgKlubbSkjerm", "(H_BASE-24)*SKALA  <= event.pos[1] <= (H_BASE-11)*SKALA):", "                    (H_BASE-48)*SKALA  <= event.pos[1] <= (H_BASE-22)*SKALA):")


with open("ui_pygame.py", "w") as f:
    f.writelines(lines)
