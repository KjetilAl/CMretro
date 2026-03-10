"""
ui_pygame.py  —  Norsk Football Manager '95
Komplett pygame-basert UI-motor.

Erstatter all terminal-interaksjon fra spillmotor.py.
Pikselkunst, 320×200 @ 3× skalering, streng CM95-palett.
"""

from __future__ import annotations

import pygame
import sys
from typing import Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum, auto

# ─────────────────────────────────────────────────────────────────────────────
# SKJERMKONSTANTER
# ─────────────────────────────────────────────────────────────────────────────
W_BASE, H_BASE = 320, 200
SKALA          = 3
W, H           = W_BASE * SKALA, H_BASE * SKALA
FPS            = 60
TITTEL         = "Norsk Football Manager '95"

# ─────────────────────────────────────────────────────────────────────────────
# CM95-PALETT  (EGA/VGA inspirert)
# ─────────────────────────────────────────────────────────────────────────────
class P:
    SVART       = (  0,   0,   0)
    HVIT        = (252, 252, 252)
    GRÅ_LYS     = (168, 168, 168)
    GRÅ_MØRK    = ( 88,  88,  88)
    GRÅ_PANEL   = ( 48,  48,  64)   # UI-bakgrunn
    NAVY        = ( 16,  24,  64)   # Mørk bakgrunn
    BLÅL        = ( 48,  80, 176)   # Primær blå
    BLÅLL       = ( 96, 144, 220)   # Lys blå
    GRØNN       = ( 56, 168,  56)   # Bane / kondisjon god
    GRØNNLL     = (120, 220, 120)
    GULT        = (252, 204,   0)   # Highlight / gult kort
    GULTL       = (252, 240, 120)
    RØD         = (208,  48,  48)   # Advarsel / rødt kort
    RØDL        = (248, 120, 120)
    ORANSJE     = (220, 128,  32)   # Kondisjon ok
    CYAN        = (  0, 212, 212)   # Aksent
    CYANL       = (140, 236, 236)
    BRUN        = ( 96,  64,  32)   # Bane-detaljer
    KREMHVIT    = (240, 232, 200)   # Tekst på mørk
    LYSBLÅ_UI   = (180, 200, 240)   # Kolonne-tekst


# ─────────────────────────────────────────────────────────────────────────────
# PIKSELKUNST-FONT  (monospace bitmap, trekkes av pygame)
# ─────────────────────────────────────────────────────────────────────────────
class Fonter:
    _initialisert = False

    @classmethod
    def init(cls):
        if cls._initialisert:
            return
        pygame.font.init()
        # Courier New fallback til monospace
        try:
            cls.liten  = pygame.font.SysFont("Courier New", 9,  bold=False)
            cls.normal = pygame.font.SysFont("Courier New", 11, bold=False)
            cls.fet    = pygame.font.SysFont("Courier New", 11, bold=True)
            cls.stor   = pygame.font.SysFont("Courier New", 14, bold=True)
            cls.tittel = pygame.font.SysFont("Courier New", 18, bold=True)
        except Exception:
            cls.liten  = pygame.font.Font(None, 10)
            cls.normal = pygame.font.Font(None, 12)
            cls.fet    = pygame.font.Font(None, 12)
            cls.stor   = pygame.font.Font(None, 16)
            cls.tittel = pygame.font.Font(None, 20)
        cls._initialisert = True


# ─────────────────────────────────────────────────────────────────────────────
# PRIMITIVER  (tegner direkte på en pygame.Surface i base-koordinater)
# ─────────────────────────────────────────────────────────────────────────────
def tegn_fyll(surf, farge, rect):
    pygame.draw.rect(surf, farge, rect)

def tegn_kant(surf, farge, rect, tykkelse=1):
    pygame.draw.rect(surf, farge, rect, tykkelse)

def tegn_ramme_3d(surf, rect, farge_mørk=P.GRÅ_MØRK, farge_lys=P.GRÅ_LYS,
                  farge_bunn=P.NAVY, tittel: str = "", font=None):
    """Innesenket CM95-panel med 3D-kant og valgfri tittellinje."""
    x, y, w, h = rect
    # Bakgrunn
    pygame.draw.rect(surf, farge_bunn, rect)
    # Lys kant (topp + venstre)
    pygame.draw.line(surf, farge_lys, (x, y+h-1), (x, y))
    pygame.draw.line(surf, farge_lys, (x, y), (x+w-1, y))
    # Mørk kant (bunn + høyre)
    pygame.draw.line(surf, farge_mørk, (x+w-1, y), (x+w-1, y+h-1))
    pygame.draw.line(surf, farge_mørk, (x, y+h-1), (x+w-1, y+h-1))
    # Tittellinje
    if tittel and font:
        pygame.draw.rect(surf, P.BLÅL, (x+1, y+1, w-2, 11))
        t = font.render(tittel, False, P.HVIT)
        surf.blit(t, (x+3, y+2))

def tegn_tekst(surf, tekst, pos, font, farge=P.KREMHVIT, max_bredde=0):
    """Tegner tekst, kutter med '...' ved max_bredde."""
    if max_bredde > 0:
        while font.size(tekst)[0] > max_bredde and len(tekst) > 3:
            tekst = tekst[:-4] + "..."
    t = font.render(tekst, False, farge)
    surf.blit(t, pos)
    return t.get_width()

def tegn_badge(surf, tekst, pos, farge_bunn=P.BLÅL, farge_tekst=P.HVIT, font=None):
    """Liten fyllt badge med avrundede hjørner (simulert)."""
    if font is None:
        font = Fonter.liten
    t = font.render(tekst, False, farge_tekst)
    tw, th = t.get_size()
    pad = 2
    pygame.draw.rect(surf, farge_bunn, (pos[0]-pad, pos[1]-1, tw+pad*2, th+2))
    surf.blit(t, pos)

def tegn_linje_h(surf, farge, x, y, bredde, tykkelse=1):
    pygame.draw.rect(surf, farge, (x, y, bredde, tykkelse))

def tegn_knapp(surf, rect, tekst, font, aktiv=True, valgt=False, hovered=False):
    """CM95-stil knapp med 3D-effekt."""
    x, y, w, h = rect
    if not aktiv:
        bunn = P.GRÅ_MØRK; kant_l = P.GRÅ_MØRK; kant_m = P.GRÅ_MØRK; tkfarge = P.GRÅ_MØRK
    elif valgt:
        bunn = P.BLÅL; kant_l = P.BLÅLL; kant_m = P.NAVY; tkfarge = P.HVIT
    elif hovered:
        bunn = P.BLÅLL; kant_l = P.HVIT; kant_m = P.BLÅL; tkfarge = P.NAVY
    else:
        bunn = P.GRÅ_PANEL; kant_l = P.GRÅ_LYS; kant_m = P.GRÅ_MØRK; tkfarge = P.KREMHVIT

    pygame.draw.rect(surf, bunn, rect)
    pygame.draw.line(surf, kant_l, (x, y+h-1), (x, y))
    pygame.draw.line(surf, kant_l, (x, y), (x+w-1, y))
    pygame.draw.line(surf, kant_m, (x+w-1, y), (x+w-1, y+h-1))
    pygame.draw.line(surf, kant_m, (x, y+h-1), (x+w-1, y+h-1))
    t = font.render(tekst, False, tkfarge)
    tw, th = t.get_size()
    surf.blit(t, (x + (w-tw)//2, y + (h-th)//2))

def tegn_kondisjon_bar(surf, x, y, bredde, kond: float, skadet: bool = False):
    """Liten horisontal kondisjonsstripel."""
    h = 4
    pygame.draw.rect(surf, P.GRÅ_MØRK, (x, y, bredde, h))
    if skadet:
        farge = P.RØD
        fylt  = bredde
    else:
        andel = max(0.0, min(1.0, kond / 100.0))
        fylt  = int(bredde * andel)
        if kond >= 90:   farge = P.GRØNN
        elif kond >= 75: farge = P.GULT
        elif kond >= 60: farge = P.ORANSJE
        else:            farge = P.RØD
    if fylt > 0:
        pygame.draw.rect(surf, farge, (x, y, fylt, h))

def tegn_scrollbar(surf, x, y, h_total, antall_elementer,
                   synlige, scroll_pos, farge=P.GRÅ_MØRK, farge_thumb=P.BLÅL):
    """Enkel vertikal scrollbar."""
    if antall_elementer <= synlige:
        return
    pygame.draw.rect(surf, farge, (x, y, 4, h_total))
    thumb_h = max(8, int(h_total * synlige / antall_elementer))
    maks_scroll = antall_elementer - synlige
    thumb_y = y + int((h_total - thumb_h) * scroll_pos / max(1, maks_scroll))
    pygame.draw.rect(surf, farge_thumb, (x, thumb_y, 4, thumb_h))


# ─────────────────────────────────────────────────────────────────────────────
# BANE-TEGNER  (miniatyr topdown, brukes i formasjonsvisning)
# ─────────────────────────────────────────────────────────────────────────────
def tegn_bane(surf, rect, farge_gress=P.GRØNN, farge_linje=P.HVIT):
    """Minimal topdown-bane."""
    x, y, w, h = rect
    pygame.draw.rect(surf, farge_gress, rect)
    # Midtlinje
    mx = x + w // 2
    pygame.draw.line(surf, farge_linje, (mx, y+2), (mx, y+h-3), 1)
    # Midtsirkel (enkel firkant)
    r = min(w, h) // 8
    pygame.draw.rect(surf, farge_linje, (mx-r, y+h//2-r, r*2, r*2), 1)
    # Mål-bokser
    mb_w, mb_h = w // 6, h // 7
    pygame.draw.rect(surf, farge_linje, (x+2, y+h//2-mb_h, mb_w, mb_h*2), 1)
    pygame.draw.rect(surf, farge_linje, (x+w-mb_w-2, y+h//2-mb_h, mb_w, mb_h*2), 1)


# Normaliserte x,y-koordinater (0–1) for hvert formasjonslayout
# Posisjonene er justert for horisontal bane (venstre=forsvar, høyre=angrep)
FORMASJON_KOORDINATER: dict[str, list[tuple[float, float]]] = {
    "4-3-3": [
        (0.05, 0.50),                           # K
        (0.22, 0.15),(0.22, 0.40),(0.22, 0.60),(0.22, 0.85),  # F×4
        (0.50, 0.25),(0.50, 0.50),(0.50, 0.75),               # M×3
        (0.78, 0.15),(0.78, 0.50),(0.78, 0.85),               # A×3
    ],
    "4-4-2": [
        (0.05, 0.50),
        (0.22, 0.15),(0.22, 0.40),(0.22, 0.60),(0.22, 0.85),
        (0.50, 0.15),(0.50, 0.38),(0.50, 0.62),(0.50, 0.85),
        (0.78, 0.35),(0.78, 0.65),
    ],
    "4-2-3-1": [
        (0.05, 0.50),
        (0.22, 0.15),(0.22, 0.40),(0.22, 0.60),(0.22, 0.85),
        (0.44, 0.35),(0.44, 0.65),
        (0.62, 0.15),(0.62, 0.50),(0.62, 0.85),
        (0.82, 0.50),
    ],
    "3-5-2": [
        (0.05, 0.50),
        (0.22, 0.28),(0.22, 0.50),(0.22, 0.72),
        (0.50, 0.10),(0.50, 0.30),(0.50, 0.50),(0.50, 0.70),(0.50, 0.90),
        (0.78, 0.35),(0.78, 0.65),
    ],
    "3-4-3": [
        (0.05, 0.50),
        (0.22, 0.28),(0.22, 0.50),(0.22, 0.72),
        (0.50, 0.20),(0.50, 0.43),(0.50, 0.57),(0.50, 0.80),
        (0.78, 0.15),(0.78, 0.50),(0.78, 0.85),
    ],
    "5-3-2": [
        (0.05, 0.50),
        (0.20, 0.10),(0.20, 0.32),(0.20, 0.50),(0.20, 0.68),(0.20, 0.90),
        (0.50, 0.25),(0.50, 0.50),(0.50, 0.75),
        (0.78, 0.35),(0.78, 0.65),
    ],
    "4-1-4-1": [
        (0.05, 0.50),
        (0.22, 0.15),(0.22, 0.40),(0.22, 0.60),(0.22, 0.85),
        (0.42, 0.50),
        (0.62, 0.15),(0.62, 0.38),(0.62, 0.62),(0.62, 0.85),
        (0.82, 0.50),
    ],
}

def tegn_formasjon_på_bane(surf, rect, spillere: list, formasjon_navn: str,
                            valgt_idx: int = -1, font=None):
    """Tegner spillerpunkter på en miniatyr-bane."""
    tegn_bane(surf, rect)
    x0, y0, bw, bh = rect
    if font is None:
        font = Fonter.liten

    koord = FORMASJON_KOORDINATER.get(formasjon_navn)
    if not koord:
        # Fallback: jevn fordeling
        koord = [(0.05 + i * 0.09, 0.50) for i in range(11)]

    for i, spiller in enumerate(spillere[:11]):
        if i >= len(koord):
            break
        nx, ny = koord[i]
        cx = int(x0 + nx * bw)
        cy = int(y0 + ny * bh)

        # Punkt
        farge = P.GULT if i == valgt_idx else P.HVIT
        pygame.draw.circle(surf, P.SVART, (cx, cy), 5)
        pygame.draw.circle(surf, farge,  (cx, cy), 4)

        # Etternavn-stub (første 3 bokstaver)
        navn = getattr(spiller, 'etternavn', '?')[:4]
        t = font.render(navn, False, P.HVIT)
        surf.blit(t, (cx - t.get_width()//2, cy + 6))


# ─────────────────────────────────────────────────────────────────────────────
# SKJERM-DATAKLASSE
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class SkjermData:
    """Abstrakt visningsenhet — underklasser tegner seg selv."""

    def tegn(self, surf: pygame.Surface, ui: "UIMotor") -> None:
        raise NotImplementedError

    def håndter_event(self, event: pygame.event.Event, ui: "UIMotor") -> None:
        raise NotImplementedError


# ─────────────────────────────────────────────────────────────────────────────
# FELLES HJELPERE (brukes av alle skjermer)
# ─────────────────────────────────────────────────────────────────────────────
def _tegn_topplinje(surf, venstre: str, midtre: str, høyre: str, font=None):
    """Toppstripel i NAVY med tre tekstfelt."""
    if font is None:
        font = Fonter.liten
    pygame.draw.rect(surf, P.NAVY, (0, 0, W_BASE, 12))
    pygame.draw.rect(surf, P.BLÅL, (0, 11, W_BASE, 1))
    tegn_tekst(surf, venstre, (2, 2), font, P.GULT)
    mid_t = font.render(midtre, False, P.KREMHVIT)
    surf.blit(mid_t, (W_BASE//2 - mid_t.get_width()//2, 2))
    høyre_t = font.render(høyre, False, P.LYSBLÅ_UI)
    surf.blit(høyre_t, (W_BASE - høyre_t.get_width() - 2, 2))

def _tegn_bunnlinje(surf, tekst: str, font=None):
    """Statuslinje nederst."""
    if font is None:
        font = Fonter.liten
    pygame.draw.rect(surf, P.NAVY, (0, H_BASE-11, W_BASE, 11))
    pygame.draw.rect(surf, P.BLÅL, (0, H_BASE-12, W_BASE, 1))
    tegn_tekst(surf, tekst, (3, H_BASE-9), font, P.GRÅ_LYS)

def _tegn_bakgrunn(surf, farge=None):
    if farge is None:
        farge = P.GRÅ_PANEL
    surf.fill(farge)
    # Subtil horisontal rutenett-overlay
    for y in range(0, H_BASE, 8):
        pygame.draw.line(surf, (farge[0]+4, farge[1]+4, farge[2]+6), (0, y), (W_BASE, y))


# ─────────────────────────────────────────────────────────────────────────────
# SKJERM: SPLASHSCREEN / HOVEDMENY
# ─────────────────────────────────────────────────────────────────────────────
class HovedmenySkjerm(SkjermData):
    def __init__(self, on_start: Callable, on_avslutt: Callable):
        self.on_start    = on_start
        self.on_avslutt  = on_avslutt
        self._tick       = 0

    def tegn(self, surf, ui):
        self._tick += 1
        # Gradientlignende mørk bakgrunn
        surf.fill(P.NAVY)
        for y in range(H_BASE):
            mørkhet = int(y * 0.7)
            pygame.draw.line(surf, (max(0, 16-mørkhet//8), max(0, 24-mørkhet//8),
                                    max(0, 64+mørkhet//4)), (0, y), (W_BASE, y))

        # Bane-dekorasjon i bunn
        tegn_bane(surf, (0, H_BASE-40, W_BASE, 40), P.GRØNN, P.HVIT)

        # Logo-boks
        logo_rect = (20, 18, W_BASE-40, 70)
        pygame.draw.rect(surf, (10, 18, 50), logo_rect)
        pygame.draw.rect(surf, P.BLÅLL, logo_rect, 2)

        f_tittel = Fonter.tittel
        f_sub    = Fonter.normal

        t1 = f_tittel.render("NORSK FOOTBALL", False, P.GULT)
        t2 = f_tittel.render("MANAGER", False, P.GULT)
        t3 = f_sub.render("'95  EDITION", False, P.CYANL)

        surf.blit(t1, (logo_rect[0] + (logo_rect[2]-t1.get_width())//2, 26))
        surf.blit(t2, (logo_rect[0] + (logo_rect[2]-t2.get_width())//2, 44))
        surf.blit(t3, (logo_rect[0] + (logo_rect[2]-t3.get_width())//2, 64))

        # Pulserende «Trykk Enter»
        if (self._tick // 30) % 2 == 0:
            t4 = Fonter.liten.render("[ TRYKK ENTER FOR Å STARTE ]", False, P.KREMHVIT)
            surf.blit(t4, ((W_BASE - t4.get_width())//2, 100))

        # Versjon/copyright
        tv = Fonter.liten.render("v0.1  ©1995 ANTROPIKK SOFTWARE", False, P.GRÅ_MØRK)
        surf.blit(tv, ((W_BASE - tv.get_width())//2, H_BASE-50))

        # Knapper
        tegn_knapp(surf, (60, 118, 80, 14), "START", Fonter.normal,
                   hovered=ui.mus_innenfor((60*SKALA, 118*SKALA, 80*SKALA, 14*SKALA)))
        tegn_knapp(surf, (180, 118, 80, 14), "AVSLUTT", Fonter.normal,
                   hovered=ui.mus_innenfor((180*SKALA, 118*SKALA, 80*SKALA, 14*SKALA)))

    def håndter_event(self, event, ui):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.on_start()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            if 60 <= mx <= 140 and 118 <= my <= 132:
                self.on_start()
            elif 180 <= mx <= 260 and 118 <= my <= 132:
                self.on_avslutt()


# ─────────────────────────────────────────────────────────────────────────────
# SKJERM: VELG KLUBB
# ─────────────────────────────────────────────────────────────────────────────
class VelgKlubbSkjerm(SkjermData):
    def __init__(self, klubber: list, on_valgt: Callable[[Any], None]):
        self.klubber  = klubber
        self.on_valgt = on_valgt
        self._scroll  = 0
        self._hover   = -1
        self._valgt   = -1
        self._SYNLIGE = 10

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)
        _tegn_topplinje(surf, "NFM'95", "VELG KLUBB", f"{len(self.klubber)} KLUBBER")

        # Kolonnehoder
        pygame.draw.rect(surf, P.BLÅL, (2, 13, W_BASE-4, 10))
        f = Fonter.liten
        tegn_tekst(surf, "KLUBB",        (4,   14), f, P.HVIT)
        tegn_tekst(surf, "STJERNER",     (130, 14), f, P.HVIT)
        tegn_tekst(surf, "STADION",      (200, 14), f, P.HVIT)

        # Klubbliste
        synlige  = self._SYNLIGE
        start    = self._scroll
        slutt    = min(start + synlige, len(self.klubber))
        rad_h    = 14
        y0       = 25

        mx, my = ui.base_mus()

        for i, idx in enumerate(range(start, slutt)):
            k     = self.klubber[idx]
            ry    = y0 + i * rad_h
            er_hover  = (4 <= mx <= W_BASE-8 and ry <= my < ry+rad_h)
            er_valgt  = (idx == self._valgt)

            if er_valgt:
                pygame.draw.rect(surf, P.BLÅL, (4, ry, W_BASE-16, rad_h-1))
            elif er_hover:
                pygame.draw.rect(surf, P.GRÅ_MØRK, (4, ry, W_BASE-16, rad_h-1))
                self._hover = idx
            elif i % 2 == 0:
                pygame.draw.rect(surf, (38, 38, 52), (4, ry, W_BASE-16, rad_h-1))

            navn    = getattr(k, 'navn', str(k))
            styrke  = getattr(k, 'historisk_styrke', 0)
            stadion = getattr(k, 'stadion', None)
            kap     = getattr(stadion, 'kapasitet', 0) if stadion else 0
            stjerner_full = min(5, styrke // 4)
            stjerner_str  = "★" * stjerner_full + "☆" * (5 - stjerner_full)

            tkfarge = P.HVIT if er_valgt else P.KREMHVIT
            tegn_tekst(surf, navn[:22],   (6,   ry+2), f, tkfarge, max_bredde=120)
            tegn_tekst(surf, stjerner_str,(132,  ry+2), f, P.GULT)
            tegn_tekst(surf, f"{kap:,}",  (200, ry+2), f, P.LYSBLÅ_UI)

        # Scrollbar
        tegn_scrollbar(surf, W_BASE-7, y0, synlige*rad_h,
                        len(self.klubber), synlige, self._scroll)

        # Bekreft-knapp (aktiv når valgt)
        aktiv = self._valgt >= 0
        tegn_knapp(surf, (W_BASE//2-40, H_BASE-24, 80, 13), "VELG KLUBB",
                   Fonter.normal, aktiv=aktiv,
                   hovered=aktiv and ui.mus_innenfor(
                       ((W_BASE//2-40)*SKALA, (H_BASE-24)*SKALA, 80*SKALA, 13*SKALA)))

        _tegn_bunnlinje(surf, "↑↓/SCROLL  ENTER=VELG  ESC=TILBAKE")

    def håndter_event(self, event, ui):
        maks_scroll = max(0, len(self.klubber) - self._SYNLIGE)
        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, min(maks_scroll, self._scroll - event.y))

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            rad_h, y0 = 14, 25
            # Klikk på rad
            for i in range(self._SYNLIGE):
                idx = self._scroll + i
                if idx >= len(self.klubber):
                    break
                ry = y0 + i * rad_h
                if 4 <= mx <= W_BASE-8 and ry <= my < ry+rad_h:
                    if self._valgt == idx:
                        self.on_valgt(self.klubber[idx])
                    else:
                        self._valgt = idx
            # Bekreft-knapp
            if (self._valgt >= 0 and
                    (W_BASE//2-40)*SKALA <= event.pos[0] <= (W_BASE//2+40)*SKALA and
                    (H_BASE-24)*SKALA  <= event.pos[1] <= (H_BASE-11)*SKALA):
                self.on_valgt(self.klubber[self._valgt])

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                if self._valgt < len(self.klubber)-1:
                    self._valgt += 1
                    if self._valgt >= self._scroll + self._SYNLIGE:
                        self._scroll = min(maks_scroll, self._scroll+1)
            elif event.key == pygame.K_UP:
                if self._valgt > 0:
                    self._valgt -= 1
                    if self._valgt < self._scroll:
                        self._scroll = max(0, self._scroll-1)
                elif self._valgt == -1 and self.klubber:
                    self._valgt = 0
            elif event.key == pygame.K_RETURN and self._valgt >= 0:
                self.on_valgt(self.klubber[self._valgt])


# ─────────────────────────────────────────────────────────────────────────────
# SKJERM: KAMPDAG-HUB  (erstatter _håndter_kampdag)
# ─────────────────────────────────────────────────────────────────────────────
class KampdagSkjerm(SkjermData):
    """Kampdag-hub: velg mellom laguttak, spill kamp, vis stall."""

    def __init__(self, kamp, dato, spiller_klubb, motstander,
                 on_laguttak: Callable, on_spill: Callable, on_spillerstall: Callable,
                 on_tabell: Callable):
        self.kamp           = kamp
        self.dato           = dato
        self.spiller_klubb  = spiller_klubb
        self.motstander     = motstander
        self.on_laguttak    = on_laguttak
        self.on_spill       = on_spill
        self.on_spillerstall = on_spillerstall
        self.on_tabell      = on_tabell
        self._hover         = -1

    def _meny_rader(self):
        return [
            ("F1  LAGUTTAK & TAKTIKK",   self.on_laguttak),
            ("F2  SPILL KAMP →",         self.on_spill),
            ("F3  SPILLERSTALL",         self.on_spillerstall),
            ("F4  SERIATABELL",          self.on_tabell),
        ]

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)

        er_hjemme = (self.kamp.hjemme == self.spiller_klubb)
        sted = "HJEMMEKAMP" if er_hjemme else "BORTEKAMP"
        dato_str = self.dato.strftime('%d.%m.%Y')
        _tegn_topplinje(surf, sted, dato_str, "")

        f = Fonter.normal
        fb = Fonter.fet
        fs = Fonter.liten

        # Kampheader
        pygame.draw.rect(surf, P.NAVY, (4, 14, W_BASE-8, 30))
        pygame.draw.rect(surf, P.BLÅL, (4, 14, W_BASE-8, 30), 1)

        hjemme_navn = getattr(self.kamp.hjemme, 'navn', '?')
        borte_navn  = getattr(self.kamp.borte,  'navn', '?')

        t_vs = f.render("VS", False, P.GRÅ_MØRK)
        t_h  = fb.render(hjemme_navn[:16], False,
                         P.GULT if er_hjemme else P.KREMHVIT)
        t_b  = fb.render(borte_navn[:16],  False,
                         P.GULT if not er_hjemme else P.KREMHVIT)

        surf.blit(t_h,  (8,  22))
        surf.blit(t_vs, (W_BASE//2 - t_vs.get_width()//2, 22))
        surf.blit(t_b,  (W_BASE - t_b.get_width() - 8, 22))

        tegn_linje_h(surf, P.BLÅL, 4, 44, W_BASE-8)

        # Meny
        rader = self._meny_rader()
        mx, my = ui.base_mus()
        meny_y = 52
        knapp_h = 18

        for i, (tekst, _) in enumerate(rader):
            ry = meny_y + i * (knapp_h + 4)
            er_hover = (10 <= mx <= W_BASE-10 and ry <= my < ry+knapp_h)
            tegn_knapp(surf, (10, ry, W_BASE-20, knapp_h), tekst,
                       fb, hovered=er_hover)

        # Neste kamp-info
        tegn_linje_h(surf, P.GRÅ_MØRK, 4, H_BASE-22, W_BASE-8)
        tegn_tekst(surf, "ESC = INGEN KAMP DENNE RUNDEN", (4, H_BASE-20), fs, P.GRÅ_MØRK)
        _tegn_bunnlinje(surf, "F1–F4  VELG HANDLING")

    def håndter_event(self, event, ui):
        rader = self._meny_rader()
        meny_y   = 52
        knapp_h  = 18

        if event.type == pygame.KEYDOWN:
            tast_map = {
                pygame.K_F1: 0, pygame.K_F2: 1,
                pygame.K_F3: 2, pygame.K_F4: 3,
            }
            if event.key in tast_map:
                idx = tast_map[event.key]
                if idx < len(rader):
                    rader[idx][1]()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            for i, (_, callback) in enumerate(rader):
                ry = meny_y + i * (knapp_h + 4)
                if 10 <= mx <= W_BASE-10 and ry <= my < ry+knapp_h:
                    callback()
                    return


# ─────────────────────────────────────────────────────────────────────────────
# SKJERM: LAGUTTAK  (erstatter _laguttak_meny)
# ─────────────────────────────────────────────────────────────────────────────
class LaguttakSkjerm(SkjermData):
    """
    To kolonner: startellever (venstre) + bane med formasjon (høyre).
    Under: benk. Klikk for å velge og bytte.
    """

    def __init__(self, builder, motstandernavn: str, on_ferdig: Callable):
        self.builder       = builder
        self.motstandernavn = motstandernavn
        self.on_ferdig     = on_ferdig
        self._valgt_start  = -1   # Indeks i startellever
        self._valgt_benk   = -1   # Indeks i benk
        self._formasjon_idx = list(__import__('taktikk').TAKTIKK_KATALOG.keys()).index(
            builder.formasjon_navn) if builder.formasjon_navn in \
            __import__('taktikk').TAKTIKK_KATALOG else 0
        self._TAKTIKK_LISTE = list(__import__('taktikk').TAKTIKK_KATALOG.keys())

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)
        f  = Fonter.liten
        fb = Fonter.fet

        _tegn_topplinje(surf, "LAGUTTAK",
                         self.builder.klubb.navn[:18],
                         f"vs {self.motstandernavn[:10]}")

        # ── Venstre kolonne: startellever ────────────────────────
        rad_h = 13
        y0    = 14
        x0    = 2

        for i, s in enumerate(self.builder.startellever):
            ry     = y0 + i * rad_h
            er_v   = (i == self._valgt_start)
            farge  = P.BLÅL if er_v else (P.NAVY if i % 2 == 0 else (28, 32, 56))
            pygame.draw.rect(surf, farge, (x0, ry, 150, rad_h-1))
            pos    = getattr(s, 'primær_posisjon', None)
            pos_s  = pos.name if pos else '?'
            ferd   = getattr(s, 'ferdighet', 0)
            navn   = f"{getattr(s, 'fornavn', '?')[0]}. {getattr(s, 'etternavn', '?')}"
            kond   = getattr(s, 'kondisjon', 100.0)
            skadet = getattr(s, 'skadet', False)

            tkf = P.HVIT if er_v else P.KREMHVIT
            tegn_tekst(surf, f"{i+1:>2}", (x0+1, ry+2), f, P.GRÅ_LYS)
            tegn_tekst(surf, navn[:14],   (x0+14, ry+2), f, tkf, max_bredde=74)
            tegn_tekst(surf, pos_s,       (x0+90, ry+2), f, P.LYSBLÅ_UI)
            tegn_tekst(surf, str(ferd),   (x0+114, ry+2), f, P.GULT)
            tegn_kondisjon_bar(surf, x0+126, ry+4, 22, kond, skadet)

        # ── Benk (under startellevere) ────────────────────────────
        benk_y0 = y0 + 11 * rad_h + 4
        pygame.draw.rect(surf, P.BLÅL, (x0, benk_y0-1, 150, 8))
        tegn_tekst(surf, "── BENK ──", (x0+2, benk_y0), Fonter.liten, P.HVIT)
        benk_y0 += 9

        for j, s in enumerate(self.builder.benk):
            ry     = benk_y0 + j * (rad_h - 2)
            er_v   = (j == self._valgt_benk)
            farge  = P.BLÅLL if er_v else (P.GRÅ_MØRK if j % 2 == 0 else (48, 48, 48))
            pygame.draw.rect(surf, farge, (x0, ry, 150, rad_h-2))
            pos    = getattr(s, 'primær_posisjon', None)
            pos_s  = pos.name if pos else '?'
            ferd   = getattr(s, 'ferdighet', 0)
            navn   = f"{getattr(s, 'fornavn', '?')[0]}. {getattr(s, 'etternavn', '?')}"
            kond   = getattr(s, 'kondisjon', 100.0)
            skadet = getattr(s, 'skadet', False)

            tkf = P.NAVY if er_v else P.GRÅ_LYS
            tegn_tekst(surf, f"S{j+1}", (x0+1, ry+1), f, P.GRÅ_MØRK)
            tegn_tekst(surf, navn[:14], (x0+14, ry+1), f, tkf, max_bredde=74)
            tegn_tekst(surf, pos_s,     (x0+90, ry+1), f, P.LYSBLÅ_UI)
            tegn_tekst(surf, str(ferd), (x0+114, ry+1), f, P.GULT)
            tegn_kondisjon_bar(surf, x0+126, ry+3, 22, kond, skadet)

        # ── Høyre: formasjons-bane ────────────────────────────────
        bane_rect = (156, 14, 162, 150)
        tegn_formasjon_på_bane(surf, bane_rect, self.builder.startellever,
                                self.builder.formasjon_navn,
                                valgt_idx=self._valgt_start, font=Fonter.liten)

        # ── Formasjonsvelger ──────────────────────────────────────
        fv_y = 170
        pygame.draw.rect(surf, P.NAVY, (156, fv_y, 162, 16))
        pygame.draw.rect(surf, P.BLÅL, (156, fv_y, 162, 16), 1)
        tegn_tekst(surf, "◄", (158, fv_y+3), fb, P.GULT)
        t_f = Fonter.normal.render(self.builder.formasjon_navn, False, P.KREMHVIT)
        surf.blit(t_f, (156 + 82 - t_f.get_width()//2, fv_y+3))
        tegn_tekst(surf, "►", (306, fv_y+3), fb, P.GULT)

        # ── Ferdig-knapp ──────────────────────────────────────────
        tegn_knapp(surf, (156, H_BASE-14, 162, 12), "FERDIG / TILBAKE",
                   Fonter.normal,
                   hovered=ui.mus_innenfor((156*SKALA, (H_BASE-14)*SKALA,
                                            162*SKALA, 12*SKALA)))

        # ── Instruksjon ───────────────────────────────────────────
        _tegn_bunnlinje(surf, "KLIKK START→BENK FOR Å BYTTE  ◄► FORMASJON")

        # Marker bytte-modus
        if self._valgt_start >= 0 and self._valgt_benk >= 0:
            pygame.draw.rect(surf, P.GULT, (x0, 0, 150, 1))  # gul toppstripel

    def håndter_event(self, event, ui):
        from taktikk import TAKTIKK_KATALOG
        rad_h  = 13
        y0     = 14
        benk_y0 = y0 + 11 * rad_h + 4 + 9

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()

            # Formasjonspiler
            if 170 <= my <= 186:
                if 156 <= mx <= 170:  # Venstre pil
                    self._formasjon_idx = (self._formasjon_idx - 1) % len(self._TAKTIKK_LISTE)
                    self.builder.bytt_formasjon(self._TAKTIKK_LISTE[self._formasjon_idx])
                    self._valgt_start = -1; self._valgt_benk = -1
                    return
                if 305 <= mx <= 320:  # Høyre pil
                    self._formasjon_idx = (self._formasjon_idx + 1) % len(self._TAKTIKK_LISTE)
                    self.builder.bytt_formasjon(self._TAKTIKK_LISTE[self._formasjon_idx])
                    self._valgt_start = -1; self._valgt_benk = -1
                    return

            # Ferdig-knapp
            if my >= H_BASE-14 and 156 <= mx <= 318:
                self.on_ferdig()
                return

            # Klikk på startspiller
            if mx <= 152:
                for i in range(len(self.builder.startellever)):
                    ry = y0 + i * rad_h
                    if ry <= my < ry + rad_h:
                        if self._valgt_benk >= 0:
                            self.builder.bytt_spiller(i, self._valgt_benk)
                            self._valgt_start = -1; self._valgt_benk = -1
                        else:
                            self._valgt_start = i if self._valgt_start != i else -1
                        return

                # Klikk på benkespiller
                for j in range(len(self.builder.benk)):
                    ry = benk_y0 + j * (rad_h - 2)
                    if ry <= my < ry + rad_h-2:
                        if self._valgt_start >= 0:
                            self.builder.bytt_spiller(self._valgt_start, j)
                            self._valgt_start = -1; self._valgt_benk = -1
                        else:
                            self._valgt_benk = j if self._valgt_benk != j else -1
                        return

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.on_ferdig()
            elif event.key == pygame.K_LEFT:
                self._formasjon_idx = (self._formasjon_idx - 1) % len(self._TAKTIKK_LISTE)
                self.builder.bytt_formasjon(self._TAKTIKK_LISTE[self._formasjon_idx])
                self._valgt_start = -1; self._valgt_benk = -1
            elif event.key == pygame.K_RIGHT:
                self._formasjon_idx = (self._formasjon_idx + 1) % len(self._TAKTIKK_LISTE)
                self.builder.bytt_formasjon(self._TAKTIKK_LISTE[self._formasjon_idx])
                self._valgt_start = -1; self._valgt_benk = -1


# ─────────────────────────────────────────────────────────────────────────────
# SKJERM: SPILLERSTALL
# ─────────────────────────────────────────────────────────────────────────────
class SpillerstallSkjerm(SkjermData):
    def __init__(self, klubb, on_tilbake: Callable):
        self.klubb      = klubb
        self.on_tilbake = on_tilbake
        self._scroll    = 0
        self._hover     = -1
        self._valgt     = -1
        self._alle_spillere = self._sorter_spillere()
        self._SYNLIGE   = 12

    def _sorter_spillere(self):
        from taktikk import POSISJON_GRUPPE
        grupper = {"K": [], "F": [], "M": [], "A": []}
        for s in getattr(self.klubb, 'spillerstall', []):
            pos   = getattr(s, 'primær_posisjon', None)
            gruppe = POSISJON_GRUPPE.get(pos, "M") if pos else "M"
            grupper[gruppe].append(s)
        for g in grupper:
            grupper[g].sort(key=lambda x: getattr(x, 'ferdighet', 0), reverse=True)
        return grupper["K"] + grupper["F"] + grupper["M"] + grupper["A"]

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)
        f  = Fonter.liten
        fb = Fonter.fet

        _tegn_topplinje(surf, "SPILLERSTALL", self.klubb.navn[:20],
                         f"{len(self._alle_spillere)} SPILLERE")

        # Kolonnehoder
        pygame.draw.rect(surf, P.BLÅL, (2, 13, W_BASE-4, 9))
        tegn_tekst(surf, "#",      (2,   14), f, P.HVIT)
        tegn_tekst(surf, "NAVN",   (12,  14), f, P.HVIT)
        tegn_tekst(surf, "POS",    (110, 14), f, P.HVIT)
        tegn_tekst(surf, "FERD",   (134, 14), f, P.HVIT)
        tegn_tekst(surf, "KOND",   (156, 14), f, P.HVIT)
        tegn_tekst(surf, "RYKTE",  (200, 14), f, P.HVIT)
        tegn_tekst(surf, "ALDER",  (240, 14), f, P.HVIT)
        tegn_tekst(surf, "KONTRAK",(275, 14), f, P.HVIT)

        # Spillerrader
        rad_h  = 13
        y0     = 24
        start  = self._scroll
        slutt  = min(start + self._SYNLIGE, len(self._alle_spillere))
        mx, my = ui.base_mus()

        for i, idx in enumerate(range(start, slutt)):
            s    = self._alle_spillere[idx]
            ry   = y0 + i * rad_h
            er_v = (idx == self._valgt)
            er_h = (2 <= mx <= W_BASE-8 and ry <= my < ry+rad_h)

            if er_v:
                pygame.draw.rect(surf, P.BLÅL, (2, ry, W_BASE-10, rad_h-1))
            elif er_h:
                pygame.draw.rect(surf, P.GRÅ_MØRK, (2, ry, W_BASE-10, rad_h-1))
            elif i % 2 == 0:
                pygame.draw.rect(surf, (34, 34, 48), (2, ry, W_BASE-10, rad_h-1))

            pos     = getattr(s, 'primær_posisjon', None)
            pos_s   = pos.name if pos else '?'
            ferd    = getattr(s, 'ferdighet', 0)
            kond    = getattr(s, 'kondisjon', 100.0)
            skadet  = getattr(s, 'skadet', False)
            rykte   = getattr(s, 'rykte', 0)
            alder   = getattr(s, 'alder', 0)
            kontr   = getattr(s, 'kontrakt', None)
            kontr_s = str(getattr(kontr, 'utlops_aar', '?')) if kontr else '-'
            fornavn = getattr(s, 'fornavn', '?')
            etternavn = getattr(s, 'etternavn', '?')
            navn    = f"{fornavn[0]}. {etternavn}"

            tkf = P.HVIT if er_v else P.KREMHVIT
            tegn_tekst(surf, str(idx+1),  (2,   ry+2), f, P.GRÅ_MØRK)
            tegn_tekst(surf, navn[:18],   (12,  ry+2), f, tkf, max_bredde=95)
            tegn_tekst(surf, pos_s,       (110, ry+2), f, P.LYSBLÅ_UI)
            tegn_badge(surf, str(ferd),   (132, ry+1),
                       P.GRØNN if ferd >= 14 else (P.BLÅL if ferd >= 10 else P.GRÅ_MØRK),
                       P.HVIT, f)
            if skadet:
                tegn_tekst(surf, "SKADET", (156, ry+2), f, P.RØD)
            else:
                tegn_kondisjon_bar(surf, 156, ry+4, 42, kond)
                tegn_tekst(surf, f"{kond:.0f}%", (200, ry+2), f,
                           P.GRØNN if kond >= 90 else (P.GULT if kond >= 75 else P.RØD))
            tegn_tekst(surf, str(rykte),  (240, ry+2), f, P.GULTL)
            tegn_tekst(surf, str(alder),  (260, ry+2), f, P.GRÅ_LYS)
            tegn_tekst(surf, kontr_s,     (278, ry+2), f, P.CYANL)

        # Scrollbar
        tegn_scrollbar(surf, W_BASE-5, y0, self._SYNLIGE*rad_h,
                        len(self._alle_spillere), self._SYNLIGE, self._scroll)

        # Tilbake-knapp
        tegn_knapp(surf, (W_BASE//2-35, H_BASE-13, 70, 11), "TILBAKE",
                   Fonter.normal,
                   hovered=ui.mus_innenfor(((W_BASE//2-35)*SKALA, (H_BASE-13)*SKALA,
                                             70*SKALA, 11*SKALA)))

        _tegn_bunnlinje(surf, "↑↓ SCROLL  ESC=TILBAKE")

    def håndter_event(self, event, ui):
        maks_scroll = max(0, len(self._alle_spillere) - self._SYNLIGE)

        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, min(maks_scroll, self._scroll - event.y))

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            rad_h, y0 = 13, 24
            for i in range(self._SYNLIGE):
                idx = self._scroll + i
                if idx >= len(self._alle_spillere):
                    break
                ry = y0 + i * rad_h
                if 2 <= mx <= W_BASE-8 and ry <= my < ry+rad_h:
                    self._valgt = idx if self._valgt != idx else -1
            # Tilbake-knapp
            if (my >= (H_BASE-13) and
                    (W_BASE//2-35)*SKALA <= event.pos[0] <= (W_BASE//2+35)*SKALA):
                self.on_tilbake()

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.on_tilbake()
            elif event.key == pygame.K_DOWN:
                self._scroll = min(maks_scroll, self._scroll + 1)
            elif event.key == pygame.K_UP:
                self._scroll = max(0, self._scroll - 1)


# ─────────────────────────────────────────────────────────────────────────────
# SKJERM: SERIATABELL
# ─────────────────────────────────────────────────────────────────────────────
class TabellSkjerm(SkjermData):
    def __init__(self, tabell, spiller_klubb_navn: str, on_tilbake: Callable):
        self.tabell              = tabell
        self.spiller_klubb_navn  = spiller_klubb_navn
        self.on_tilbake          = on_tilbake
        self._fane               = 0   # 0=tabell 1=toppscorere

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)
        f  = Fonter.liten
        fb = Fonter.fet

        _tegn_topplinje(surf, "SERIE", self.tabell.divisjon, "")

        # Faner
        for fi, tekst in enumerate(["TABELL", "TOPPSCORERE"]):
            er_aktiv = fi == self._fane
            tegn_knapp(surf, (2 + fi*80, 13, 78, 10), tekst, f,
                        valgt=er_aktiv,
                        hovered=(not er_aktiv and
                                 ui.mus_innenfor(((2+fi*80)*SKALA, 13*SKALA, 78*SKALA, 10*SKALA))))

        if self._fane == 0:
            self._tegn_tabell(surf, ui)
        else:
            self._tegn_toppscorere(surf, ui)

        tegn_knapp(surf, (W_BASE//2-30, H_BASE-13, 60, 11), "TILBAKE",
                   Fonter.normal,
                   hovered=ui.mus_innenfor(((W_BASE//2-30)*SKALA, (H_BASE-13)*SKALA,
                                             60*SKALA, 11*SKALA)))
        _tegn_bunnlinje(surf, "TAB=BYTT FANE  ESC=TILBAKE")

    def _tegn_tabell(self, surf, ui):
        f  = Fonter.liten
        rader = self.tabell.sorter()

        # Kolonnetitler
        pygame.draw.rect(surf, P.BLÅL, (2, 24, W_BASE-4, 8))
        tegn_tekst(surf, "#",  (2,  25), f, P.HVIT)
        tegn_tekst(surf, "KLUBB", (14, 25), f, P.HVIT)
        tegn_tekst(surf, "K",  (142, 25), f, P.HVIT)
        tegn_tekst(surf, "S",  (158, 25), f, P.HVIT)
        tegn_tekst(surf, "U",  (172, 25), f, P.HVIT)
        tegn_tekst(surf, "T",  (186, 25), f, P.HVIT)
        tegn_tekst(surf, "MF", (200, 25), f, P.HVIT)
        tegn_tekst(surf, "MM", (216, 25), f, P.HVIT)
        tegn_tekst(surf, "MD", (232, 25), f, P.HVIT)
        tegn_tekst(surf, "P",  (252, 25), f, P.HVIT)

        rad_h = 12
        y0    = 34
        for plass, rad in enumerate(rader, 1):
            ry       = y0 + (plass-1) * rad_h
            if ry + rad_h > H_BASE - 16:
                break
            er_min   = (rad.klubb_navn == self.spiller_klubb_navn)
            farge_rad = P.BLÅL if er_min else ((34,34,48) if plass % 2 == 0 else (28,28,40))
            pygame.draw.rect(surf, farge_rad, (2, ry, W_BASE-4, rad_h-1))

            md  = rad.mål_differanse
            md_s = f"+{md}" if md > 0 else str(md)
            tkf  = P.GULT if er_min else P.KREMHVIT

            tegn_tekst(surf, str(plass),          (2,   ry+2), f, P.GRÅ_LYS)
            tegn_tekst(surf, rad.klubb_navn[:18],  (14,  ry+2), f, tkf, max_bredde=125)
            tegn_tekst(surf, str(rad.kamp),        (142, ry+2), f, P.LYSBLÅ_UI)
            tegn_tekst(surf, str(rad.seier),       (158, ry+2), f, P.GRØNN)
            tegn_tekst(surf, str(rad.uavgjort),    (172, ry+2), f, P.GULT)
            tegn_tekst(surf, str(rad.tap),         (186, ry+2), f, P.RØD)
            tegn_tekst(surf, str(rad.mål_for),     (200, ry+2), f, P.KREMHVIT)
            tegn_tekst(surf, str(rad.mål_mot),     (216, ry+2), f, P.KREMHVIT)
            tegn_tekst(surf, md_s,                 (232, ry+2), f,
                       P.GRØNN if md > 0 else (P.RØD if md < 0 else P.GRÅ_LYS))
            tegn_badge(surf, str(rad.poeng),        (252, ry+1),
                       P.GULT if er_min else P.NAVY, P.NAVY if er_min else P.HVIT, f)

    def _tegn_toppscorere(self, surf, ui):
        f  = Fonter.liten
        if not hasattr(self.tabell, '_statistikk_register'):
            tegn_tekst(surf, "Ingen statistikk tilgjengelig ennå.", (4, 40), f, P.GRÅ_LYS)
            return

        pygame.draw.rect(surf, P.BLÅL, (2, 24, W_BASE-4, 8))
        tegn_tekst(surf, "#",      (2,  25), f, P.HVIT)
        tegn_tekst(surf, "SPILLER",(14, 25), f, P.HVIT)
        tegn_tekst(surf, "K",      (158,25), f, P.HVIT)
        tegn_tekst(surf, "MÅL",    (174,25), f, P.HVIT)
        tegn_tekst(surf, "RTG",    (200,25), f, P.HVIT)

        topp = self.tabell._statistikk_register.toppscorere(12)
        for i, stat in enumerate(topp):
            ry = 34 + i * 12
            if ry + 12 > H_BASE - 16:
                break
            farge_rad = (34,34,48) if i % 2 == 0 else (28,28,40)
            pygame.draw.rect(surf, farge_rad, (2, ry, W_BASE-4, 11))
            tegn_tekst(surf, str(i+1),        (2,  ry+2), f, P.GRÅ_LYS)
            tegn_tekst(surf, stat.spiller_navn[:20], (14, ry+2), f, P.KREMHVIT, max_bredde=140)
            tegn_tekst(surf, str(stat.kamper), (158,ry+2), f, P.LYSBLÅ_UI)
            tegn_badge(surf, str(stat.mål),    (172,ry+1), P.GRØNN, P.HVIT, f)
            tegn_tekst(surf, f"{stat.snitt_rating:.1f}", (200,ry+2), f, P.GULT)

    def håndter_event(self, event, ui):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.on_tilbake()
            elif event.key == pygame.K_TAB:
                self._fane = 1 - self._fane
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            # Faner
            for fi in range(2):
                if 2+fi*80 <= mx <= 80+fi*80 and 13 <= my <= 23:
                    self._fane = fi
                    return
            # Tilbake
            if (my >= H_BASE-13 and
                    (W_BASE//2-30)*SKALA <= event.pos[0] <= (W_BASE//2+30)*SKALA):
                self.on_tilbake()


# ─────────────────────────────────────────────────────────────────────────────
# SKJERM: KAMPRAPPORT
# ─────────────────────────────────────────────────────────────────────────────
class KamprapportSkjerm(SkjermData):
    def __init__(self, resultat, hjemme_spillere, borte_spillere,
                 on_ferdig: Callable):
        self.resultat         = resultat
        self.hjemme_spillere  = hjemme_spillere or []
        self.borte_spillere   = borte_spillere or []
        self.on_ferdig        = on_ferdig
        self._fane            = 0   # 0=hendelser 1=statistikk 2=børs
        self._scroll          = 0

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf, P.NAVY)
        f  = Fonter.liten
        fb = Fonter.fet

        r = self.resultat
        _tegn_topplinje(surf, "KAMPRAPPORT", "", r.hjemme_navn[:10] + " vs " + r.borte_navn[:10])

        # Score-banner
        pygame.draw.rect(surf, (10, 20, 60), (4, 13, W_BASE-8, 22))
        pygame.draw.rect(surf, P.BLÅLL, (4, 13, W_BASE-8, 22), 1)

        t_h  = Fonter.stor.render(r.hjemme_navn[:14], False, P.KREMHVIT)
        t_b  = Fonter.stor.render(r.borte_navn[:14],  False, P.KREMHVIT)
        score = f"{r.hjemme_maal}  –  {r.borte_maal}"
        if r.ekstraomganger:
            score += " e.o." if not r.straffer else " str."
        t_s  = Fonter.tittel.render(score, False, P.GULT)

        surf.blit(t_h, (6, 18))
        surf.blit(t_b, (W_BASE - t_b.get_width() - 6, 18))
        surf.blit(t_s, (W_BASE//2 - t_s.get_width()//2, 16))

        # Faner
        fane_navn = ["HENDELSER", "STATISTIKK", "SPILLERBØRS"]
        for fi, navn in enumerate(fane_navn):
            er_aktiv = fi == self._fane
            tegn_knapp(surf, (2 + fi*106, 37, 104, 9), navn, f,
                        valgt=er_aktiv,
                        hovered=(not er_aktiv and
                                 ui.mus_innenfor(((2+fi*106)*SKALA, 37*SKALA,
                                                   104*SKALA, 9*SKALA))))

        innhold_y = 48
        innhold_h = H_BASE - innhold_y - 14

        if self._fane == 0:
            self._tegn_hendelser(surf, innhold_y, innhold_h)
        elif self._fane == 1:
            self._tegn_statistikk(surf, innhold_y, innhold_h)
        else:
            self._tegn_bors(surf, innhold_y, innhold_h)

        tegn_knapp(surf, (W_BASE//2-35, H_BASE-13, 70, 11), "FORTSETT",
                   Fonter.normal,
                   hovered=ui.mus_innenfor(((W_BASE//2-35)*SKALA, (H_BASE-13)*SKALA,
                                             70*SKALA, 11*SKALA)))
        _tegn_bunnlinje(surf, "TAB=FANE  ENTER=FORTSETT")

    def _tegn_hendelser(self, surf, y0, h):
        f = Fonter.liten
        hendelser = sorted(self.resultat.hendelser, key=lambda x: x.minutt)
        synlige   = h // 10
        start     = self._scroll
        ikon_map  = {"mål": "⚽", "gult_kort": "🟨", "rødt_kort": "🟥",
                     "skade": "🚑", "bytte": "🔄"}

        for i, hend in enumerate(hendelser[start:start+synlige]):
            ry  = y0 + i * 10
            farge = (P.GULT if hend.type == "mål" else
                     P.GRÅ_LYS if hend.type == "bytte" else P.KREMHVIT)
            lag_s = "H" if hend.lag == "hjemme" else "B"
            navn  = getattr(hend.spiller, 'etternavn', '?')
            detalj = f" ({hend.detalj})" if hend.detalj else ""
            tegn_tekst(surf, f"{hend.minutt:>3}'  [{lag_s}]  {navn[:16]}{detalj[:20]}",
                       (4, ry), f, farge)

        if not hendelser:
            tegn_tekst(surf, "Ingen hendelser registrert.", (4, y0+10), f, P.GRÅ_MØRK)

        tegn_scrollbar(surf, W_BASE-6, y0, h, len(hendelser), synlige, self._scroll)

    def _tegn_statistikk(self, surf, y0, h):
        f  = Fonter.liten
        fb = Fonter.fet
        s  = self.resultat.statistikk
        r  = self.resultat
        bes_h, bes_b = s.ballbesittelse

        def rad(label, v_h, v_b, ry, farge_v=P.KREMHVIT):
            midtre = W_BASE // 2
            pygame.draw.rect(surf, (28,28,44), (4, ry, W_BASE-8, 9))
            tegn_tekst(surf, str(v_h), (midtre-40, ry+1), f, P.LYSBLÅ_UI)
            tegn_tekst(surf, label,    (midtre - Fonter.liten.size(label)[0]//2, ry+1),
                        f, P.GRÅ_LYS)
            tegn_tekst(surf, str(v_b), (midtre+30, ry+1), f, P.LYSBLÅ_UI)

        rad("Ballbesittelse",  f"{bes_h}%",  f"{bes_b}%",  y0+2)
        rad("Sjanser",         s.sjanser_hjemme,    s.sjanser_borte,    y0+13)
        rad("Skudd",           s.skudd_hjemme,      s.skudd_borte,      y0+24)
        rad("Skudd på mål",    s.skudd_paa_maal_hjemme, s.skudd_paa_maal_borte, y0+35)
        rad("Gule kort",       s.gule_kort_hjemme,  s.gule_kort_borte,  y0+46)
        rad("Røde kort",       s.røde_kort_hjemme,  s.røde_kort_borte,  y0+57)

        # Navnlinje
        pygame.draw.rect(surf, P.BLÅL, (4, y0+70, W_BASE-8, 8))
        t_h = Fonter.liten.render(r.hjemme_navn[:14], False, P.HVIT)
        t_b = Fonter.liten.render(r.borte_navn[:14],  False, P.HVIT)
        surf.blit(t_h, (6, y0+71))
        surf.blit(t_b, (W_BASE - t_b.get_width() - 6, y0+71))

    def _tegn_bors(self, surf, y0, h):
        f  = Fonter.liten
        alle = ([(s, True) for s in self.hjemme_spillere] +
                [(s, False) for s in self.borte_spillere])
        synlige = h // 10
        start   = self._scroll

        pygame.draw.rect(surf, P.BLÅL, (2, y0, W_BASE-4, 8))
        tegn_tekst(surf, "SPILLER",  (4,  y0+1), f, P.HVIT)
        tegn_tekst(surf, "LAG",      (150, y0+1), f, P.HVIT)
        tegn_tekst(surf, "RATING",   (190, y0+1), f, P.HVIT)

        for i, (s, er_hjemme) in enumerate(alle[start:start+synlige]):
            ry     = y0 + 9 + i * 10
            rating = self.resultat.statistikk.hent_rating(s)
            navn   = f"{getattr(s, 'fornavn','?')[0]}. {getattr(s,'etternavn','?')}"
            lag    = self.resultat.hjemme_navn[:6] if er_hjemme else self.resultat.borte_navn[:6]

            farge_rad = (34,34,48) if i%2==0 else (28,28,40)
            pygame.draw.rect(surf, farge_rad, (2, ry, W_BASE-4, 9))

            rtg_farge = (P.GRØNN if rating >= 7.5 else
                         P.GULT  if rating >= 6.5 else
                         P.RØD   if rating < 5.5 else P.GRÅ_LYS)

            tegn_tekst(surf, navn[:20], (4,  ry+1), f, P.KREMHVIT)
            tegn_tekst(surf, lag,       (150,ry+1), f, P.LYSBLÅ_UI)
            tegn_badge(surf, f"{rating:.1f}", (190, ry+1), rtg_farge, P.SVART, f)

        tegn_scrollbar(surf, W_BASE-6, y0+9, h-9, len(alle), synlige, self._scroll)

    def håndter_event(self, event, ui):
        fane_navn  = ["HENDELSER", "STATISTIKK", "SPILLERBØRS"]
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.on_ferdig()
            elif event.key == pygame.K_TAB:
                self._fane = (self._fane + 1) % 3
                self._scroll = 0
            elif event.key == pygame.K_DOWN:
                self._scroll += 1
            elif event.key == pygame.K_UP:
                self._scroll = max(0, self._scroll-1)

        elif event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, self._scroll - event.y)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            for fi in range(3):
                if 2+fi*106 <= mx <= 106+fi*106 and 37 <= my <= 46:
                    self._fane  = fi
                    self._scroll = 0
                    return
            if my >= H_BASE-13:
                self.on_ferdig()


# ─────────────────────────────────────────────────────────────────────────────
# SKJERM: KALENDER-HENDELSE / INFO
# ─────────────────────────────────────────────────────────────────────────────
class InfoSkjerm(SkjermData):
    """Generisk infovisning med tittel + tekstlinjer + fortsett-knapp."""

    def __init__(self, tittel: str, linjer: list[str], on_ferdig: Callable,
                 farge_bakgrunn=None):
        self.tittel_tekst   = tittel
        self.linjer         = linjer
        self.on_ferdig      = on_ferdig
        self.farge_bakgrunn = farge_bakgrunn or P.NAVY

    def tegn(self, surf, ui):
        surf.fill(self.farge_bakgrunn)
        for y in range(H_BASE):
            mørkhet = y // 3
            r, g, b = self.farge_bakgrunn
            pygame.draw.line(surf, (max(0, r-mørkhet//2),
                                    max(0, g-mørkhet//2),
                                    min(255, b+mørkhet//4)),
                             (0, y), (W_BASE, y))

        f  = Fonter.normal
        fb = Fonter.stor

        # Tittelramme
        pygame.draw.rect(surf, (10, 18, 50, 200), (10, 20, W_BASE-20, 30))
        pygame.draw.rect(surf, P.BLÅLL, (10, 20, W_BASE-20, 30), 2)
        t = fb.render(self.tittel_tekst, False, P.GULT)
        surf.blit(t, (W_BASE//2 - t.get_width()//2, 27))

        # Linjer
        for i, linje in enumerate(self.linjer[:10]):
            tegn_tekst(surf, linje, (14, 60 + i*12), f, P.KREMHVIT)

        tegn_knapp(surf, (W_BASE//2-40, H_BASE-20, 80, 14), "FORTSETT →",
                   Fonter.normal,
                   hovered=ui.mus_innenfor(((W_BASE//2-40)*SKALA, (H_BASE-20)*SKALA,
                                             80*SKALA, 14*SKALA)))
        _tegn_bunnlinje(surf, "ENTER / KLIKK FOR Å FORTSETTE")

    def håndter_event(self, event, ui):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.on_ferdig()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            if H_BASE-20 <= my <= H_BASE-6 and W_BASE//2-40 <= mx <= W_BASE//2+40:
                self.on_ferdig()


# ─────────────────────────────────────────────────────────────────────────────
# SKJERM: ANDRE RESULTATER (rask gjennomkjøring)
# ─────────────────────────────────────────────────────────────────────────────
class AndreResultaterSkjerm(SkjermData):
    def __init__(self, resultater: list[tuple[str,int,str,int]], dato_str: str,
                 on_ferdig: Callable):
        self.resultater = resultater   # [(hjemme, h_mål, borte, b_mål), ...]
        self.dato_str   = dato_str
        self.on_ferdig  = on_ferdig

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf, P.NAVY)
        _tegn_topplinje(surf, "RESULTATER", self.dato_str, "")

        f  = Fonter.liten
        fb = Fonter.normal

        for i, (h, hm, b, bm) in enumerate(self.resultater[:14]):
            ry = 18 + i * 12
            farge_rad = (34,34,48) if i % 2 == 0 else (28,28,44)
            pygame.draw.rect(surf, farge_rad, (4, ry, W_BASE-8, 11))
            score = f"{hm} – {bm}"
            tegn_tekst(surf, h[:16],   (6,   ry+2), f, P.KREMHVIT)
            tegn_tekst(surf, score,    (W_BASE//2 - 12, ry+2), fb, P.GULT)
            t_b = f.render(b[:16], False, P.KREMHVIT)
            surf.blit(t_b, (W_BASE - t_b.get_width() - 6, ry+2))

        tegn_knapp(surf, (W_BASE//2-30, H_BASE-14, 60, 12), "OK →",
                   Fonter.normal,
                   hovered=ui.mus_innenfor(((W_BASE//2-30)*SKALA, (H_BASE-14)*SKALA,
                                             60*SKALA, 12*SKALA)))
        _tegn_bunnlinje(surf, "ENTER = FORTSETT")

    def håndter_event(self, event, ui):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE,
                                                           pygame.K_ESCAPE):
            self.on_ferdig()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.on_ferdig()


# ─────────────────────────────────────────────────────────────────────────────
# SKJERM: SESONG SLUTT
# ─────────────────────────────────────────────────────────────────────────────
class SesongsSluttSkjerm(SkjermData):
    def __init__(self, klubb_navn: str, resultater: list[str],
                 tabell, on_avslutt: Callable):
        self.klubb_navn = klubb_navn
        self.resultater = resultater
        self.tabell     = tabell
        self.on_avslutt = on_avslutt

    def tegn(self, surf, ui):
        surf.fill(P.NAVY)
        for y in range(H_BASE):
            t = y / H_BASE
            r = int(20 * (1-t) + 10*t)
            g = int(30 * (1-t) + 20*t)
            b = int(80 * (1-t) + 40*t)
            pygame.draw.line(surf, (r,g,b), (0,y), (W_BASE,y))

        f  = Fonter.normal
        fb = Fonter.stor
        fs = Fonter.liten

        t1 = fb.render("SESONGEN ER OVER", False, P.GULT)
        surf.blit(t1, (W_BASE//2 - t1.get_width()//2, 14))
        pygame.draw.rect(surf, P.BLÅL, (0, 30, W_BASE, 1))

        hist    = self.resultater
        seiere  = hist.count("S")
        uavgjort= hist.count("U")
        tap     = hist.count("T")
        poeng   = seiere*3 + uavgjort

        tegn_tekst(surf, self.klubb_navn, (8, 36), f, P.KREMHVIT)

        stats = [
            ("Kamper spilt:",  str(len(hist))),
            ("Seiere:",        str(seiere)),
            ("Uavgjort:",      str(uavgjort)),
            ("Tap:",           str(tap)),
            ("Poeng:",         str(poeng)),
        ]
        for i, (label, verdi) in enumerate(stats):
            ry = 50 + i*12
            tegn_tekst(surf, label, (8, ry), fs, P.GRÅ_LYS)
            tegn_tekst(surf, verdi, (130, ry), f, P.GULT)

        # Tabellplassering
        if self.tabell:
            plass = self.tabell.plass(self.klubb_navn)
            pygame.draw.rect(surf, (10, 18, 50), (4, 118, W_BASE-8, 16))
            tegn_tekst(surf, f"ENDELIG TABELLPLASS: {plass}. PLASS",
                        (8, 122), f, P.CYANL)

        tegn_knapp(surf, (W_BASE//2-40, H_BASE-20, 80, 14), "AVSLUTT",
                   Fonter.normal,
                   hovered=ui.mus_innenfor(((W_BASE//2-40)*SKALA, (H_BASE-20)*SKALA,
                                             80*SKALA, 14*SKALA)))

    def håndter_event(self, event, ui):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self.on_avslutt()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            if H_BASE-20 <= my <= H_BASE-6:
                self.on_avslutt()


# ─────────────────────────────────────────────────────────────────────────────
# UI-MOTOR  (hoved event-loop, skjermstack, skalering)
# ─────────────────────────────────────────────────────────────────────────────
class UIMotor:
    """
    Hoved-UIMotor.
    - Holder en skjermstack — øverste skjerm er aktiv
    - Skalerer 320×200 base-canvas til W×H skjerm
    - Tilbyr push/pop_skjerm for navigasjon
    - Kjøres av spillmotor.py via start() / ett steg om gangen
    """

    def __init__(self):
        pygame.init()
        Fonter.init()
        self._skjerm     = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITTEL)
        self._klokke     = pygame.time.Clock()
        self._base       = pygame.Surface((W_BASE, H_BASE))
        self._stack: list[SkjermData] = []
        self._kjører     = True
        self._mus_pos    = (0, 0)
        pygame.mouse.set_visible(True)

    # ── Navigasjon ────────────────────────────────────────────────────────────
    def push_skjerm(self, skjerm: SkjermData):
        self._stack.append(skjerm)

    def pop_skjerm(self) -> Optional[SkjermData]:
        if self._stack:
            return self._stack.pop()
        return None

    def bytt_skjerm(self, skjerm: SkjermData):
        """Erstatter øverste skjerm (ingen tilbake-mulighet)."""
        if self._stack:
            self._stack[-1] = skjerm
        else:
            self._stack.append(skjerm)

    def tøm_og_sett(self, skjerm: SkjermData):
        """Tøm stakken og sett ny root-skjerm."""
        self._stack.clear()
        self._stack.append(skjerm)

    # ── Hjelpere ──────────────────────────────────────────────────────────────
    def base_mus(self) -> tuple[int, int]:
        """Returnerer museposisjon i base-koordinater (320×200)."""
        mx, my = self._mus_pos
        return (mx // SKALA, my // SKALA)

    def mus_innenfor(self, rect_skalert: tuple) -> bool:
        """Sjekker om mus er innenfor en rekt i skalerte koordinater."""
        x, y, w, h = rect_skalert
        mx, my = self._mus_pos
        return x <= mx < x+w and y <= my < y+h

    def avslutt(self):
        self._kjører = False

    # ── Hoved event-loop ──────────────────────────────────────────────────────
    def tikk(self) -> bool:
        """
        Kjør én frame. Returnerer True mens spillet kjører.
        Kalles av spillmotor.py i sin game-loop.
        """
        self._klokke.tick(FPS)
        self._mus_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._kjører = False
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()

            if self._stack:
                self._stack[-1].håndter_event(event, self)

        # Tegn øverste skjerm
        self._base.fill(P.GRÅ_PANEL)
        if self._stack:
            self._stack[-1].tegn(self._base, self)

        # Skaler til vindu
        pygame.transform.scale(self._base, (W, H), self._skjerm)
        pygame.display.flip()

        return self._kjører

    def start_modal(self, skjerm: SkjermData) -> None:
        """
        Blokkerende modal: kjør UI-loop til skjermen popper seg selv.
        Brukes av spillmotor for å avvente brukerinput.
        """
        self.push_skjerm(skjerm)
        ferdig = False

        original_callback = None
        # Pakk callback i en ferdig-setter
        if hasattr(skjerm, 'on_ferdig'):
            original_callback = skjerm.on_ferdig
            def ferdig_wrapper(*args, **kwargs):
                nonlocal ferdig
                ferdig = True
                if original_callback:
                    original_callback(*args, **kwargs)
            skjerm.on_ferdig = ferdig_wrapper

        while not ferdig and self._kjører:
            self.tikk()
        self.pop_skjerm()

    def kjør_til_valg(self, skjerm: SkjermData) -> Any:
        """
        Kjør modal og returner resultat.
        Skjermen setter self._resultat og kaller on_ferdig().
        """
        self.push_skjerm(skjerm)
        while self._kjører:
            if not self.tikk():
                break
            if hasattr(skjerm, '_ferdig') and skjerm._ferdig:
                break
        self.pop_skjerm()
        return getattr(skjerm, '_resultat', None)
