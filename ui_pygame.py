"""
ui_pygame.py  —  Norsk Football Manager
Championship Manager 01/02-inspired graphical interface.
Clean, flat, information-dense. 1024x768 @ 1x scaling.
"""

from __future__ import annotations

import pygame
import sys
from typing import Callable, Optional, Any
from dataclasses import dataclass, field

# ─────────────────────────────────────────────────────────────────────────────
# SCREEN CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
W_BASE = W = 1024
H_BASE = H = 768
SKALA       = 1
FPS         = 60
TITTEL      = "Norsk Football Manager"

# ─────────────────────────────────────────────────────────────────────────────
# COLOR PALETTE  (CM 01/02 style)
# ─────────────────────────────────────────────────────────────────────────────
class P:
    SVART       = (  0,   0,   0)
    BAKGRUNN    = ( 18,  22,  38)
    PANEL       = ( 26,  32,  54)
    PANEL_LYS   = ( 36,  44,  70)
    HEADER      = ( 10,  14,  30)
    HEADER_KANT = ( 55,  85, 155)
    RAD_MØRK    = ( 22,  28,  46)
    RAD_LYS     = ( 28,  36,  58)
    RAD_HOVER   = ( 42,  58,  98)
    RAD_VALGT   = ( 48,  80, 155)
    KOL_HEADER  = ( 14,  20,  40)
    HVIT        = (245, 245, 250)
    TEKST       = (210, 215, 232)
    TEKST_SVAK  = (120, 132, 160)
    GULT        = (255, 210,  50)
    GULTL       = (255, 230, 120)
    RØD         = (200,  60,  60)
    RØDL        = (240, 120, 120)
    GRØNN       = ( 60, 180,  80)
    GRØNNL      = (120, 210, 130)
    BLÅ         = ( 55,  85, 155)
    BLÅL        = ( 90, 130, 210)
    BLÅLL       = (140, 180, 240)
    CYAN        = ( 80, 200, 210)
    ORANSJE     = (220, 140,  50)
    # Compatibility aliases
    NAVY        = ( 18,  22,  38)
    GRÅ_PANEL   = ( 26,  32,  54)
    GRÅ_MØRK    = ( 50,  58,  80)
    GRÅ_LYS     = (140, 152, 180)
    KREMHVIT    = (210, 215, 232)
    LYSBLÅ_UI   = (140, 180, 240)
    CYANL       = ( 80, 200, 210)


# ─────────────────────────────────────────────────────────────────────────────
# FONTS
# ─────────────────────────────────────────────────────────────────────────────
class Fonter:
    tittel = None  # 28pt bold
    stor   = None  # 20pt bold
    fet    = None  # 15pt bold
    normal = None  # 14pt
    liten  = None  # 13pt

    @classmethod
    def init(cls):
        def _f(size, bold=False):
            for navn in ["arial", "dejavusans", "freesans", "ubuntu"]:
                try:
                    f = pygame.font.SysFont(navn, size, bold=bold)
                    if f:
                        return f
                except Exception:
                    pass
            return pygame.font.SysFont(None, size, bold=bold)
        cls.tittel = _f(28, bold=True)
        cls.stor   = _f(20, bold=True)
        cls.fet    = _f(15, bold=True)
        cls.normal = _f(14)
        cls.liten  = _f(13)


# ─────────────────────────────────────────────────────────────────────────────
# BACKGROUND CACHE WITH PITCH WATERMARK
# ─────────────────────────────────────────────────────────────────────────────
_BAKGRUNN_CACHE = None


def _lag_bakgrunn():
    surf = pygame.Surface((W_BASE, H_BASE))
    surf.fill(P.BAKGRUNN)
    kf = (P.BAKGRUNN[0] + 8, P.BAKGRUNN[1] + 10, P.BAKGRUNN[2] + 14)
    cx, cy = W_BASE // 2, H_BASE // 2
    pw, ph = 820, 580
    px, py = cx - pw // 2, cy - ph // 2
    pygame.draw.rect(surf, kf, (px, py, pw, ph), 1)
    pygame.draw.line(surf, kf, (cx, py), (cx, py + ph))
    pygame.draw.circle(surf, kf, (cx, cy), 90, 1)
    pygame.draw.circle(surf, kf, (cx, cy), 3)
    pbw, pbh = 160, 260
    pygame.draw.rect(surf, kf, (px, cy - pbh // 2, pbw, pbh), 1)
    pygame.draw.rect(surf, kf, (px + pw - pbw, cy - pbh // 2, pbw, pbh), 1)
    gbw, gbh = 60, 130
    pygame.draw.rect(surf, kf, (px, cy - gbh // 2, gbw, gbh), 1)
    pygame.draw.rect(surf, kf, (px + pw - gbw, cy - gbh // 2, gbw, gbh), 1)
    return surf


def _tegn_bakgrunn(surf, farge=None):
    global _BAKGRUNN_CACHE
    if farge and farge != P.BAKGRUNN:
        surf.fill(farge)
        return
    if _BAKGRUNN_CACHE is None:
        _BAKGRUNN_CACHE = _lag_bakgrunn()
    surf.blit(_BAKGRUNN_CACHE, (0, 0))


# ─────────────────────────────────────────────────────────────────────────────
# PRIMITIVES
# ─────────────────────────────────────────────────────────────────────────────
def tegn_tekst(surf, tekst, pos, font, farge=P.TEKST, max_bredde=0):
    """Renders text with antialias, clips with '...' if max_bredde is set."""
    if max_bredde > 0:
        while font.size(tekst)[0] > max_bredde and len(tekst) > 3:
            tekst = tekst[:-4] + "..."
    t = font.render(tekst, True, farge)
    surf.blit(t, pos)
    return t.get_width()


def tegn_linje_h(surf, farge, x, y, bredde, tykkelse=1):
    pygame.draw.rect(surf, farge, (x, y, bredde, tykkelse))


def tegn_knapp(surf, rect, tekst, font, aktiv=True, valgt=False, hovered=False):
    """Flat button with centered text, color change on hover/active."""
    x, y, w, h = rect
    if not aktiv:
        bunn = P.PANEL
        tkfarge = P.TEKST_SVAK
        kant = P.GRÅ_MØRK
    elif valgt:
        bunn = P.BLÅ
        tkfarge = P.HVIT
        kant = P.BLÅLL
    elif hovered:
        bunn = P.PANEL_LYS
        tkfarge = P.HVIT
        kant = P.BLÅL
    else:
        bunn = P.PANEL
        tkfarge = P.TEKST
        kant = P.GRÅ_MØRK
    pygame.draw.rect(surf, bunn, rect)
    pygame.draw.rect(surf, kant, rect, 1)
    t = font.render(tekst, True, tkfarge)
    tw, th = t.get_size()
    surf.blit(t, (x + (w - tw) // 2, y + (h - th) // 2))


def tegn_kondisjon_bar(surf, x, y, bredde, kond: float, skadet: bool = False):
    """Horizontal condition bar, 8px high."""
    h = 8
    pygame.draw.rect(surf, P.GRÅ_MØRK, (x, y, bredde, h))
    if skadet:
        farge = P.RØD
        fylt = bredde
    else:
        andel = max(0.0, min(1.0, kond / 100.0))
        fylt = int(bredde * andel)
        if kond >= 90:
            farge = P.GRØNN
        elif kond >= 75:
            farge = P.GULT
        elif kond >= 60:
            farge = P.ORANSJE
        else:
            farge = P.RØD
    if fylt > 0:
        pygame.draw.rect(surf, farge, (x, y, fylt, h))


def tegn_scrollbar(surf, x, y, h_total, antall, synlige, scroll):
    """6px wide vertical scrollbar."""
    w = 6
    if antall <= synlige:
        return
    pygame.draw.rect(surf, P.PANEL_LYS, (x, y, w, h_total))
    thumb_h = max(16, int(h_total * synlige / antall))
    maks_scroll = antall - synlige
    thumb_y = y + int((h_total - thumb_h) * scroll / max(1, maks_scroll))
    pygame.draw.rect(surf, P.BLÅL, (x, thumb_y, w, thumb_h))


def tegn_badge(surf, tekst, pos, farge_bunn, farge_tekst, font):
    """Small colored box with text."""
    if font is None:
        font = Fonter.liten
    t = font.render(tekst, True, farge_tekst)
    tw, th = t.get_size()
    pad = 3
    pygame.draw.rect(surf, farge_bunn, (pos[0] - pad, pos[1] - 1, tw + pad * 2, th + 2))
    surf.blit(t, pos)


def tegn_bane(surf, rect, farge_gress=(34, 100, 50), farge_linje=(200, 230, 200)):
    """Top-down football pitch."""
    x, y, w, h = rect
    pygame.draw.rect(surf, farge_gress, rect)
    # Alternating grass stripes
    stripe_w = w // 10
    for i in range(10):
        if i % 2 == 0:
            sx = x + i * stripe_w
            sw = min(stripe_w, x + w - sx)
            lighter = (min(255, farge_gress[0] + 6),
                       min(255, farge_gress[1] + 8),
                       min(255, farge_gress[2] + 6))
            pygame.draw.rect(surf, lighter, (sx, y, sw, h))
    # Outline
    pygame.draw.rect(surf, farge_linje, (x, y, w, h), 1)
    # Halfway line
    mx = x + w // 2
    pygame.draw.line(surf, farge_linje, (mx, y + 2), (mx, y + h - 2), 1)
    # Centre circle
    r = min(w, h) // 7
    pygame.draw.circle(surf, farge_linje, (mx, y + h // 2), r, 1)
    pygame.draw.circle(surf, farge_linje, (mx, y + h // 2), 2)
    # Penalty boxes
    pb_w, pb_h = w // 6, h // 3
    pygame.draw.rect(surf, farge_linje, (x + 1, y + h // 2 - pb_h // 2, pb_w, pb_h), 1)
    pygame.draw.rect(surf, farge_linje, (x + w - pb_w - 1, y + h // 2 - pb_h // 2, pb_w, pb_h), 1)
    # Goal boxes
    gb_w, gb_h = pb_w // 2, pb_h // 2
    pygame.draw.rect(surf, farge_linje, (x + 1, y + h // 2 - gb_h // 2, gb_w, gb_h), 1)
    pygame.draw.rect(surf, farge_linje, (x + w - gb_w - 1, y + h // 2 - gb_h // 2, gb_w, gb_h), 1)


# Formation coordinates (normalized 0..1, horizontal pitch, left=defense right=attack)
FORMASJON_KOORDINATER = {
    "4-3-3": [
        (0.05, 0.50),
        (0.22, 0.15), (0.22, 0.40), (0.22, 0.60), (0.22, 0.85),
        (0.50, 0.25), (0.50, 0.50), (0.50, 0.75),
        (0.78, 0.15), (0.78, 0.50), (0.78, 0.85),
    ],
    "4-4-2": [
        (0.05, 0.50),
        (0.22, 0.15), (0.22, 0.40), (0.22, 0.60), (0.22, 0.85),
        (0.50, 0.15), (0.50, 0.38), (0.50, 0.62), (0.50, 0.85),
        (0.78, 0.35), (0.78, 0.65),
    ],
    "4-2-3-1": [
        (0.05, 0.50),
        (0.22, 0.15), (0.22, 0.40), (0.22, 0.60), (0.22, 0.85),
        (0.44, 0.35), (0.44, 0.65),
        (0.62, 0.15), (0.62, 0.50), (0.62, 0.85),
        (0.82, 0.50),
    ],
    "3-5-2": [
        (0.05, 0.50),
        (0.22, 0.28), (0.22, 0.50), (0.22, 0.72),
        (0.50, 0.10), (0.50, 0.30), (0.50, 0.50), (0.50, 0.70), (0.50, 0.90),
        (0.78, 0.35), (0.78, 0.65),
    ],
    "3-4-3": [
        (0.05, 0.50),
        (0.22, 0.28), (0.22, 0.50), (0.22, 0.72),
        (0.50, 0.20), (0.50, 0.43), (0.50, 0.57), (0.50, 0.80),
        (0.78, 0.15), (0.78, 0.50), (0.78, 0.85),
    ],
    "5-3-2": [
        (0.05, 0.50),
        (0.20, 0.10), (0.20, 0.32), (0.20, 0.50), (0.20, 0.68), (0.20, 0.90),
        (0.50, 0.25), (0.50, 0.50), (0.50, 0.75),
        (0.78, 0.35), (0.78, 0.65),
    ],
    "4-1-4-1": [
        (0.05, 0.50),
        (0.22, 0.15), (0.22, 0.40), (0.22, 0.60), (0.22, 0.85),
        (0.42, 0.50),
        (0.62, 0.15), (0.62, 0.38), (0.62, 0.62), (0.62, 0.85),
        (0.82, 0.50),
    ],
}


def tegn_formasjon_på_bane(surf, rect, spillere: list, formasjon_navn: str,
                            valgt_idx: int = -1, font=None):
    """Draws player dots on a miniature pitch."""
    tegn_bane(surf, rect)
    x0, y0, bw, bh = rect
    if font is None:
        font = Fonter.liten

    koord = FORMASJON_KOORDINATER.get(formasjon_navn)
    if not koord:
        koord = [(0.05 + i * 0.09, 0.50) for i in range(11)]

    for i, spiller in enumerate(spillere[:11]):
        if i >= len(koord):
            break
        nx, ny = koord[i]
        cx = int(x0 + nx * bw)
        cy = int(y0 + ny * bh)

        farge = P.GULT if i == valgt_idx else P.HVIT
        pygame.draw.circle(surf, P.SVART, (cx, cy), 8)
        pygame.draw.circle(surf, farge, (cx, cy), 7)

        navn = getattr(spiller, 'etternavn', '?')[:5]
        t = font.render(navn, True, P.HVIT)
        surf.blit(t, (cx - t.get_width() // 2, cy + 9))


# ─────────────────────────────────────────────────────────────────────────────
# SHARED HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _tegn_topplinje(surf, venstre: str, midtre: str, høyre: str, font=None, is_pauset: bool = False):
    """28px top bar with three text areas."""
    if font is None:
        font = Fonter.liten
    pygame.draw.rect(surf, P.HEADER, (0, 0, W_BASE, 28))
    tegn_linje_h(surf, P.HEADER_KANT, 0, 27, W_BASE, 1)

    tegn_tekst(surf, venstre, (6, 7), font, P.GULT)
    mid_t = font.render(midtre, True, P.TEKST)
    surf.blit(mid_t, (W_BASE // 2 - mid_t.get_width() // 2, 7))
    høyre_t = font.render(høyre, True, P.TEKST_SVAK)
    surf.blit(høyre_t, (W_BASE - høyre_t.get_width() - 6, 7))

    if is_pauset:
        pygame.draw.rect(surf, P.GULT, (W_BASE - 70, 4, 66, 20))
        tegn_tekst(surf, "PAUSET", (W_BASE - 68, 8), font, P.SVART)


def _tegn_bunnlinje(surf, tekst: str, font=None):
    """22px bottom status bar."""
    if font is None:
        font = Fonter.liten
    pygame.draw.rect(surf, P.HEADER, (0, H_BASE - 22, W_BASE, 22))
    tegn_linje_h(surf, P.HEADER_KANT, 0, H_BASE - 22, W_BASE, 1)
    tegn_tekst(surf, tekst, (8, H_BASE - 16), font, P.TEKST_SVAK)


def _tegn_kolonne_header(surf, kolonner, y=28, h=22):
    """Draw column header row."""
    pygame.draw.rect(surf, P.KOL_HEADER, (0, y, W_BASE, h))
    tegn_linje_h(surf, P.HEADER_KANT, 0, y + h - 1, W_BASE, 1)
    f = Fonter.liten
    for tekst, x in kolonner:
        tegn_tekst(surf, tekst, (x + 4, y + 4), f, P.TEKST_SVAK)


# ─────────────────────────────────────────────────────────────────────────────
# BASE SCREEN CLASS
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class SkjermData:
    """Abstract display unit — subclasses draw themselves."""

    def tegn(self, surf: pygame.Surface, ui: "UIMotor") -> None:
        raise NotImplementedError

    def håndter_event(self, event: pygame.event.Event, ui: "UIMotor") -> None:
        raise NotImplementedError



# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: CREATE MANAGER
# ─────────────────────────────────────────────────────────────────────────────
class OpprettManagerSkjerm(SkjermData):
    """
    Shown once at new season, after club is selected.
    Player types in first and last name.
    """
    def __init__(self, klubb_navn: str, on_ferdig: Callable[[str, str], None]):
        self.klubb_navn  = klubb_navn
        self.on_ferdig   = on_ferdig
        self.fornavn     = ""
        self.etternavn   = ""
        self._aktiv_felt = 0  # 0=fornavn, 1=etternavn

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)

        fb = Fonter.stor
        f  = Fonter.normal
        fs = Fonter.liten

        # Title header
        pygame.draw.rect(surf, P.HEADER, (0, 0, W_BASE, 60))
        tegn_linje_h(surf, P.HEADER_KANT, 0, 59, W_BASE, 2)
        t1 = Fonter.tittel.render("NORSK FOOTBALL MANAGER", True, P.GULT)
        surf.blit(t1, (W_BASE // 2 - t1.get_width() // 2, 14))

        # Subtitle
        t2 = fb.render(f"NY MANAGER — {self.klubb_navn.upper()}", True, P.TEKST)
        surf.blit(t2, (W_BASE // 2 - t2.get_width() // 2, 80))

        cx = W_BASE // 2
        field_w = 320
        field_x = cx - field_w // 2

        # Field 0: First name
        label0 = fs.render("FORNAVN", True, P.TEKST_SVAK)
        surf.blit(label0, (field_x, 148))
        pygame.draw.rect(surf, P.PANEL, (field_x, 164, field_w, 34))
        kant0 = P.GULT if self._aktiv_felt == 0 else P.GRÅ_MØRK
        pygame.draw.rect(surf, kant0, (field_x, 164, field_w, 34), 1)
        vis0 = self.fornavn + ("|" if self._aktiv_felt == 0 else "")
        tegn_tekst(surf, vis0, (field_x + 10, 172), f, P.HVIT)

        # Field 1: Last name
        label1 = fs.render("ETTERNAVN", True, P.TEKST_SVAK)
        surf.blit(label1, (field_x, 222))
        pygame.draw.rect(surf, P.PANEL, (field_x, 238, field_w, 34))
        kant1 = P.GULT if self._aktiv_felt == 1 else P.GRÅ_MØRK
        pygame.draw.rect(surf, kant1, (field_x, 238, field_w, 34), 1)
        vis1 = self.etternavn + ("|" if self._aktiv_felt == 1 else "")
        tegn_tekst(surf, vis1, (field_x + 10, 246), f, P.HVIT)

        begge_fylt = len(self.fornavn) >= 2 and len(self.etternavn) >= 2

        knapp_rect = (cx - 100, 310, 200, 36)
        tegn_knapp(surf, knapp_rect, "BEKREFT", f,
                   aktiv=begge_fylt,
                   hovered=begge_fylt and ui.mus_innenfor(knapp_rect))

        _tegn_bunnlinje(surf, "TAB = BYTT FELT   ENTER = BEKREFT")

    def håndter_event(self, event, ui):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            if W_BASE // 2 - 160 <= mx <= W_BASE // 2 + 160:
                if 164 <= my <= 198:
                    self._aktiv_felt = 0
                elif 238 <= my <= 272:
                    self._aktiv_felt = 1
            begge_fylt = len(self.fornavn) >= 2 and len(self.etternavn) >= 2
            if begge_fylt and W_BASE // 2 - 100 <= mx <= W_BASE // 2 + 100 and 310 <= my <= 346:
                self.on_ferdig(self.fornavn, self.etternavn)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self._aktiv_felt = 1 - self._aktiv_felt
            elif event.key == pygame.K_RETURN:
                if self._aktiv_felt == 0:
                    self._aktiv_felt = 1
                else:
                    if len(self.fornavn) >= 2 and len(self.etternavn) >= 2:
                        self.on_ferdig(self.fornavn, self.etternavn)
            elif event.key == pygame.K_BACKSPACE:
                if self._aktiv_felt == 0:
                    self.fornavn = self.fornavn[:-1]
                else:
                    self.etternavn = self.etternavn[:-1]
            else:
                char = event.unicode
                if char.isalpha() or char in " -":
                    if self._aktiv_felt == 0 and len(self.fornavn) < 24:
                        self.fornavn += char
                    elif self._aktiv_felt == 1 and len(self.etternavn) < 24:
                        self.etternavn += char


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: MAIN MENU / SPLASH
# ─────────────────────────────────────────────────────────────────────────────
class HovedmenySkjerm(SkjermData):
    def __init__(self, on_start: Callable, on_avslutt: Callable):
        self.on_start   = on_start
        self.on_avslutt = on_avslutt
        self._tick      = 0

    def tegn(self, surf, ui):
        self._tick += 1
        _tegn_bakgrunn(surf)

        # Logo box
        logo_x, logo_y = W_BASE // 2 - 300, 100
        logo_w, logo_h = 600, 220
        pygame.draw.rect(surf, P.PANEL, (logo_x, logo_y, logo_w, logo_h))
        pygame.draw.rect(surf, P.HEADER_KANT, (logo_x, logo_y, logo_w, logo_h), 1)
        tegn_linje_h(surf, P.HEADER_KANT, logo_x, logo_y + 2, logo_w, 2)

        t1 = Fonter.tittel.render("NORSK FOOTBALL MANAGER", True, P.GULT)
        surf.blit(t1, (W_BASE // 2 - t1.get_width() // 2, logo_y + 40))

        t2 = Fonter.stor.render("Basert på norsk fotball", True, P.TEKST_SVAK)
        surf.blit(t2, (W_BASE // 2 - t2.get_width() // 2, logo_y + 90))

        t3 = Fonter.normal.render("2025 SESONG", True, P.CYAN)
        surf.blit(t3, (W_BASE // 2 - t3.get_width() // 2, logo_y + 130))

        # Pulsating prompt
        if (self._tick // 30) % 2 == 0:
            tp = Fonter.normal.render("TRYKK ENTER FOR Å STARTE", True, P.TEKST)
            surf.blit(tp, (W_BASE // 2 - tp.get_width() // 2, logo_y + 175))

        # Buttons
        btn_y = 380
        btn_w, btn_h = 180, 44
        start_rect  = (W_BASE // 2 - 200, btn_y, btn_w, btn_h)
        avslutt_rect= (W_BASE // 2 + 20,  btn_y, btn_w, btn_h)

        tegn_knapp(surf, start_rect, "START", Fonter.stor,
                   hovered=ui.mus_innenfor(start_rect))
        tegn_knapp(surf, avslutt_rect, "AVSLUTT", Fonter.stor,
                   hovered=ui.mus_innenfor(avslutt_rect))

        _tegn_bunnlinje(surf, "NORSK FOOTBALL MANAGER")

    def håndter_event(self, event, ui):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.on_start()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            btn_y = 380
            btn_w, btn_h = 180, 44
            if W_BASE // 2 - 200 <= mx <= W_BASE // 2 - 20 and btn_y <= my <= btn_y + btn_h:
                self.on_start()
            elif W_BASE // 2 + 20 <= mx <= W_BASE // 2 + 200 and btn_y <= my <= btn_y + btn_h:
                self.on_avslutt()



# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: SELECT CLUB
# ─────────────────────────────────────────────────────────────────────────────
class VelgKlubbSkjerm(SkjermData):
    SYNLIGE = 25

    def __init__(self, klubber: list, on_valgt: Callable[[Any], None]):
        self.klubber  = klubber
        self.on_valgt = on_valgt
        self._scroll  = 0
        self._valgt   = -1
        self._sist_klikk_idx = -1
        self._sist_klikk_tid = 0

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)
        _tegn_topplinje(surf, "NFM", "VELG KLUBB", f"{sum(1 for k in self.klubber if not isinstance(k, str))} KLUBBER")

        # Column headers
        kolonner = [("KLUBB", 4), ("STJERNER", 420), ("STADION KAP.", 580)]
        _tegn_kolonne_header(surf, kolonner, y=28, h=22)

        rad_h = 26
        y0    = 50
        start = self._scroll
        slutt = min(start + self.SYNLIGE, len(self.klubber))
        mx, my = ui.base_mus()

        for i, idx in enumerate(range(start, slutt)):
            k  = self.klubber[idx]
            ry = y0 + i * rad_h

            if isinstance(k, str):
                # Division separator
                pygame.draw.rect(surf, P.HEADER, (0, ry, W_BASE, rad_h - 1))
                tegn_linje_h(surf, P.HEADER_KANT, 0, ry + rad_h - 1, W_BASE, 1)
                tl = Fonter.fet.render(f"  {k.upper()}", True, P.BLÅLL)
                surf.blit(tl, (8, ry + 4))
                continue

            er_hover = (0 <= mx <= W_BASE - 8 and ry <= my < ry + rad_h)
            er_valgt = (idx == self._valgt)

            if er_valgt:
                pygame.draw.rect(surf, P.RAD_VALGT, (0, ry, W_BASE - 8, rad_h - 1))
            elif er_hover:
                pygame.draw.rect(surf, P.RAD_HOVER, (0, ry, W_BASE - 8, rad_h - 1))
            elif i % 2 == 0:
                pygame.draw.rect(surf, P.RAD_MØRK, (0, ry, W_BASE - 8, rad_h - 1))
            else:
                pygame.draw.rect(surf, P.RAD_LYS, (0, ry, W_BASE - 8, rad_h - 1))

            navn    = getattr(k, 'navn', str(k))
            styrke  = getattr(k, 'historisk_styrke', 0)
            stadion = getattr(k, 'stadion', None)
            kap     = getattr(stadion, 'kapasitet', 0) if stadion else 0
            stjerner_full = min(5, styrke // 4)
            stjerner_str  = "★" * stjerner_full + "☆" * (5 - stjerner_full)
            divisjon = getattr(k, 'divisjon', '')

            tkfarge = P.HVIT if er_valgt else P.TEKST
            tegn_tekst(surf, navn, (8, ry + 5), Fonter.normal, tkfarge, max_bredde=390)
            tegn_tekst(surf, stjerner_str, (424, ry + 5), Fonter.liten, P.GULT)
            tegn_tekst(surf, f"{kap:,}", (584, ry + 5), Fonter.liten, P.TEKST_SVAK)

        # Scrollbar
        tegn_scrollbar(surf, W_BASE - 8, y0, self.SYNLIGE * rad_h,
                        len(self.klubber), self.SYNLIGE, self._scroll)

        # Confirm button
        aktiv = self._valgt >= 0 and not isinstance(self.klubber[self._valgt], str)
        btn_rect = (W_BASE // 2 - 120, H_BASE - 46, 240, 36)
        tegn_knapp(surf, btn_rect, "VELG KLUBB", Fonter.stor,
                   aktiv=aktiv,
                   hovered=aktiv and ui.mus_innenfor(btn_rect))

        _tegn_bunnlinje(surf, "↑↓ / SCROLL = NAVIGER   ENTER / DOBBELT-KLIKK = VELG")

    def håndter_event(self, event, ui):
        maks_scroll = max(0, len(self.klubber) - self.SYNLIGE)

        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, min(maks_scroll, self._scroll - event.y))

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            rad_h, y0 = 26, 50
            now = pygame.time.get_ticks()

            # Row clicks
            for i in range(self.SYNLIGE):
                idx = self._scroll + i
                if idx >= len(self.klubber):
                    break
                k = self.klubber[idx]
                if isinstance(k, str):
                    continue
                ry = y0 + i * rad_h
                if 0 <= mx <= W_BASE - 8 and ry <= my < ry + rad_h:
                    if self._sist_klikk_idx == idx and now - self._sist_klikk_tid < 500:
                        self.on_valgt(self.klubber[idx])
                        return
                    self._valgt = idx
                    self._sist_klikk_idx = idx
                    self._sist_klikk_tid = now
                    break

            # Confirm button
            btn_rect = (W_BASE // 2 - 120, H_BASE - 46, 240, 36)
            bx, by, bw, bh = btn_rect
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                if self._valgt >= 0 and not isinstance(self.klubber[self._valgt], str):
                    self.on_valgt(self.klubber[self._valgt])

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                start_sok = max(0, self._valgt)
                for nv in range(start_sok + 1, len(self.klubber)):
                    if not isinstance(self.klubber[nv], str):
                        self._valgt = nv
                        if self._valgt >= self._scroll + self.SYNLIGE:
                            self._scroll = min(maks_scroll, self._valgt - self.SYNLIGE + 1)
                        break
            elif event.key == pygame.K_UP:
                if self._valgt > 0:
                    for nv in range(self._valgt - 1, -1, -1):
                        if not isinstance(self.klubber[nv], str):
                            self._valgt = nv
                            if self._valgt < self._scroll:
                                self._scroll = max(0, self._valgt)
                            break
                elif self._valgt == -1 and self.klubber:
                    for nv in range(len(self.klubber)):
                        if not isinstance(self.klubber[nv], str):
                            self._valgt = nv
                            break
            elif event.key == pygame.K_RETURN and self._valgt >= 0:
                if not isinstance(self.klubber[self._valgt], str):
                    self.on_valgt(self.klubber[self._valgt])



# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: MANAGER HUB (landing page)
# ─────────────────────────────────────────────────────────────────────────────
class HubSkjerm(SkjermData):
    """
    Persistent manager dashboard — the "home base" between events.
    Shows club status, next match, navigation and a mini league table.
    """

    def __init__(self, spiller_klubb, dato, tabeller: dict,
                 uleste_antall: int, manager_navn: str,
                 neste_kamp=None,           # (dato, kamp) or None
                 siste_resultat=None,       # (hjemme_navn, h_maal, borte_navn, b_maal) or None
                 on_innboks: Callable = None,
                 on_spillerstall: Callable = None,
                 on_tabell: Callable = None,
                 on_terminliste: Callable = None,
                 on_laguttak: Callable = None,
                 on_klubbinfo: Callable = None,
                 on_fortsett: Callable = None):
        self.spiller_klubb  = spiller_klubb
        self.dato           = dato
        self.tabeller       = tabeller
        self.uleste_antall  = uleste_antall
        self.manager_navn   = manager_navn
        self.neste_kamp     = neste_kamp        # (dato, kamp) or None
        self.siste_resultat = siste_resultat    # (h, hm, b, bm) or None
        self.on_innboks     = on_innboks     or (lambda: None)
        self.on_spillerstall= on_spillerstall or (lambda: None)
        self.on_tabell      = on_tabell      or (lambda: None)
        self.on_terminliste = on_terminliste or (lambda: None)
        self.on_laguttak    = on_laguttak    or (lambda: None)
        self.on_klubbinfo   = on_klubbinfo   or (lambda: None)
        self.on_fortsett    = on_fortsett    or (lambda: None)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _nav_rader(self):
        innboks_tekst = f"F1   INNBOKS"
        if self.uleste_antall > 0:
            innboks_tekst += f"  [{self.uleste_antall} NY]"
        return [
            (innboks_tekst,       self.on_innboks,       self.uleste_antall > 0),
            ("F2   SPILLERSTALL", self.on_spillerstall,  False),
            ("F3   SERIATABELL",  self.on_tabell,        False),
            ("F4   TERMINLISTE",  self.on_terminliste,   False),
            ("F5   LAGUTTAK & TAKTIKK", self.on_laguttak, False),
            ("F6   KLUBBINFO",    self.on_klubbinfo,     False),
        ]

    def _mini_tabell(self):
        """Return up to 6 sorted rows from player's division table."""
        div = getattr(self.spiller_klubb, 'divisjon', '')
        tabell = self.tabeller.get(div)
        if not tabell:
            return []
        return tabell.sorter()[:6]

    def _tabell_plass(self):
        div = getattr(self.spiller_klubb, 'divisjon', '')
        tabell = self.tabeller.get(div)
        if tabell:
            return tabell.plass(getattr(self.spiller_klubb, 'navn', ''))
        return -1

    # ── Drawing ───────────────────────────────────────────────────────────────

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)

        dato_str = self.dato.strftime('%d.%m.%Y') if self.dato else ""
        _tegn_topplinje(
            surf,
            getattr(self.spiller_klubb, 'navn', '').upper(),
            "NORSK FOOTBALL MANAGER",
            self.manager_navn,
        )

        y = 28

        # ── Club status bar ───────────────────────────────────────────────────
        BAR_H = 46
        pygame.draw.rect(surf, P.PANEL, (0, y, W_BASE, BAR_H))
        tegn_linje_h(surf, P.HEADER_KANT, 0, y, W_BASE, 1)
        tegn_linje_h(surf, P.HEADER_KANT, 0, y + BAR_H - 1, W_BASE, 1)

        klubb_navn = getattr(self.spiller_klubb, 'navn', '?')
        div_navn   = getattr(self.spiller_klubb, 'divisjon', '?')
        plass      = self._tabell_plass()
        saldo      = getattr(self.spiller_klubb, 'saldo', 0)
        saldo_str  = f"Kr {saldo:,.0f}".replace(",", " ") if saldo is not None else "–"

        t_klub = Fonter.stor.render(klubb_navn.upper(), True, P.GULT)
        surf.blit(t_klub, (14, y + 12))

        sep_x = 14 + t_klub.get_width() + 16
        tegn_tekst(surf, div_navn, (sep_x, y + 15), Fonter.normal, P.TEKST_SVAK)

        if plass > 0:
            plass_farge = P.GRØNN if plass <= 3 else (P.GULT if plass <= 6 else P.TEKST)
            plass_str = f"{plass}. PLASS"
            tegn_tekst(surf, plass_str, (sep_x + 120, y + 15), Fonter.normal, plass_farge)

        tegn_tekst(surf, dato_str, (W_BASE - 200, y + 8), Fonter.normal, P.TEKST)
        tegn_tekst(surf, saldo_str, (W_BASE - 200, y + 26), Fonter.liten, P.GRØNNL)

        y += BAR_H + 4

        # ── Next match panel ──────────────────────────────────────────────────
        KAMP_H = 58
        pygame.draw.rect(surf, P.HEADER, (0, y, W_BASE, KAMP_H))
        tegn_linje_h(surf, P.HEADER_KANT, 0, y, W_BASE, 1)
        tegn_linje_h(surf, P.HEADER_KANT, 0, y + KAMP_H - 1, W_BASE, 1)

        if self.neste_kamp:
            neste_dato, kamp = self.neste_kamp
            er_hjemme   = (kamp.hjemme == self.spiller_klubb)
            motstander  = kamp.borte if er_hjemme else kamp.hjemme
            mot_navn    = getattr(motstander, 'navn', '?')
            sted_tekst  = "HJEMMEKAMP" if er_hjemme else "BORTEKAMP"
            kamp_type   = getattr(kamp, 'kamp_type', 'serie').upper()
            dato_tekst  = neste_dato.strftime('%d.%m.%Y') if neste_dato else "?"
            dager       = (neste_dato - self.dato).days if neste_dato and self.dato else 0
            dager_str   = f"Om {dager} dag{'er' if dager != 1 else ''}" if dager > 0 else "I DAG"

            tegn_tekst(surf, "NESTE KAMP", (14, y + 6), Fonter.fet, P.TEKST_SVAK)
            tegn_tekst(surf, dager_str, (110, y + 6), Fonter.fet, P.CYAN)
            tegn_tekst(surf, f"·  {dato_tekst}", (200, y + 6), Fonter.fet, P.TEKST_SVAK)

            h_tekst = klubb_navn if er_hjemme else mot_navn
            b_tekst = mot_navn if er_hjemme else klubb_navn
            t_h  = Fonter.stor.render(h_tekst, True, P.GULT if er_hjemme else P.TEKST)
            t_vs = Fonter.fet.render("VS", True, P.TEKST_SVAK)
            t_b  = Fonter.stor.render(b_tekst, True, P.TEKST if er_hjemme else P.GULT)

            mid_x = W_BASE // 2
            surf.blit(t_h,  (mid_x - t_vs.get_width()//2 - t_h.get_width() - 14, y + 28))
            surf.blit(t_vs, (mid_x - t_vs.get_width()//2, y + 32))
            surf.blit(t_b,  (mid_x + t_vs.get_width()//2 + 14, y + 28))

            tegn_tekst(surf, sted_tekst, (W_BASE - 160, y + 6), Fonter.fet, P.TEKST_SVAK)
            tegn_tekst(surf, kamp_type,  (W_BASE - 160, y + 26), Fonter.liten, P.BLÅLL)
        else:
            tegn_tekst(surf, "Ingen kommende kamper", (14, y + 20), Fonter.normal, P.TEKST_SVAK)

        y += KAMP_H + 6

        # ── Navigation column (left) + mini table (right) ─────────────────────
        NAV_W  = 510
        TBL_X  = NAV_W + 14
        TBL_W  = W_BASE - TBL_X - 4
        BTN_H  = 46
        BTN_GAP = 6
        mx, my = ui.base_mus()

        rader = self._nav_rader()
        for i, (tekst, _, er_uthevet) in enumerate(rader):
            ry = y + i * (BTN_H + BTN_GAP)
            rect = (4, ry, NAV_W, BTN_H)
            er_hover = ui.mus_innenfor(rect)
            farge_tekst = None
            if er_uthevet:
                # Draw subtle accent border for inbox with unread
                pygame.draw.rect(surf, P.PANEL, rect)
                pygame.draw.rect(surf, P.CYAN, rect, 1)
                t = Fonter.stor.render(tekst, True, P.CYAN if not er_hover else P.HVIT)
            else:
                tegn_knapp(surf, rect, tekst, Fonter.stor, hovered=er_hover)
                t = None
            if t and er_uthevet:
                surf.blit(t, (rect[0] + (NAV_W - t.get_width())//2,
                               ry + (BTN_H - t.get_height())//2))

        # Mini table
        mini_rader = self._mini_tabell()
        if mini_rader:
            tbl_y = y
            pygame.draw.rect(surf, P.KOL_HEADER, (TBL_X, tbl_y, TBL_W, 20))
            tegn_linje_h(surf, P.HEADER_KANT, TBL_X, tbl_y + 19, TBL_W, 1)
            tegn_tekst(surf, "#", (TBL_X + 4, tbl_y + 4), Fonter.liten, P.TEKST_SVAK)
            tegn_tekst(surf, "LAG", (TBL_X + 22, tbl_y + 4), Fonter.liten, P.TEKST_SVAK)
            tegn_tekst(surf, "K",  (TBL_X + TBL_W - 100, tbl_y + 4), Fonter.liten, P.TEKST_SVAK)
            tegn_tekst(surf, "P",  (TBL_X + TBL_W - 30,  tbl_y + 4), Fonter.liten, P.TEKST_SVAK)
            tbl_y += 22
            spiller_navn = getattr(self.spiller_klubb, 'navn', '')
            for plass_idx, rad in enumerate(mini_rader):
                er_spiller = (rad.klubb_navn == spiller_navn)
                bunn = P.RAD_VALGT if er_spiller else (P.RAD_MØRK if plass_idx % 2 == 0 else P.RAD_LYS)
                pygame.draw.rect(surf, bunn, (TBL_X, tbl_y, TBL_W, 22))
                plass_txt = str(plass_idx + 1)
                plass_farge = P.GRØNN if plass_idx < 3 else (P.RØD if plass_idx >= len(mini_rader) - 1 else P.TEKST_SVAK)
                tegn_tekst(surf, plass_txt,      (TBL_X + 4,            tbl_y + 4), Fonter.liten, plass_farge)
                tegn_tekst(surf, rad.klubb_navn, (TBL_X + 22,           tbl_y + 4), Fonter.liten,
                           P.GULT if er_spiller else P.TEKST, max_bredde=TBL_W - 140)
                tegn_tekst(surf, str(rad.kamp), (TBL_X + TBL_W - 100, tbl_y + 4), Fonter.liten, P.TEKST_SVAK)
                tegn_tekst(surf, str(rad.poeng),  (TBL_X + TBL_W - 30,  tbl_y + 4), Fonter.liten,
                           P.GULT if er_spiller else P.TEKST)
                tbl_y += 22

        # ── Last result ───────────────────────────────────────────────────────
        if self.siste_resultat:
            h_navn, h_maal, b_navn, b_maal = self.siste_resultat
            res_y = y + len(rader) * (BTN_H + BTN_GAP) + 4
            pygame.draw.rect(surf, P.PANEL, (4, res_y, NAV_W, 30))
            tegn_linje_h(surf, P.PANEL_LYS, 4, res_y, NAV_W, 1)
            tegn_tekst(surf, "SIST:", (10, res_y + 8), Fonter.liten, P.TEKST_SVAK)
            res_str = f"{h_navn}  {h_maal} – {b_maal}  {b_navn}"
            tegn_tekst(surf, res_str, (55, res_y + 8), Fonter.liten, P.TEKST, max_bredde=NAV_W - 60)

        # ── Continue button ───────────────────────────────────────────────────
        BTN_FORTS_W = 280
        BTN_FORTS_H = 44
        BTN_FORTS_X = (NAV_W - BTN_FORTS_W) // 2 + 4
        BTN_FORTS_Y = H_BASE - 22 - BTN_FORTS_H - 8
        forts_rect = (BTN_FORTS_X, BTN_FORTS_Y, BTN_FORTS_W, BTN_FORTS_H)
        tegn_knapp(surf, forts_rect, "FORTSETT  →", Fonter.stor,
                   hovered=ui.mus_innenfor(forts_rect))

        _tegn_bunnlinje(surf, "F1–F6 = VELG SEKSJON   MELLOMROM / ENTER = FORTSETT")

    # ── Event handling ────────────────────────────────────────────────────────

    def håndter_event(self, event, ui):
        rader   = self._nav_rader()
        NAV_W   = 510
        BTN_H   = 46
        BTN_GAP = 6

        # top bar (28) + club status (46+4) + next match (58+6) = y offset for nav
        Y0 = 28 + 46 + 4 + 58 + 6

        BTN_FORTS_W = 280
        BTN_FORTS_H = 44
        BTN_FORTS_X = (NAV_W - BTN_FORTS_W) // 2 + 4
        BTN_FORTS_Y = H_BASE - 22 - BTN_FORTS_H - 8

        if event.type == pygame.KEYDOWN:
            tast_map = {
                pygame.K_F1: 0, pygame.K_F2: 1, pygame.K_F3: 2,
                pygame.K_F4: 3, pygame.K_F5: 4, pygame.K_F6: 5,
            }
            if event.key in tast_map:
                idx = tast_map[event.key]
                if idx < len(rader):
                    rader[idx][1]()
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.on_fortsett()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            # Nav buttons
            for i, (_, callback, _) in enumerate(rader):
                ry = Y0 + i * (BTN_H + BTN_GAP)
                if 4 <= mx <= 4 + NAV_W and ry <= my < ry + BTN_H:
                    callback()
                    return
            # Continue button
            if (BTN_FORTS_X <= mx <= BTN_FORTS_X + BTN_FORTS_W
                    and BTN_FORTS_Y <= my <= BTN_FORTS_Y + BTN_FORTS_H):
                self.on_fortsett()


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: MATCHDAY HUB
# ─────────────────────────────────────────────────────────────────────────────
class KampdagSkjerm(SkjermData):
    """Matchday hub: choose between team selection, play match, squad view."""

    def __init__(self, kamp, dato, spiller_klubb, motstander,
                 on_laguttak: Callable, on_spill: Callable,
                 on_spillerstall: Callable, on_tabell: Callable):
        self.kamp            = kamp
        self.dato            = dato
        self.spiller_klubb   = spiller_klubb
        self.motstander      = motstander
        self.on_laguttak     = on_laguttak
        self.on_spill        = on_spill
        self.on_spillerstall = on_spillerstall
        self.on_tabell       = on_tabell

    def _meny_rader(self):
        return [
            ("F1   LAGUTTAK & TAKTIKK",  self.on_laguttak),
            ("F2   SPILL KAMP",          self.on_spill),
            ("F3   SPILLERSTALL",        self.on_spillerstall),
            ("F4   SERIATABELL",         self.on_tabell),
        ]

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)

        er_hjemme = (self.kamp.hjemme == self.spiller_klubb)
        sted = "HJEMMEKAMP" if er_hjemme else "BORTEKAMP"
        dato_str = self.dato.strftime('%d.%m.%Y')
        manager_str = ""
        if hasattr(ui, 'manager_fornavn') and ui.manager_fornavn:
            manager_str = f"{ui.manager_fornavn} {ui.manager_etternavn}"
        _tegn_topplinje(surf, sted, dato_str, manager_str)

        # Match header box
        header_y = 36
        pygame.draw.rect(surf, P.PANEL, (0, header_y, W_BASE, 90))
        tegn_linje_h(surf, P.HEADER_KANT, 0, header_y, W_BASE, 1)
        tegn_linje_h(surf, P.HEADER_KANT, 0, header_y + 89, W_BASE, 1)

        hjemme_navn = getattr(self.kamp.hjemme, 'navn', '?')
        borte_navn  = getattr(self.kamp.borte,  'navn', '?')

        # Home team
        tkh = P.GULT if er_hjemme else P.TEKST
        tkb = P.GULT if not er_hjemme else P.TEKST
        t_h = Fonter.stor.render(hjemme_navn, True, tkh)
        t_b = Fonter.stor.render(borte_navn,  True, tkb)
        t_vs = Fonter.fet.render("VS", True, P.TEKST_SVAK)
        surf.blit(t_h, (20, header_y + 28))
        surf.blit(t_vs, (W_BASE // 2 - t_vs.get_width() // 2, header_y + 34))
        surf.blit(t_b, (W_BASE - t_b.get_width() - 20, header_y + 28))

        # Kamp type
        kamp_type = getattr(self.kamp, 'kamp_type', 'serie').upper()
        tkamptype = Fonter.liten.render(kamp_type, True, P.CYAN)
        surf.blit(tkamptype, (W_BASE // 2 - tkamptype.get_width() // 2, header_y + 60))

        # Menu buttons
        rader = self._meny_rader()
        mx, my = ui.base_mus()
        meny_y = 146
        btn_w  = W_BASE - 80
        btn_x  = 40
        btn_h  = 50
        btn_gap = 10

        for i, (tekst, _) in enumerate(rader):
            ry = meny_y + i * (btn_h + btn_gap)
            er_hover = (btn_x <= mx <= btn_x + btn_w and ry <= my < ry + btn_h)
            tegn_knapp(surf, (btn_x, ry, btn_w, btn_h), tekst,
                       Fonter.stor, hovered=er_hover)

        _tegn_bunnlinje(surf, "F1–F4 = VELG HANDLING")

    def håndter_event(self, event, ui):
        rader = self._meny_rader()
        meny_y  = 146
        btn_h   = 50
        btn_gap = 10
        btn_w   = W_BASE - 80
        btn_x   = 40

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
                ry = meny_y + i * (btn_h + btn_gap)
                if btn_x <= mx <= btn_x + btn_w and ry <= my < ry + btn_h:
                    callback()
                    return



# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: TEAM SELECTION
# ─────────────────────────────────────────────────────────────────────────────
class LaguttakSkjerm(SkjermData):
    """
    Two columns: starters (left) + formation pitch (right).
    Below starters: bench. Click to select and swap.
    """

    def __init__(self, builder, motstandernavn: str, on_ferdig: Callable,
                 on_spillerkort: Callable = None):
        self.builder         = builder
        self.motstandernavn  = motstandernavn
        self.on_ferdig       = on_ferdig
        self.on_spillerkort  = on_spillerkort
        self._valgt_start    = -1
        self._valgt_benk     = -1
        import taktikk as _taktikk
        self._TAKTIKK_LISTE = list(_taktikk.TAKTIKK_KATALOG.keys())
        self._formasjon_idx = (
            self._TAKTIKK_LISTE.index(builder.formasjon_navn)
            if builder.formasjon_navn in self._TAKTIKK_LISTE else 0
        )

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)
        f  = Fonter.liten
        fb = Fonter.fet
        fn = Fonter.normal

        manager_str = ""
        if hasattr(ui, 'manager_fornavn') and ui.manager_fornavn:
            manager_str = f"{ui.manager_fornavn} {ui.manager_etternavn}"
        elif self.motstandernavn:
            manager_str = f"vs {self.motstandernavn}"

        _tegn_topplinje(surf, "LAGUTTAK", self.builder.klubb.navn, manager_str)

        # === LEFT COLUMN: starters ===
        LEFT_W = 490
        rad_h  = 28
        y0     = 28

        # Column header for starters
        pygame.draw.rect(surf, P.KOL_HEADER, (0, y0, LEFT_W, 20))
        tegn_linje_h(surf, P.HEADER_KANT, 0, y0 + 19, LEFT_W, 1)
        for lbl, lx in [("#", 2), ("NAVN", 24), ("POS", 192), ("FERD", 240), ("KOND", 272)]:
            tegn_tekst(surf, lbl, (lx + 2, y0 + 4), f, P.TEKST_SVAK)

        y0 += 20
        mx, my = ui.base_mus()

        for i, s in enumerate(self.builder.startellever):
            ry   = y0 + i * rad_h
            er_v = (i == self._valgt_start)
            if er_v:
                pygame.draw.rect(surf, P.RAD_VALGT, (0, ry, LEFT_W - 2, rad_h - 1))
            elif i % 2 == 0:
                pygame.draw.rect(surf, P.RAD_MØRK, (0, ry, LEFT_W - 2, rad_h - 1))
            else:
                pygame.draw.rect(surf, P.RAD_LYS, (0, ry, LEFT_W - 2, rad_h - 1))

            pos   = getattr(s, 'primær_posisjon', None)
            pos_s = pos.name if pos else '?'
            ferd  = getattr(s, 'ferdighet', 0)
            navn  = f"{getattr(s, 'fornavn', '?')[0]}. {getattr(s, 'etternavn', '?')}"
            kond  = getattr(s, 'kondisjon', 100.0)
            skadet= getattr(s, 'skadet', False)

            tkf = P.HVIT if er_v else P.TEKST
            tegn_tekst(surf, f"{i+1:>2}", (4, ry + 6), f, P.TEKST_SVAK)
            tegn_tekst(surf, navn, (24, ry + 6), fn, tkf, max_bredde=162)
            tegn_tekst(surf, pos_s, (194, ry + 6), f, P.BLÅLL)
            ferd_farge = P.GRØNN if ferd >= 14 else (P.GULT if ferd >= 10 else P.TEKST_SVAK)
            tegn_tekst(surf, str(ferd), (242, ry + 6), fb, ferd_farge)
            if skadet:
                tegn_tekst(surf, "SKADET", (272, ry + 6), f, P.RØD)
            else:
                tegn_kondisjon_bar(surf, 272, ry + 10, 80, kond)
                kond_farge = P.GRØNN if kond >= 90 else (P.GULT if kond >= 75 else P.RØD)
                tegn_tekst(surf, f"{kond:.0f}%", (358, ry + 6), f, kond_farge)

        # Bench header
        benk_hdr_y = y0 + 11 * rad_h + 4
        pygame.draw.rect(surf, P.HEADER, (0, benk_hdr_y, LEFT_W, 20))
        tegn_linje_h(surf, P.HEADER_KANT, 0, benk_hdr_y + 19, LEFT_W, 1)
        tegn_tekst(surf, "BENK", (8, benk_hdr_y + 4), fb, P.BLÅLL)

        benk_y0 = benk_hdr_y + 20
        benk_rad_h = 24

        for j, s in enumerate(self.builder.benk):
            ry   = benk_y0 + j * benk_rad_h
            er_v = (j == self._valgt_benk)
            if er_v:
                pygame.draw.rect(surf, P.RAD_VALGT, (0, ry, LEFT_W - 2, benk_rad_h - 1))
            elif j % 2 == 0:
                pygame.draw.rect(surf, P.RAD_MØRK, (0, ry, LEFT_W - 2, benk_rad_h - 1))
            else:
                pygame.draw.rect(surf, P.RAD_LYS, (0, ry, LEFT_W - 2, benk_rad_h - 1))

            pos   = getattr(s, 'primær_posisjon', None)
            pos_s = pos.name if pos else '?'
            ferd  = getattr(s, 'ferdighet', 0)
            navn  = f"{getattr(s, 'fornavn', '?')[0]}. {getattr(s, 'etternavn', '?')}"
            kond  = getattr(s, 'kondisjon', 100.0)
            skadet= getattr(s, 'skadet', False)

            tkf = P.HVIT if er_v else P.TEKST
            tegn_tekst(surf, f"S{j+1}", (4, ry + 4), f, P.TEKST_SVAK)
            tegn_tekst(surf, navn, (24, ry + 4), f, tkf, max_bredde=162)
            tegn_tekst(surf, pos_s, (194, ry + 4), f, P.BLÅLL)
            ferd_farge = P.GRØNN if ferd >= 14 else (P.GULT if ferd >= 10 else P.TEKST_SVAK)
            tegn_tekst(surf, str(ferd), (242, ry + 4), f, ferd_farge)
            if skadet:
                tegn_tekst(surf, "SKADET", (272, ry + 4), f, P.RØD)
            else:
                tegn_kondisjon_bar(surf, 272, ry + 8, 80, kond)

        # Swap mode indicator
        if self._valgt_start >= 0 or self._valgt_benk >= 0:
            tegn_linje_h(surf, P.GULT, 0, 27, LEFT_W, 2)

        # === RIGHT COLUMN: formation pitch ===
        RIGHT_X = 494
        RIGHT_W = W_BASE - RIGHT_X - 4
        bane_rect = (RIGHT_X, 28, RIGHT_W, 400)
        tegn_formasjon_på_bane(surf, bane_rect, self.builder.startellever,
                                self.builder.formasjon_navn,
                                valgt_idx=self._valgt_start, font=Fonter.liten)

        # Formation selector
        fv_y = 436
        pygame.draw.rect(surf, P.PANEL, (RIGHT_X, fv_y, RIGHT_W, 32))
        pygame.draw.rect(surf, P.GRÅ_MØRK, (RIGHT_X, fv_y, RIGHT_W, 32), 1)

        arr_l_rect = (RIGHT_X + 4, fv_y + 4, 28, 24)
        arr_r_rect = (RIGHT_X + RIGHT_W - 32, fv_y + 4, 28, 24)
        tegn_knapp(surf, arr_l_rect, "<", fb, hovered=ui.mus_innenfor(arr_l_rect))
        tegn_knapp(surf, arr_r_rect, ">", fb, hovered=ui.mus_innenfor(arr_r_rect))
        t_f = Fonter.normal.render(self.builder.formasjon_navn, True, P.HVIT)
        surf.blit(t_f, (RIGHT_X + RIGHT_W // 2 - t_f.get_width() // 2, fv_y + 8))

        # FERDIG button
        ferdig_rect = (RIGHT_X, H_BASE - 46, RIGHT_W, 36)
        tegn_knapp(surf, ferdig_rect, "FERDIG / TILBAKE", Fonter.stor,
                   hovered=ui.mus_innenfor(ferdig_rect))

        _tegn_bunnlinje(surf, "KLIKK START → BENK FOR Å BYTTE   < > = FORMASJON   ESC = TILBAKE")

    def håndter_event(self, event, ui):
        rad_h     = 28
        y0        = 48  # 28 (topbar) + 20 (col header)
        benk_y0   = y0 + 11 * rad_h + 24  # +4 gap +20 bench header
        benk_rad_h = 24
        LEFT_W    = 490
        RIGHT_X   = 494
        RIGHT_W   = W_BASE - RIGHT_X - 4

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()

            # Formation arrows
            fv_y = 436
            arr_l_rect = (RIGHT_X + 4, fv_y + 4, 28, 24)
            arr_r_rect = (RIGHT_X + RIGHT_W - 32, fv_y + 4, 28, 24)
            ax, ay, aw, ah = arr_l_rect
            if ax <= mx <= ax + aw and ay <= my <= ay + ah:
                self._formasjon_idx = (self._formasjon_idx - 1) % len(self._TAKTIKK_LISTE)
                self.builder.bytt_formasjon(self._TAKTIKK_LISTE[self._formasjon_idx])
                self._valgt_start = -1; self._valgt_benk = -1
                return
            ax, ay, aw, ah = arr_r_rect
            if ax <= mx <= ax + aw and ay <= my <= ay + ah:
                self._formasjon_idx = (self._formasjon_idx + 1) % len(self._TAKTIKK_LISTE)
                self.builder.bytt_formasjon(self._TAKTIKK_LISTE[self._formasjon_idx])
                self._valgt_start = -1; self._valgt_benk = -1
                return

            # FERDIG button
            ferdig_x, ferdig_y, ferdig_w, ferdig_h = (RIGHT_X, H_BASE - 46, RIGHT_W, 36)
            if ferdig_x <= mx <= ferdig_x + ferdig_w and ferdig_y <= my <= ferdig_y + ferdig_h:
                self.on_ferdig()
                return

            # Click on starting player
            if mx < LEFT_W:
                for i in range(len(self.builder.startellever)):
                    ry = y0 + i * rad_h
                    if ry <= my < ry + rad_h:
                        if self._valgt_benk >= 0:
                            self.builder.bytt_spiller(i, self._valgt_benk)
                            self._valgt_start = -1; self._valgt_benk = -1
                        else:
                            if self._valgt_start == i:
                                if self.on_spillerkort:
                                    self.on_spillerkort(
                                        self.builder.startellever[i],
                                        self.builder.startellever, i)
                            else:
                                self._valgt_start = i
                        return

                # Click on bench player
                for j in range(len(self.builder.benk)):
                    ry = benk_y0 + j * benk_rad_h
                    if ry <= my < ry + benk_rad_h:
                        if self._valgt_start >= 0:
                            self.builder.bytt_spiller(self._valgt_start, j)
                            self._valgt_start = -1; self._valgt_benk = -1
                        else:
                            if self._valgt_benk == j:
                                if self.on_spillerkort:
                                    self.on_spillerkort(
                                        self.builder.benk[j],
                                        self.builder.benk, j)
                            else:
                                self._valgt_benk = j
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
# SCREEN: SQUAD VIEW
# ─────────────────────────────────────────────────────────────────────────────
class SpillerstallSkjerm(SkjermData):
    SYNLIGE = 25

    def __init__(self, klubb, on_tilbake: Callable, on_spillerkort: Callable = None):
        self.klubb          = klubb
        self.on_tilbake     = on_tilbake
        self.on_spillerkort = on_spillerkort
        self._scroll        = 0
        self._valgt         = -1
        self._sist_klikk_idx= -1
        self._sist_klikk_tid= 0
        self._alle_spillere = self._sorter_spillere()

    def _sorter_spillere(self):
        from taktikk import POSISJON_GRUPPE
        grupper = {"K": [], "F": [], "M": [], "A": []}
        for s in getattr(self.klubb, 'spillerstall', []):
            pos    = getattr(s, 'primær_posisjon', None)
            gruppe = POSISJON_GRUPPE.get(pos, "M") if pos else "M"
            grupper[gruppe].append(s)
        for g in grupper:
            grupper[g].sort(key=lambda x: getattr(x, 'ferdighet', 0), reverse=True)
        return grupper["K"] + grupper["F"] + grupper["M"] + grupper["A"]

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)
        f  = Fonter.liten
        fn = Fonter.normal
        fb = Fonter.fet

        n_spillere = len(self._alle_spillere)
        manager_str = f"{n_spillere} SPILLERE"
        if hasattr(ui, 'manager_fornavn') and ui.manager_fornavn:
            manager_str = f"{ui.manager_fornavn} {ui.manager_etternavn}"

        _tegn_topplinje(surf, "SPILLERSTALL", self.klubb.navn, manager_str)

        # Column headers
        KOL = [
            ("#",        4),
            ("NAVN",    26),
            ("POS",    280),
            ("FERD",   328),
            ("KOND%",  376),
            ("RYKTE",  490),
            ("ALDER",  556),
            ("KONTRAKT", 618),
        ]
        _tegn_kolonne_header(surf, KOL, y=28, h=22)

        rad_h  = 26
        y0     = 50
        start  = self._scroll
        slutt  = min(start + self.SYNLIGE, n_spillere)
        mx, my = ui.base_mus()

        for i, idx in enumerate(range(start, slutt)):
            s    = self._alle_spillere[idx]
            ry   = y0 + i * rad_h
            er_v = (idx == self._valgt)
            er_h = (0 <= mx <= W_BASE - 10 and ry <= my < ry + rad_h)

            if er_v:
                pygame.draw.rect(surf, P.RAD_VALGT, (0, ry, W_BASE - 10, rad_h - 1))
            elif er_h:
                pygame.draw.rect(surf, P.RAD_HOVER, (0, ry, W_BASE - 10, rad_h - 1))
            elif i % 2 == 0:
                pygame.draw.rect(surf, P.RAD_MØRK, (0, ry, W_BASE - 10, rad_h - 1))
            else:
                pygame.draw.rect(surf, P.RAD_LYS, (0, ry, W_BASE - 10, rad_h - 1))

            pos     = getattr(s, 'primær_posisjon', None)
            pos_s   = pos.name if pos else '?'
            ferd    = getattr(s, 'ferdighet', 0)
            kond    = getattr(s, 'kondisjon', 100.0)
            skadet  = getattr(s, 'skadet', False)
            rykte   = getattr(s, 'rykte', 0)
            alder   = getattr(s, 'alder', 0)
            kontr   = getattr(s, 'kontrakt', None)
            kontr_s = str(getattr(kontr, 'utlops_aar', '?')) if kontr else '-'
            fornavn  = getattr(s, 'fornavn', '?')
            etternavn= getattr(s, 'etternavn', '?')
            navn     = f"{fornavn[0]}. {etternavn}"

            tkf = P.HVIT if er_v else P.TEKST
            tegn_tekst(surf, str(idx + 1), (6, ry + 5), f, P.TEKST_SVAK)
            tegn_tekst(surf, navn, (26, ry + 5), fn, tkf, max_bredde=248)
            tegn_tekst(surf, pos_s, (282, ry + 5), f, P.BLÅLL)
            ferd_farge = P.GRØNN if ferd >= 14 else (P.GULT if ferd >= 10 else P.TEKST_SVAK)
            tegn_badge(surf, str(ferd), (330, ry + 3), ferd_farge, P.SVART, f)
            if skadet:
                tegn_tekst(surf, "SKADET", (378, ry + 5), f, P.RØD)
            else:
                tegn_kondisjon_bar(surf, 378, ry + 9, 80, kond)
                kond_f = P.GRØNN if kond >= 90 else (P.GULT if kond >= 75 else P.RØD)
                tegn_tekst(surf, f"{kond:.0f}%", (464, ry + 5), f, kond_f)
            tegn_tekst(surf, str(rykte), (492, ry + 5), f, P.GULTL)
            tegn_tekst(surf, str(alder), (558, ry + 5), f, P.TEKST_SVAK)
            tegn_tekst(surf, kontr_s, (620, ry + 5), f, P.CYAN)

        tegn_scrollbar(surf, W_BASE - 8, y0, self.SYNLIGE * rad_h,
                       n_spillere, self.SYNLIGE, self._scroll)

        btn_rect = (W_BASE // 2 - 100, H_BASE - 46, 200, 36)
        tegn_knapp(surf, btn_rect, "TILBAKE", Fonter.stor,
                   hovered=ui.mus_innenfor(btn_rect))

        _tegn_bunnlinje(surf, "↑↓ / SCROLL = NAVIGER   DOBBELT-KLIKK = SPILLERKORT   ESC = TILBAKE")

    def håndter_event(self, event, ui):
        maks_scroll = max(0, len(self._alle_spillere) - self.SYNLIGE)

        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, min(maks_scroll, self._scroll - event.y))

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            rad_h, y0 = 26, 50
            now = pygame.time.get_ticks()

            for i in range(self.SYNLIGE):
                idx = self._scroll + i
                if idx >= len(self._alle_spillere):
                    break
                ry = y0 + i * rad_h
                if 0 <= mx <= W_BASE - 10 and ry <= my < ry + rad_h:
                    if self._sist_klikk_idx == idx and now - self._sist_klikk_tid < 500:
                        if self.on_spillerkort:
                            self.on_spillerkort(self._alle_spillere[idx],
                                                self._alle_spillere, idx)
                    else:
                        self._valgt = idx
                    self._sist_klikk_idx = idx
                    self._sist_klikk_tid = now
                    break

            btn_rect = (W_BASE // 2 - 100, H_BASE - 46, 200, 36)
            bx, by, bw, bh = btn_rect
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                self.on_tilbake()

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.on_tilbake()
            elif event.key == pygame.K_DOWN:
                self._scroll = min(maks_scroll, self._scroll + 1)
            elif event.key == pygame.K_UP:
                self._scroll = max(0, self._scroll - 1)



# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: LEAGUE TABLE
# ─────────────────────────────────────────────────────────────────────────────
class TabellSkjerm(SkjermData):
    SYNLIGE = 22

    def __init__(self, tabeller: dict, aktiv_divisjon: str,
                 spiller_klubb_navn: str, on_tilbake: Callable,
                 on_velg_klubb: Callable = None):
        self.tabeller = tabeller
        self.divisjoner = list(tabeller.keys())
        self._aktiv_div_idx = (
            self.divisjoner.index(aktiv_divisjon)
            if aktiv_divisjon in self.divisjoner else 0
        )
        self.spiller_klubb_navn = spiller_klubb_navn
        self.on_tilbake = on_tilbake
        self.on_velg_klubb = on_velg_klubb  # Callable(klubb_navn: str) or None
        self._fane  = 0  # 0=tabell, 1=toppscorere
        self._scroll = 0

    @property
    def aktiv_tabell(self):
        return self.tabeller[self.divisjoner[self._aktiv_div_idx]]

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)
        f  = Fonter.liten
        fb = Fonter.fet
        fn = Fonter.normal

        div_navn = self.divisjoner[self._aktiv_div_idx]
        _tegn_topplinje(surf, "SERIATABELL", div_navn, "< > = BYTT DIVISJON")

        # Tabs
        tab_y = 28
        for fi, tekst in enumerate(["TABELL", "TOPPSCORERE"]):
            er_aktiv = fi == self._fane
            tab_rect = (4 + fi * 130, tab_y, 126, 22)
            tegn_knapp(surf, tab_rect, tekst, fb, valgt=er_aktiv,
                       hovered=not er_aktiv and ui.mus_innenfor(tab_rect))

        tegn_linje_h(surf, P.HEADER_KANT, 0, tab_y + 21, W_BASE, 1)

        if self._fane == 0:
            self._tegn_tabell(surf, ui)
        else:
            self._tegn_toppscorere(surf, ui)

        btn_rect = (W_BASE // 2 - 100, H_BASE - 46, 200, 36)
        tegn_knapp(surf, btn_rect, "TILBAKE", Fonter.stor,
                   hovered=ui.mus_innenfor(btn_rect))

        klikk_hint = "   KLIKK KLUBB = KLUBBSIDE" if self.on_velg_klubb and self._fane == 0 else ""
        _tegn_bunnlinje(surf, f"TAB = BYTT FANE   < > = DIVISJON   ↑↓ = SCROLL   ESC = TILBAKE{klikk_hint}")

    def _tegn_tabell(self, surf, ui):
        f  = Fonter.liten
        fn = Fonter.normal
        rader = self.aktiv_tabell.sorter()

        KOL = [
            ("#",    4),
            ("KLUBB", 36),
            ("K",   350),
            ("S",   390),
            ("U",   428),
            ("T",   466),
            ("MF",  504),
            ("MM",  550),
            ("MD",  596),
            ("P",   648),
        ]
        _tegn_kolonne_header(surf, KOL, y=50, h=22)

        rad_h = 26
        y0    = 72
        start = self._scroll
        slutt = min(start + self.SYNLIGE, len(rader))
        mx, my = ui.base_mus()

        for i, plass in enumerate(range(start, slutt)):
            rad = rader[plass]
            ry  = y0 + i * rad_h
            er_min    = (rad.klubb_navn == self.spiller_klubb_navn)
            er_hover  = (self.on_velg_klubb is not None
                         and ry <= my < ry + rad_h
                         and 0 <= mx < W_BASE - 10
                         and not er_min)

            if er_min:
                pygame.draw.rect(surf, P.RAD_VALGT, (0, ry, W_BASE - 10, rad_h - 1))
            elif er_hover:
                pygame.draw.rect(surf, P.RAD_HOVER, (0, ry, W_BASE - 10, rad_h - 1))
            elif i % 2 == 0:
                pygame.draw.rect(surf, P.RAD_MØRK, (0, ry, W_BASE - 10, rad_h - 1))
            else:
                pygame.draw.rect(surf, P.RAD_LYS, (0, ry, W_BASE - 10, rad_h - 1))

            md    = rad.mål_differanse
            md_s  = f"+{md}" if md > 0 else str(md)
            tkf   = P.GULT if er_min else P.TEKST

            tkf_klubb = P.BLÅLL if er_hover else tkf
            tegn_tekst(surf, str(plass + 1), (6, ry + 5), f, P.TEKST_SVAK)
            tegn_tekst(surf, rad.klubb_navn, (38, ry + 5), fn, tkf_klubb, max_bredde=306)
            tegn_tekst(surf, str(rad.kamp),     (352, ry + 5), f, P.TEKST_SVAK)
            tegn_tekst(surf, str(rad.seier),    (392, ry + 5), f, P.GRØNN)
            tegn_tekst(surf, str(rad.uavgjort), (430, ry + 5), f, P.GULT)
            tegn_tekst(surf, str(rad.tap),      (468, ry + 5), f, P.RØD)
            tegn_tekst(surf, str(rad.mål_for),  (506, ry + 5), f, P.TEKST)
            tegn_tekst(surf, str(rad.mål_mot),  (552, ry + 5), f, P.TEKST)
            md_farge = P.GRØNN if md > 0 else (P.RØD if md < 0 else P.TEKST_SVAK)
            tegn_tekst(surf, md_s, (598, ry + 5), f, md_farge)
            poeng_farge = P.GULT if er_min else P.HVIT
            tegn_badge(surf, str(rad.poeng), (650, ry + 3),
                       P.BLÅ if er_min else P.PANEL, poeng_farge, f)

        tegn_scrollbar(surf, W_BASE - 8, y0, self.SYNLIGE * rad_h,
                       len(rader), self.SYNLIGE, self._scroll)

    def _tegn_toppscorere(self, surf, ui):
        f  = Fonter.liten
        fn = Fonter.normal
        if not hasattr(self.aktiv_tabell, '_statistikk_register'):
            return

        KOL = [("#", 4), ("SPILLER", 36), ("KLUBB", 320), ("K", 460),
               ("MÅL", 500), ("RTG", 570)]
        _tegn_kolonne_header(surf, KOL, y=50, h=22)

        topp = self.aktiv_tabell._statistikk_register.toppscorere(self.SYNLIGE)
        rad_h = 26
        y0    = 72

        for i, stat in enumerate(topp):
            ry = y0 + i * rad_h
            if i % 2 == 0:
                pygame.draw.rect(surf, P.RAD_MØRK, (0, ry, W_BASE - 10, rad_h - 1))
            else:
                pygame.draw.rect(surf, P.RAD_LYS, (0, ry, W_BASE - 10, rad_h - 1))
            tegn_tekst(surf, str(i + 1), (6, ry + 5), f, P.TEKST_SVAK)
            tegn_tekst(surf, stat.spiller_navn, (38, ry + 5), fn, P.TEKST, max_bredde=278)
            tegn_tekst(surf, str(stat.kamper), (462, ry + 5), f, P.TEKST_SVAK)
            tegn_badge(surf, str(stat.mål), (502, ry + 3), P.GRØNN, P.SVART, f)
            tegn_tekst(surf, f"{stat.snitt_rating:.1f}", (572, ry + 5), f, P.GULT)

    def håndter_event(self, event, ui):
        maks_scroll = max(0, len(self.aktiv_tabell.sorter()) - self.SYNLIGE)

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.on_tilbake()
            elif event.key == pygame.K_TAB:
                self._fane = 1 - self._fane
                self._scroll = 0
            elif event.key == pygame.K_LEFT:
                self._aktiv_div_idx = (self._aktiv_div_idx - 1) % len(self.divisjoner)
                self._scroll = 0
            elif event.key == pygame.K_RIGHT:
                self._aktiv_div_idx = (self._aktiv_div_idx + 1) % len(self.divisjoner)
                self._scroll = 0
            elif event.key == pygame.K_DOWN:
                self._scroll = min(maks_scroll, self._scroll + 1)
            elif event.key == pygame.K_UP:
                self._scroll = max(0, self._scroll - 1)

        elif event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, min(maks_scroll, self._scroll - event.y))

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            for fi in range(2):
                tab_rect = (4 + fi * 130, 28, 126, 22)
                tx, ty, tw, th = tab_rect
                if tx <= mx <= tx + tw and ty <= my <= ty + th:
                    self._fane = fi
                    self._scroll = 0
            btn_rect = (W_BASE // 2 - 100, H_BASE - 46, 200, 36)
            bx, by, bw, bh = btn_rect
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                self.on_tilbake()
                return
            # Club row click → open club page
            if self._fane == 0 and self.on_velg_klubb:
                rader = self.aktiv_tabell.sorter()
                rad_h = 26
                y0    = 72
                start = self._scroll
                slutt = min(start + self.SYNLIGE, len(rader))
                for i in range(slutt - start):
                    ry = y0 + i * rad_h
                    if ry <= my < ry + rad_h and 0 <= mx < W_BASE - 10:
                        self.on_velg_klubb(rader[start + i].klubb_navn)
                        return



# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: MATCH REPORT
# ─────────────────────────────────────────────────────────────────────────────
class KamprapportSkjerm(SkjermData):
    def __init__(self, resultat, hjemme_spillere, borte_spillere,
                 on_ferdig: Callable):
        self.resultat        = resultat
        self.hjemme_spillere = hjemme_spillere or []
        self.borte_spillere  = borte_spillere or []
        self.on_ferdig       = on_ferdig
        self._fane           = 0  # 0=hendelser 1=statistikk 2=børs
        self._scroll         = 0

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)
        f  = Fonter.liten
        fb = Fonter.fet
        fn = Fonter.normal
        r  = self.resultat

        _tegn_topplinje(surf, "KAMPRAPPORT", "", "")

        # Score banner
        banner_y = 28
        pygame.draw.rect(surf, P.PANEL, (0, banner_y, W_BASE, 70))
        tegn_linje_h(surf, P.HEADER_KANT, 0, banner_y, W_BASE, 1)
        tegn_linje_h(surf, P.HEADER_KANT, 0, banner_y + 69, W_BASE, 1)

        t_h  = Fonter.stor.render(r.hjemme_navn, True, P.TEKST)
        t_b  = Fonter.stor.render(r.borte_navn,  True, P.TEKST)
        score = f"{r.hjemme_maal}  -  {r.borte_maal}"
        if r.ekstraomganger:
            score += "  e.o." if not r.straffer else "  str."
        t_s  = Fonter.tittel.render(score, True, P.GULT)

        surf.blit(t_h, (16, banner_y + 22))
        surf.blit(t_b, (W_BASE - t_b.get_width() - 16, banner_y + 22))
        surf.blit(t_s, (W_BASE // 2 - t_s.get_width() // 2, banner_y + 18))

        # Tabs
        tab_y = 100
        fane_navn = ["HENDELSER", "STATISTIKK", "SPILLERBORS"]
        tab_w = (W_BASE - 8) // 3
        for fi, tekst in enumerate(fane_navn):
            er_aktiv = fi == self._fane
            tab_rect = (4 + fi * tab_w, tab_y, tab_w - 2, 24)
            tegn_knapp(surf, tab_rect, tekst, fb, valgt=er_aktiv,
                       hovered=not er_aktiv and ui.mus_innenfor(tab_rect))
        tegn_linje_h(surf, P.HEADER_KANT, 0, tab_y + 23, W_BASE, 1)

        innhold_y = 126
        innhold_h = H_BASE - innhold_y - 50

        if self._fane == 0:
            self._tegn_hendelser(surf, innhold_y, innhold_h)
        elif self._fane == 1:
            self._tegn_statistikk(surf, innhold_y, innhold_h)
        else:
            self._tegn_bors(surf, innhold_y, innhold_h)

        btn_rect = (W_BASE // 2 - 120, H_BASE - 44, 240, 36)
        tegn_knapp(surf, btn_rect, "FORTSETT", Fonter.stor,
                   hovered=ui.mus_innenfor(btn_rect))

        _tegn_bunnlinje(surf, "TAB = BYTT FANE   ENTER / MELLOMROM = FORTSETT")

    def _tegn_hendelser(self, surf, y0, h):
        f = Fonter.liten
        fn = Fonter.normal
        hendelser = sorted(self.resultat.hendelser, key=lambda x: x.minutt)
        synlige = h // 24
        start   = self._scroll

        pygame.draw.rect(surf, P.KOL_HEADER, (0, y0, W_BASE, 20))
        tegn_linje_h(surf, P.HEADER_KANT, 0, y0 + 19, W_BASE, 1)
        tegn_tekst(surf, "MIN", (6, y0 + 4), f, P.TEKST_SVAK)
        tegn_tekst(surf, "LAG", (60, y0 + 4), f, P.TEKST_SVAK)
        tegn_tekst(surf, "SPILLER", (110, y0 + 4), f, P.TEKST_SVAK)
        tegn_tekst(surf, "HENDELSE", (380, y0 + 4), f, P.TEKST_SVAK)
        y0 += 20

        for i, hend in enumerate(hendelser[start:start + synlige]):
            ry = y0 + i * 24
            if i % 2 == 0:
                pygame.draw.rect(surf, P.RAD_MØRK, (0, ry, W_BASE - 10, 23))
            else:
                pygame.draw.rect(surf, P.RAD_LYS, (0, ry, W_BASE - 10, 23))

            type_farge = {
                "mål": P.GULT, "gult_kort": P.GULT, "rødt_kort": P.RØD,
                "bytte": P.BLÅLL, "skade": P.RØD
            }.get(hend.type, P.TEKST)

            lag_s = "HJEMME" if hend.lag == "hjemme" else "BORTE"
            lag_farge = P.BLÅLL if hend.lag == "hjemme" else P.CYAN
            navn  = getattr(hend.spiller, 'etternavn', '?')
            detalj = f"  ({hend.detalj})" if hend.detalj else ""

            tegn_tekst(surf, f"{hend.minutt}'", (6, ry + 4), fn, P.TEKST_SVAK)
            tegn_tekst(surf, lag_s, (60, ry + 4), f, lag_farge)
            tegn_tekst(surf, navn, (110, ry + 4), fn, P.TEKST, max_bredde=260)
            tegn_tekst(surf, hend.type.upper() + detalj, (380, ry + 4), f, type_farge)

        if not hendelser:
            tegn_tekst(surf, "Ingen hendelser registrert.", (16, y0 + 20), fn, P.TEKST_SVAK)

        tegn_scrollbar(surf, W_BASE - 8, y0, synlige * 24,
                       max(len(hendelser), 1), synlige, self._scroll)

    def _tegn_statistikk(self, surf, y0, h):
        f  = Fonter.liten
        fn = Fonter.normal
        s  = self.resultat.statistikk
        r  = self.resultat
        bes_h, bes_b = s.ballbesittelse

        mid = W_BASE // 2

        def stat_rad(label, v_h, v_b, ry):
            if ry % (2 * 34) < 34:
                pygame.draw.rect(surf, P.RAD_MØRK, (0, ry, W_BASE - 10, 33))
            else:
                pygame.draw.rect(surf, P.RAD_LYS, (0, ry, W_BASE - 10, 33))
            t_h = fn.render(str(v_h), True, P.BLÅLL)
            t_b = fn.render(str(v_b), True, P.BLÅLL)
            t_l = f.render(label, True, P.TEKST_SVAK)
            surf.blit(t_h, (mid - 160 - t_h.get_width(), ry + 8))
            surf.blit(t_l, (mid - t_l.get_width() // 2, ry + 10))
            surf.blit(t_b, (mid + 160, ry + 8))

        # Team names header
        pygame.draw.rect(surf, P.PANEL, (0, y0, W_BASE, 28))
        t_hn = Fonter.stor.render(r.hjemme_navn, True, P.TEKST)
        t_bn = Fonter.stor.render(r.borte_navn,  True, P.TEKST)
        surf.blit(t_hn, (mid - 160 - t_hn.get_width(), y0 + 4))
        surf.blit(t_bn, (mid + 160, y0 + 4))
        tegn_linje_h(surf, P.HEADER_KANT, 0, y0 + 27, W_BASE, 1)
        y0 += 28

        stat_rad("Ballbesittelse", f"{bes_h}%", f"{bes_b}%", y0)
        stat_rad("Sjanser",        s.sjanser_hjemme,         s.sjanser_borte,         y0 + 34)
        stat_rad("Skudd",          s.skudd_hjemme,           s.skudd_borte,           y0 + 68)
        stat_rad("Skudd på mål",   s.skudd_paa_maal_hjemme,  s.skudd_paa_maal_borte,  y0 + 102)
        stat_rad("Gule kort",      s.gule_kort_hjemme,       s.gule_kort_borte,       y0 + 136)
        stat_rad("Røde kort",      s.røde_kort_hjemme,       s.røde_kort_borte,       y0 + 170)

    def _tegn_bors(self, surf, y0, h):
        f  = Fonter.liten
        fn = Fonter.normal
        alle = ([(s, True) for s in self.hjemme_spillere] +
                [(s, False) for s in self.borte_spillere])
        synlige = h // 26
        start   = self._scroll

        KOL = [("SPILLER", 4), ("LAG", 340), ("RATING", 460)]
        _tegn_kolonne_header(surf, KOL, y=y0, h=22)
        y0 += 22

        for i, (s, er_hjemme) in enumerate(alle[start:start + synlige]):
            ry     = y0 + i * 26
            rating = self.resultat.statistikk.hent_rating(s)
            navn   = f"{getattr(s, 'fornavn', '?')[0]}. {getattr(s, 'etternavn', '?')}"
            lag    = self.resultat.hjemme_navn if er_hjemme else self.resultat.borte_navn

            if i % 2 == 0:
                pygame.draw.rect(surf, P.RAD_MØRK, (0, ry, W_BASE - 10, 25))
            else:
                pygame.draw.rect(surf, P.RAD_LYS, (0, ry, W_BASE - 10, 25))

            rtg_farge = (P.GRØNN if rating >= 7.5 else
                         P.GULT  if rating >= 6.5 else
                         P.RØD   if rating < 5.5 else P.TEKST_SVAK)

            tegn_tekst(surf, navn, (6, ry + 5), fn, P.TEKST, max_bredde=328)
            tegn_tekst(surf, lag[:14], (342, ry + 5), f, P.BLÅLL)
            tegn_badge(surf, f"{rating:.1f}", (462, ry + 3), rtg_farge, P.SVART, fn)

        tegn_scrollbar(surf, W_BASE - 8, y0, synlige * 26,
                       max(len(alle), 1), synlige, self._scroll)

    def håndter_event(self, event, ui):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.on_ferdig()
            elif event.key == pygame.K_TAB:
                self._fane = (self._fane + 1) % 3
                self._scroll = 0
            elif event.key == pygame.K_DOWN:
                self._scroll += 1
            elif event.key == pygame.K_UP:
                self._scroll = max(0, self._scroll - 1)

        elif event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, self._scroll - event.y)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            tab_y = 100
            tab_w = (W_BASE - 8) // 3
            for fi in range(3):
                tx = 4 + fi * tab_w
                if tx <= mx <= tx + tab_w - 2 and tab_y <= my <= tab_y + 24:
                    self._fane  = fi
                    self._scroll = 0
                    return
            btn_rect = (W_BASE // 2 - 120, H_BASE - 44, 240, 36)
            bx, by, bw, bh = btn_rect
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                self.on_ferdig()



# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: INFO / GENERIC MESSAGE
# ─────────────────────────────────────────────────────────────────────────────
class InfoSkjerm(SkjermData):
    """Generic info screen with title box + text lines + continue button."""

    def __init__(self, tittel: str, linjer: list, on_ferdig: Callable,
                 farge_bakgrunn=None):
        self.tittel_tekst   = tittel
        self.linjer         = linjer
        self.on_ferdig      = on_ferdig
        self.farge_bakgrunn = farge_bakgrunn

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf, self.farge_bakgrunn)
        f  = Fonter.normal
        fb = Fonter.stor

        # Title box
        t_rect = (W_BASE // 2 - 320, 60, 640, 60)
        pygame.draw.rect(surf, P.PANEL, t_rect)
        pygame.draw.rect(surf, P.HEADER_KANT, t_rect, 1)
        tegn_linje_h(surf, P.HEADER_KANT, t_rect[0], t_rect[1], t_rect[2], 2)
        t = fb.render(self.tittel_tekst, True, P.GULT)
        surf.blit(t, (W_BASE // 2 - t.get_width() // 2, 78))

        # Text lines
        for i, linje in enumerate(self.linjer[:18]):
            tegn_tekst(surf, linje, (W_BASE // 2 - 310, 140 + i * 26), f, P.TEKST)

        btn_rect = (W_BASE // 2 - 120, H_BASE - 80, 240, 40)
        tegn_knapp(surf, btn_rect, "FORTSETT", Fonter.stor,
                   hovered=ui.mus_innenfor(btn_rect))

        _tegn_bunnlinje(surf, "ENTER / KLIKK FOR Å FORTSETTE")

    def håndter_event(self, event, ui):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.on_ferdig()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            btn_rect = (W_BASE // 2 - 120, H_BASE - 80, 240, 40)
            bx, by, bw, bh = btn_rect
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                self.on_ferdig()


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: PLAYER CARD
# ─────────────────────────────────────────────────────────────────────────────
class SpillerkortSkjerm(SkjermData):
    """Full-screen player card with attributes and season stats."""

    def __init__(self, spiller, spiller_liste: list, start_idx: int,
                 stat_register, on_tilbake: Callable,
                 on_forrige: Callable = None, on_neste: Callable = None):
        self.spiller_liste = spiller_liste
        self.idx           = start_idx
        self.stat_register = stat_register
        self.on_tilbake    = on_tilbake
        self.on_forrige    = on_forrige
        self.on_neste      = on_neste
        self.spiller       = spiller

    def _tegn_portrett_placeholder(self, surf, x, y, w, h, pos_str):
        """Draw a simple silhouette placeholder."""
        pygame.draw.rect(surf, P.PANEL, (x, y, w, h))
        pygame.draw.rect(surf, P.GRÅ_MØRK, (x, y, w, h), 1)
        hx, hy = x + w // 2, y + h // 4
        pygame.draw.circle(surf, P.TEKST_SVAK, (hx, hy), w // 6)
        body_h = h // 3
        body_w = w // 3
        pygame.draw.rect(surf, P.TEKST_SVAK, (hx - body_w // 2, hy + w // 6, body_w, body_h))
        if pos_str == 'K':
            pygame.draw.rect(surf, P.GRØNN,
                             (hx - body_w // 2 - 6, hy + w // 6 + 4, 6, 14))
            pygame.draw.rect(surf, P.GRØNN,
                             (hx + body_w // 2, hy + w // 6 + 4, 6, 14))
        pos_t = Fonter.stor.render(pos_str, True, P.GULT)
        surf.blit(pos_t, (x + w // 2 - pos_t.get_width() // 2, y + h - 30))

    def _tegn_attributt_bar(self, surf, label, verdi, x, y, font):
        """Draw a labeled attribute bar."""
        tegn_tekst(surf, label, (x, y), font, P.TEKST, max_bredde=120)
        bar_x = x + 130
        bar_w = 120
        pygame.draw.rect(surf, P.PANEL_LYS, (bar_x, y + 3, bar_w, 9))
        farge = (P.GRØNN if verdi >= 14 else
                 P.GULT  if verdi >= 10 else
                 P.ORANSJE if verdi >= 7 else P.RØD)
        fylt = max(0, min(bar_w, int((verdi / 20.0) * bar_w)))
        if fylt > 0:
            pygame.draw.rect(surf, farge, (bar_x, y + 3, fylt, 9))
        tegn_tekst(surf, str(verdi), (bar_x + bar_w + 6, y), font, P.HVIT)

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)
        f  = Fonter.liten
        fn = Fonter.normal
        fb = Fonter.stor
        s  = self.spiller

        pos     = getattr(s, 'primær_posisjon', None)
        pos_str = pos.name if pos else '?'

        _tegn_topplinje(surf, getattr(s, 'fullt_navn', '?'), pos_str, "SPILLERKORT")

        # Left: portrait
        self._tegn_portrett_placeholder(surf, 8, 36, 130, 160, pos_str)

        # Identity info
        kontr   = getattr(s, 'kontrakt', None)
        utlops  = getattr(kontr, 'utlops_aar', '?') if kontr else 'Ingen'
        lonn    = getattr(kontr, 'ukelonn', 0) if kontr else 0
        mverdi  = getattr(s, 'markedsverdi_nok', 0)

        tegn_tekst(surf, f"Alder: {s.alder}", (148, 42), fn, P.TEKST)
        tegn_tekst(surf, "Nasjonalitet: NOR", (148, 64), fn, P.TEKST_SVAK)
        tegn_tekst(surf, f"Kontrakt: {utlops}", (148, 86), fn, P.TEKST)
        tegn_tekst(surf, f"Ukeslonn: kr {lonn:,}", (148, 108), fn, P.TEKST_SVAK)
        tegn_tekst(surf, f"Markedsverdi: kr {mverdi:,}", (148, 130), fn, P.TEKST)

        # OVR badge
        pygame.draw.rect(surf, P.PANEL, (W_BASE - 120, 36, 112, 80))
        pygame.draw.rect(surf, P.BLÅ, (W_BASE - 120, 36, 112, 80), 1)
        ovr_lbl = f.render("OVR", True, P.TEKST_SVAK)
        surf.blit(ovr_lbl, (W_BASE - 120 + 56 - ovr_lbl.get_width() // 2, 44))
        ovr = s.ferdighet
        ovr_farge = P.GRØNN if ovr >= 14 else (P.GULT if ovr >= 10 else P.RØD)
        t_ovr = Fonter.tittel.render(str(ovr), True, ovr_farge)
        surf.blit(t_ovr, (W_BASE - 120 + 56 - t_ovr.get_width() // 2, 60))

        tegn_linje_h(surf, P.GRÅ_MØRK, 0, 204, W_BASE, 1)

        # Attributes — left column: technical
        y0 = 212
        x_left = 8
        x_right = 290

        attrs_left = [
            ("Skudd",     s.skudd),
            ("Pasning",   s.pasning),
            ("Dribling",  s.dribling),
            ("Takling",   s.takling),
            ("Hodespill", s.hodespill),
            ("Teknikk",   s.teknikk),
            ("Dodball",   s.dodball),
            ("Keeper",    s.keeperferdighet),
        ]
        attrs_right = [
            ("Fart",          s.fart),
            ("Utholdenhet",   s.utholdenhet),
            ("Fysikk",        s.fysikk),
            ("Kreativitet",   s.kreativitet),
            ("Aggressivitet", s.aggressivitet),
            ("Mentalitet",    s.mentalitet),
        ]

        # Section header
        pygame.draw.rect(surf, P.KOL_HEADER, (0, y0 - 18, W_BASE // 2 - 4, 18))
        tegn_tekst(surf, "TEKNISKE EGENSKAPER", (x_left + 2, y0 - 14), f, P.TEKST_SVAK)
        pygame.draw.rect(surf, P.KOL_HEADER, (W_BASE // 2 + 4, y0 - 18, W_BASE // 2 - 4, 18))
        tegn_tekst(surf, "FYSISKE & MENTALE", (x_right + 2, y0 - 14), f, P.TEKST_SVAK)

        for i, (label, verdi) in enumerate(attrs_left):
            self._tegn_attributt_bar(surf, label, verdi, x_left, y0 + i * 24, f)

        for i, (label, verdi) in enumerate(attrs_right):
            self._tegn_attributt_bar(surf, label, verdi, x_right + 290, y0 + i * 24, f)

        # Season stats
        tegn_linje_h(surf, P.GRÅ_MØRK, 0, H_BASE - 100, W_BASE, 1)
        pygame.draw.rect(surf, P.PANEL, (0, H_BASE - 100, W_BASE, 52))

        stat = None
        if hasattr(self.stat_register, '_data'):
            pid = getattr(s, 'id', str(id(s)))
            stat = self.stat_register._data.get(pid)

        if stat:
            stat_str = (f"Kamper: {stat.kamper}   Mål: {stat.mål}   "
                        f"Assist: {stat.assist}   Snitt: {stat.snitt_rating:.1f}   "
                        f"Gule: {stat.gule_kort}   Røde: {stat.røde_kort}")
        else:
            stat_str = "Ingen kamper spilt denne sesongen"

        sesong_t = f.render("SESONGSTATISTIKK", True, P.TEKST_SVAK)
        surf.blit(sesong_t, (8, H_BASE - 96))
        tegn_tekst(surf, stat_str, (8, H_BASE - 78), fn, P.GULTL)

        # Navigation buttons
        forr_rect  = (8, H_BASE - 44, 140, 36)
        tilb_rect  = (W_BASE // 2 - 90, H_BASE - 44, 180, 36)
        neste_rect = (W_BASE - 148, H_BASE - 44, 140, 36)

        tegn_knapp(surf, forr_rect, "< FORRIGE", fn,
                   aktiv=self.on_forrige is not None,
                   hovered=self.on_forrige is not None and ui.mus_innenfor(forr_rect))
        tegn_knapp(surf, tilb_rect, "TILBAKE", Fonter.stor,
                   hovered=ui.mus_innenfor(tilb_rect))
        tegn_knapp(surf, neste_rect, "NESTE >", fn,
                   aktiv=self.on_neste is not None,
                   hovered=self.on_neste is not None and ui.mus_innenfor(neste_rect))

        _tegn_bunnlinje(surf, "< > = NAVIGER SPILLERE   ESC = TILBAKE")

    def håndter_event(self, event, ui):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.on_tilbake()
            elif event.key == pygame.K_LEFT:
                if self.on_forrige:
                    self.on_forrige()
            elif event.key == pygame.K_RIGHT:
                if self.on_neste:
                    self.on_neste()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            forr_rect  = (8, H_BASE - 44, 140, 36)
            tilb_rect  = (W_BASE // 2 - 90, H_BASE - 44, 180, 36)
            neste_rect = (W_BASE - 148, H_BASE - 44, 140, 36)

            def _i_rect(rect):
                rx, ry, rw, rh = rect
                return rx <= mx <= rx + rw and ry <= my <= ry + rh

            if _i_rect(forr_rect) and self.on_forrige:
                self.on_forrige()
            elif _i_rect(tilb_rect):
                self.on_tilbake()
            elif _i_rect(neste_rect) and self.on_neste:
                self.on_neste()



# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: OTHER RESULTS
# ─────────────────────────────────────────────────────────────────────────────
class AndreResultaterSkjerm(SkjermData):
    def __init__(self, resultater: list, dato_str: str, on_ferdig: Callable):
        self.resultater = resultater  # [(hjemme, h_mål, borte, b_mål), ...]
        self.dato_str   = dato_str
        self.on_ferdig  = on_ferdig

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)
        _tegn_topplinje(surf, "RESULTATER", self.dato_str, f"{len(self.resultater)} KAMPER")

        pygame.draw.rect(surf, P.KOL_HEADER, (0, 28, W_BASE, 22))
        tegn_linje_h(surf, P.HEADER_KANT, 0, 49, W_BASE, 1)
        tegn_tekst(surf, "HJEMME", (8, 32), Fonter.liten, P.TEKST_SVAK)
        tegn_tekst(surf, "RESULTAT", (W_BASE // 2 - 50, 32), Fonter.liten, P.TEKST_SVAK)
        tegn_tekst(surf, "BORTE", (W_BASE - 200, 32), Fonter.liten, P.TEKST_SVAK)

        f  = Fonter.liten
        fn = Fonter.normal
        rad_h = 30

        for i, (h, hm, b, bm) in enumerate(self.resultater[:22]):
            ry = 50 + i * rad_h
            if i % 2 == 0:
                pygame.draw.rect(surf, P.RAD_MØRK, (0, ry, W_BASE, rad_h - 1))
            else:
                pygame.draw.rect(surf, P.RAD_LYS, (0, ry, W_BASE, rad_h - 1))

            score = f"{hm}  -  {bm}"
            if hm > bm:
                h_farge = P.GRØNN
                b_farge = P.RØD
            elif hm < bm:
                h_farge = P.RØD
                b_farge = P.GRØNN
            else:
                h_farge = P.GULT
                b_farge = P.GULT

            tegn_tekst(surf, h, (8, ry + 7), fn, h_farge, max_bredde=320)
            t_score = fn.render(score, True, P.HVIT)
            surf.blit(t_score, (W_BASE // 2 - t_score.get_width() // 2, ry + 7))
            t_b = fn.render(b, True, b_farge)
            surf.blit(t_b, (W_BASE - t_b.get_width() - 8, ry + 7))

        btn_rect = (W_BASE // 2 - 100, H_BASE - 46, 200, 36)
        tegn_knapp(surf, btn_rect, "OK", Fonter.stor,
                   hovered=ui.mus_innenfor(btn_rect))
        _tegn_bunnlinje(surf, "ENTER = FORTSETT")

    def håndter_event(self, event, ui):
        if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
            self.on_ferdig()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            btn_rect = (W_BASE // 2 - 100, H_BASE - 46, 200, 36)
            bx, by, bw, bh = btn_rect
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                self.on_ferdig()


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: SEASON END
# ─────────────────────────────────────────────────────────────────────────────
class SesongsSluttSkjerm(SkjermData):
    def __init__(self, klubb_navn: str, resultater: list,
                 tabell, on_avslutt: Callable, on_fortsett: Callable = None):
        self.klubb_navn  = klubb_navn
        self.resultater  = resultater
        self.tabell      = tabell
        self.on_avslutt  = on_avslutt
        self.on_fortsett = on_fortsett if on_fortsett is not None else on_avslutt

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)

        f  = Fonter.normal
        fb = Fonter.stor
        fs = Fonter.liten

        # Title
        pygame.draw.rect(surf, P.PANEL, (0, 0, W_BASE, 80))
        tegn_linje_h(surf, P.HEADER_KANT, 0, 79, W_BASE, 2)
        t1 = Fonter.tittel.render("SESONGEN ER OVER", True, P.GULT)
        surf.blit(t1, (W_BASE // 2 - t1.get_width() // 2, 22))

        manager_str = ""
        if hasattr(ui, 'manager_fornavn') and ui.manager_fornavn:
            manager_str = f"Manager: {ui.manager_fornavn} {ui.manager_etternavn}"

        # Club name
        t_k = fb.render(self.klubb_navn, True, P.TEKST)
        surf.blit(t_k, (W_BASE // 2 - t_k.get_width() // 2, 96))
        if manager_str:
            t_m = fs.render(manager_str, True, P.TEKST_SVAK)
            surf.blit(t_m, (W_BASE // 2 - t_m.get_width() // 2, 122))

        # Stats
        hist     = self.resultater
        seiere   = hist.count("S")
        uavgjort = hist.count("U")
        tap      = hist.count("T")
        poeng    = seiere * 3 + uavgjort

        stats_panel_x = W_BASE // 2 - 220
        pygame.draw.rect(surf, P.PANEL, (stats_panel_x, 148, 440, 200))
        pygame.draw.rect(surf, P.GRÅ_MØRK, (stats_panel_x, 148, 440, 200), 1)

        rows = [
            ("Kamper spilt:", str(len(hist)),  P.TEKST),
            ("Seiere:",        str(seiere),     P.GRØNN),
            ("Uavgjort:",      str(uavgjort),   P.GULT),
            ("Tap:",           str(tap),        P.RØD),
            ("Poeng:",         str(poeng),      P.HVIT),
        ]
        for i, (label, verdi, vfarge) in enumerate(rows):
            ry = 162 + i * 34
            tegn_tekst(surf, label, (stats_panel_x + 20, ry), f, P.TEKST_SVAK)
            t_v = fb.render(verdi, True, vfarge)
            surf.blit(t_v, (stats_panel_x + 420 - t_v.get_width(), ry - 2))

        # League position
        if self.tabell:
            plass = self.tabell.plass(self.klubb_navn)
            pos_y = 368
            pygame.draw.rect(surf, P.BLÅ, (W_BASE // 2 - 200, pos_y, 400, 50))
            pygame.draw.rect(surf, P.BLÅLL, (W_BASE // 2 - 200, pos_y, 400, 50), 1)
            pos_t = fb.render(f"ENDELIG TABELLPLASS:  {plass}.", True, P.HVIT)
            surf.blit(pos_t, (W_BASE // 2 - pos_t.get_width() // 2, pos_y + 12))

        btn_rect = (W_BASE // 2 - 120, H_BASE - 70, 240, 46)
        tegn_knapp(surf, btn_rect, "NESTE SESONG", Fonter.tittel,
                   hovered=ui.mus_innenfor(btn_rect))

        _tegn_bunnlinje(surf, "ENTER = NESTE SESONG  |  ESC = AVSLUTT")

    def håndter_event(self, event, ui):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.on_fortsett()
            elif event.key == pygame.K_ESCAPE:
                self.on_avslutt()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            btn_rect = (W_BASE // 2 - 120, H_BASE - 70, 240, 46)
            bx, by, bw, bh = btn_rect
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                self.on_fortsett()



# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: CLUB INFO PAGE
# ─────────────────────────────────────────────────────────────────────────────
class KlubbInfoSkjerm(SkjermData):
    """Full club information page with tabs for players, staff, economy, schedule and records."""

    SYNLIGE = 20
    FANER = ["OVERSIKT", "SPILLERE", "ANSATTE", "ØKONOMI", "TERMINLISTE", "REKORDER"]

    def __init__(self, klubb, tabell=None, terminliste=None,
                 stat_register=None, on_tilbake: Callable = None,
                 on_spillerkort: Callable = None, start_fane: int = 0):
        self.klubb          = klubb
        self.tabell         = tabell          # Seriatabell for this club's division
        self.terminliste    = terminliste or []  # list of Kamp objects involving this club
        self.stat_register  = stat_register   # SpillerStatistikkRegister
        self.on_tilbake     = on_tilbake or (lambda: None)
        self.on_spillerkort = on_spillerkort  # Callable(spiller, liste, idx)
        self._fane          = start_fane
        self._scroll        = 0
        self._hover_idx     = -1

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _spillere_sortert(self):
        from person import Posisjon, FORSVAR, MIDTBANE, ANGREP
        sone_orden = {}
        for p in FORSVAR:
            sone_orden[p] = 1
        for p in MIDTBANE:
            sone_orden[p] = 2
        for p in ANGREP:
            sone_orden[p] = 3
        def _sort_key(s):
            pos = getattr(s, 'primær_posisjon', None)
            sone = sone_orden.get(pos, 4)
            return (sone, -getattr(s, 'ferdighet', 0))
        return sorted(self.klubb.spillerstall, key=_sort_key)

    def _maks_scroll(self):
        if self._fane == 1:
            return max(0, len(self._spillere_sortert()) - self.SYNLIGE)
        if self._fane == 4:
            return max(0, len(self.terminliste) - self.SYNLIGE)
        if self._fane == 5:
            antall = len(self._rekorder_rader())
            return max(0, antall - self.SYNLIGE)
        return 0

    def _rekorder_rader(self):
        """Returns list of (label, value, farge) tuples for the records tab."""
        rader = []
        if not self.stat_register:
            return rader
        # Top scorers from this club
        alle = list(self.stat_register._data.values())
        fra_klubb = [s for s in alle if any(
            getattr(sp, 'id', None) == s.spiller_id
            for sp in self.klubb.spillerstall
        )]
        fra_klubb.sort(key=lambda s: s.mål, reverse=True)
        for i, stat in enumerate(fra_klubb[:10]):
            if stat.mål == 0:
                break
            rader.append((stat.spiller_navn, f"{stat.mål} mål  ({stat.kamper} k)", P.GRØNN))
        # Best rating
        fra_klubb_rtg = [s for s in fra_klubb if s.kamper >= 3]
        fra_klubb_rtg.sort(key=lambda s: s.snitt_rating, reverse=True)
        if fra_klubb_rtg:
            best = fra_klubb_rtg[0]
            rader.append((best.spiller_navn, f"Snittrating {best.snitt_rating:.1f}", P.GULT))
        return rader

    # ── Drawing ───────────────────────────────────────────────────────────────

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)
        k = self.klubb
        _tegn_topplinje(surf, k.navn.upper(), k.divisjon, "KLUBBSIDE")

        # Tabs
        tab_y = 28
        tab_w = (W_BASE - 8) // len(self.FANER)
        for fi, tekst in enumerate(self.FANER):
            er_aktiv = fi == self._fane
            tab_rect = (4 + fi * tab_w, tab_y, tab_w - 2, 22)
            tegn_knapp(surf, tab_rect, tekst, Fonter.fet, valgt=er_aktiv,
                       hovered=not er_aktiv and ui.mus_innenfor(tab_rect))
        tegn_linje_h(surf, P.HEADER_KANT, 0, tab_y + 21, W_BASE, 1)

        innhold_y = 52

        if self._fane == 0:
            self._tegn_oversikt(surf, innhold_y)
        elif self._fane == 1:
            self._tegn_spillere(surf, ui, innhold_y)
        elif self._fane == 2:
            self._tegn_ansatte(surf, innhold_y)
        elif self._fane == 3:
            self._tegn_okonomi(surf, innhold_y)
        elif self._fane == 4:
            self._tegn_terminliste(surf, ui, innhold_y)
        elif self._fane == 5:
            self._tegn_rekorder(surf, innhold_y)

        btn_rect = (W_BASE // 2 - 90, H_BASE - 44, 180, 34)
        tegn_knapp(surf, btn_rect, "TILBAKE", Fonter.stor,
                   hovered=ui.mus_innenfor(btn_rect))
        _tegn_bunnlinje(surf, "TAB = BYTT FANE   ↑↓ = SCROLL   ESC = TILBAKE")

    def _tegn_oversikt(self, surf, y0):
        k = self.klubb
        f  = Fonter.liten
        fn = Fonter.normal
        fb = Fonter.stor

        # Club name banner
        pygame.draw.rect(surf, P.PANEL, (0, y0, W_BASE, 50))
        tegn_linje_h(surf, P.HEADER_KANT, 0, y0 + 49, W_BASE, 1)
        t_navn = Fonter.tittel.render(k.navn, True, P.GULT)
        surf.blit(t_navn, (16, y0 + 12))
        tegn_tekst(surf, k.divisjon, (W_BASE - 200, y0 + 18), fn, P.TEKST_SVAK)

        y = y0 + 58

        # Left column
        def rad(label, verdi, farge=P.TEKST, y_off=0):
            tegn_tekst(surf, label, (16, y + y_off), f, P.TEKST_SVAK)
            tegn_tekst(surf, verdi, (220, y + y_off), fn, farge)

        info = [
            ("Grunnlagt:",       str(k.grunnlagt_aar)),
            ("Farger:",          ", ".join(k.farger) if k.farger else "–"),
            ("Rivaler:",         ", ".join(k.rivaler) if k.rivaler else "Ingen"),
        ]
        for i, (lbl, val) in enumerate(info):
            tegn_tekst(surf, lbl, (16, y + i * 24), f, P.TEKST_SVAK)
            tegn_tekst(surf, val, (220, y + i * 24), fn, P.TEKST, max_bredde=360)

        y += len(info) * 24 + 12
        tegn_linje_h(surf, P.PANEL_LYS, 0, y, W_BASE // 2, 1)
        y += 10

        # Stadium
        s = k.stadion
        tegn_tekst(surf, "STADION", (16, y), Fonter.fet, P.BLÅLL)
        y += 22
        if s:
            stadium_info = [
                ("Navn:",       s.navn),
                ("Kapasitet:",  f"{s.kapasitet:,}"),
                ("Standard:",   s.standard_tekst),
                ("Byggeår:",    str(s.byggeaar)),
            ]
            for lbl, val in stadium_info:
                tegn_tekst(surf, lbl, (16, y), f, P.TEKST_SVAK)
                tegn_tekst(surf, val, (220, y), fn, P.TEKST)
                y += 22
        else:
            tegn_tekst(surf, "Ingen stadion registrert", (16, y), fn, P.TEKST_SVAK)
            y += 22

        y += 8
        tegn_linje_h(surf, P.PANEL_LYS, 0, y, W_BASE // 2, 1)
        y += 10

        # Manager
        mgr = k.naavaerende_manager
        tegn_tekst(surf, "MANAGER:", (16, y), f, P.TEKST_SVAK)
        mgr_navn = mgr.fullt_navn if mgr else "Ledig"
        tegn_tekst(surf, mgr_navn, (220, y), fn, P.GULT if mgr else P.RØD)

        # Right column — culture ratings
        rx = W_BASE // 2 + 20
        ry = y0 + 58
        kultur = [
            ("Supporterbase",     k.supporterbase),
            ("Ambisjonsnivå",     k.ambisjonsnivaa),
            ("Historisk suksess", k.historisk_suksess),
        ]
        tegn_tekst(surf, "KLUBBKULTUR", (rx, ry - 24), Fonter.fet, P.BLÅLL)
        for i, (lbl, verdi) in enumerate(kultur):
            ky = ry + i * 40
            tegn_tekst(surf, lbl, (rx, ky), f, P.TEKST_SVAK)
            bar_x = rx
            bar_y = ky + 16
            bar_w = 280
            pygame.draw.rect(surf, P.PANEL_LYS, (bar_x, bar_y, bar_w, 10))
            farge = (P.GRØNN if verdi >= 14 else P.GULT if verdi >= 8 else P.RØD)
            fylt = int((verdi / 20.0) * bar_w)
            if fylt > 0:
                pygame.draw.rect(surf, farge, (bar_x, bar_y, fylt, 10))
            tegn_tekst(surf, f"{verdi}/20", (bar_x + bar_w + 8, ky + 14), f, P.TEKST)

        # Economic status badge
        ek_y = ry + len(kultur) * 40 + 20
        if k.er_i_okonomisk_krise:
            pygame.draw.rect(surf, P.RØD, (rx, ek_y, 200, 28))
            tegn_tekst(surf, "! ØKONOMISK KRISE", (rx + 10, ek_y + 7), fn, P.HVIT)
        elif k.har_rik_eier:
            pygame.draw.rect(surf, P.GRØNN, (rx, ek_y, 200, 28))
            tegn_tekst(surf, "RIK EIER", (rx + 10, ek_y + 7), fn, P.SVART)
        else:
            pygame.draw.rect(surf, P.PANEL, (rx, ek_y, 200, 28))
            pygame.draw.rect(surf, P.GRÅ_MØRK, (rx, ek_y, 200, 28), 1)
            tegn_tekst(surf, "Stabil økonomi", (rx + 10, ek_y + 7), fn, P.TEKST)

        # Table position
        if self.tabell:
            plass = self.tabell.plass(k.navn)
            tp_y = ek_y + 40
            tegn_tekst(surf, "Tabellplass:", (rx, tp_y), f, P.TEKST_SVAK)
            tegn_badge(surf, str(plass), (rx + 130, tp_y - 1),
                       P.BLÅ, P.HVIT, Fonter.stor)

    def _tegn_spillere(self, surf, ui, y0):
        f  = Fonter.liten
        fn = Fonter.normal
        spillere = self._spillere_sortert()

        KOL = [
            ("POS",   4),
            ("NAVN",  50),
            ("ALDER", 380),
            ("OVR",   430),
            ("KONTRAKT", 476),
            ("LØNN/UKE", 570),
        ]
        _tegn_kolonne_header(surf, KOL, y=y0, h=22)

        rad_h = 26
        y_start = y0 + 22
        start = self._scroll
        slutt = min(start + self.SYNLIGE, len(spillere))
        mx, my = ui.base_mus()

        for i, s in enumerate(spillere[start:slutt]):
            ry = y_start + i * rad_h
            er_hover = (y_start + i * rad_h <= my < y_start + i * rad_h + rad_h
                        and 0 <= mx < W_BASE - 10)
            if er_hover:
                pygame.draw.rect(surf, P.RAD_HOVER, (0, ry, W_BASE - 10, rad_h - 1))
            elif i % 2 == 0:
                pygame.draw.rect(surf, P.RAD_MØRK, (0, ry, W_BASE - 10, rad_h - 1))
            else:
                pygame.draw.rect(surf, P.RAD_LYS, (0, ry, W_BASE - 10, rad_h - 1))

            pos = getattr(s, 'primær_posisjon', None)
            pos_str = pos.name if pos else '?'
            ovr = s.ferdighet
            ovr_farge = P.GRØNN if ovr >= 14 else (P.GULT if ovr >= 10 else P.RØD)
            skadet = getattr(s, 'skadet', False)
            navn_farge = P.RØD if skadet else P.TEKST

            kontrakt = getattr(s, 'kontrakt', None)
            utlop = str(getattr(kontrakt, 'utlops_aar', '?')) if kontrakt else '–'
            lonn  = getattr(kontrakt, 'ukelonn', 0) if kontrakt else 0

            tegn_tekst(surf, pos_str,         (6,   ry + 5), f, P.TEKST_SVAK)
            tegn_tekst(surf, getattr(s, 'fullt_navn', '?'), (52, ry + 5), fn, navn_farge, max_bredde=322)
            tegn_tekst(surf, str(s.alder),    (382, ry + 5), f, P.TEKST_SVAK)
            tegn_badge(surf, str(ovr),        (432, ry + 3), P.PANEL, ovr_farge, f)
            tegn_tekst(surf, utlop,           (478, ry + 5), f, P.TEKST)
            tegn_tekst(surf, f"{lonn:,}",     (572, ry + 5), f, P.TEKST_SVAK)

        tegn_scrollbar(surf, W_BASE - 8, y_start, self.SYNLIGE * rad_h,
                       len(spillere), self.SYNLIGE, self._scroll)

    def _tegn_ansatte(self, surf, y0):
        f  = Fonter.liten
        fn = Fonter.normal
        fb = Fonter.stor
        k  = self.klubb
        y  = y0 + 8

        # Manager
        pygame.draw.rect(surf, P.PANEL, (0, y, W_BASE, 26))
        tegn_tekst(surf, "MANAGER", (8, y + 6), Fonter.fet, P.BLÅLL)
        y += 28

        mgr = k.naavaerende_manager
        if mgr:
            pygame.draw.rect(surf, P.RAD_MØRK, (0, y, W_BASE - 10, 28))
            tegn_tekst(surf, mgr.fullt_navn, (12, y + 7), fn, P.GULT)
            tegn_tekst(surf, f"Alder: {mgr.alder}", (400, y + 7), f, P.TEKST_SVAK)
            kontrakt = getattr(mgr, 'kontrakt', None)
            if kontrakt:
                tegn_tekst(surf, f"Kontrakt til: {kontrakt.utlops_aar}", (560, y + 7), f, P.TEKST)
        else:
            tegn_tekst(surf, "Ingen manager ansatt", (12, y + 7), fn, P.RØD)
        y += 34

        # Coaches
        trenere = k.trenerstab
        pygame.draw.rect(surf, P.PANEL, (0, y, W_BASE, 26))
        tegn_tekst(surf, f"TRENERSTAB  ({len(trenere)} trenere)", (8, y + 6), Fonter.fet, P.BLÅLL)
        y += 28

        from person import TrenerRolle
        for i, t in enumerate(trenere):
            ry = y + i * 28
            if i % 2 == 0:
                pygame.draw.rect(surf, P.RAD_MØRK, (0, ry, W_BASE - 10, 27))
            else:
                pygame.draw.rect(surf, P.RAD_LYS, (0, ry, W_BASE - 10, 27))
            tegn_tekst(surf, t.fullt_navn, (12, ry + 7), fn, P.TEKST)
            rolle = t.hent_naavaerende_rolle()
            if isinstance(rolle, TrenerRolle):
                tegn_tekst(surf, rolle.spesialitet, (380, ry + 7), f, P.CYAN)
            tegn_tekst(surf, f"Alder: {t.alder}", (560, ry + 7), f, P.TEKST_SVAK)

        if not trenere:
            tegn_tekst(surf, "Ingen trenere registrert", (12, y + 7), fn, P.TEKST_SVAK)

        # Other staff (non-player, non-manager, non-coach)
        from person import SpillerRolle, ManagerRolle
        andre = [p for p in k._alt_personell
                 if not isinstance(p.hent_naavaerende_rolle(), (SpillerRolle, TrenerRolle, ManagerRolle))]
        if andre:
            y_andre = y + max(len(trenere), 1) * 28 + 16
            pygame.draw.rect(surf, P.PANEL, (0, y_andre, W_BASE, 26))
            tegn_tekst(surf, "ØVRIG STAB", (8, y_andre + 6), Fonter.fet, P.BLÅLL)
            y_andre += 28
            for i, p in enumerate(andre):
                ry = y_andre + i * 28
                if i % 2 == 0:
                    pygame.draw.rect(surf, P.RAD_MØRK, (0, ry, W_BASE - 10, 27))
                else:
                    pygame.draw.rect(surf, P.RAD_LYS, (0, ry, W_BASE - 10, 27))
                tegn_tekst(surf, p.fullt_navn, (12, ry + 7), fn, P.TEKST)
                rolle = p.hent_naavaerende_rolle()
                tegn_tekst(surf, type(rolle).__name__ if rolle else "?", (380, ry + 7), f, P.TEKST_SVAK)

    def _tegn_okonomi(self, surf, y0):
        f  = Fonter.liten
        fn = Fonter.normal
        k  = self.klubb
        y  = y0 + 16

        def saldo_farge(v):
            return P.GRØNN if v >= 0 else P.RØD

        def tegn_rad(label, verdi_str, farge, y_pos):
            pygame.draw.rect(surf, P.RAD_MØRK, (40, y_pos, W_BASE - 80, 36))
            tegn_tekst(surf, label, (56, y_pos + 10), fn, P.TEKST_SVAK)
            t = Fonter.stor.render(verdi_str, True, farge)
            surf.blit(t, (W_BASE - 80 - t.get_width(), y_pos + 8))

        rader = [
            ("Saldo",                  f"kr {k.saldo:,.0f}",                       saldo_farge(k.saldo)),
            ("Gjeld",                  f"kr {k.gjeld:,.0f}",                        P.RØD if k.gjeld > 0 else P.TEKST_SVAK),
            ("Ukentlig lønnsbudsjett", f"kr {k.ukentlig_loennsbudsjett:,.0f}",      P.TEKST),
            ("Faktisk ukentlig lønn",  f"kr {k.total_ukentlig_loennskostnad:,.0f}", P.ORANSJE),
            ("Stadionvedlikehold/uke", f"kr {k.stadion.ukentlig_vedlikehold:,.0f}" if k.stadion else "–", P.TEKST_SVAK),
            ("Rik eier",               "Ja" if k.har_rik_eier else "Nei",           P.GRØNN if k.har_rik_eier else P.TEKST_SVAK),
            ("Hovedsponsor",           k.hovedsponsor or "Ingen",                   P.CYAN if k.hovedsponsor else P.TEKST_SVAK),
        ]

        for i, (lbl, val, farge) in enumerate(rader):
            tegn_rad(lbl, val, farge, y + i * 44)

        if k.er_i_okonomisk_krise:
            krise_y = y + len(rader) * 44 + 10
            pygame.draw.rect(surf, P.RØD, (40, krise_y, W_BASE - 80, 36))
            t = fn.render("ADVARSEL: Klubben er i økonomisk krise!", True, P.HVIT)
            surf.blit(t, (W_BASE // 2 - t.get_width() // 2, krise_y + 10))

    def _tegn_terminliste(self, surf, ui, y0):
        f  = Fonter.liten
        fn = Fonter.normal
        k  = self.klubb

        KOL = [("RD", 4), ("DATO", 40), ("HJEMME", 120), ("RESULTAT", 420), ("BORTE", 530)]
        _tegn_kolonne_header(surf, KOL, y=y0, h=22)

        rad_h = 26
        y_start = y0 + 22
        kamper = self.terminliste
        start = self._scroll
        slutt = min(start + self.SYNLIGE, len(kamper))

        for i, kamp in enumerate(kamper[start:slutt]):
            ry = y_start + i * rad_h
            if i % 2 == 0:
                pygame.draw.rect(surf, P.RAD_MØRK, (0, ry, W_BASE - 10, rad_h - 1))
            else:
                pygame.draw.rect(surf, P.RAD_LYS, (0, ry, W_BASE - 10, rad_h - 1))

            hjemme_obj = getattr(kamp, 'hjemme', None)
            borte_obj  = getattr(kamp, 'borte', None)
            hjemme_navn = getattr(hjemme_obj, 'navn', '?') if hjemme_obj else '?'
            borte_navn  = getattr(borte_obj, 'navn', '?') if borte_obj else '?'
            runde = getattr(kamp, 'runde', i + start + 1)
            spilt  = getattr(kamp, 'spilt', False)
            dato   = getattr(kamp, 'dato', None)
            dato_str = dato.strftime('%d.%m') if dato else '–'

            er_hjemme = (hjemme_obj == k)
            hjemme_farge = P.GULT if er_hjemme else P.TEKST
            borte_farge  = P.TEKST if er_hjemme else P.GULT

            tegn_tekst(surf, str(runde),       (6,   ry + 5), f, P.TEKST_SVAK)
            tegn_tekst(surf, dato_str,         (42,  ry + 5), f, P.TEKST_SVAK)
            tegn_tekst(surf, hjemme_navn,      (122, ry + 5), fn, hjemme_farge, max_bredde=290)
            tegn_tekst(surf, borte_navn,       (532, ry + 5), fn, borte_farge,  max_bredde=290)

            if spilt:
                hm = getattr(kamp, 'hjemme_maal', 0)
                bm = getattr(kamp, 'borte_maal', 0)
                score = f"{hm}  –  {bm}"
                # Determine result for our club
                if er_hjemme:
                    res_farge = P.GRØNN if hm > bm else (P.RØD if hm < bm else P.GULT)
                else:
                    res_farge = P.GRØNN if bm > hm else (P.RØD if bm < hm else P.GULT)
                t_sc = fn.render(score, True, res_farge)
                surf.blit(t_sc, (422 + (100 - t_sc.get_width()) // 2, ry + 5))
            else:
                tegn_tekst(surf, "– – –", (440, ry + 5), f, P.TEKST_SVAK)

        tegn_scrollbar(surf, W_BASE - 8, y_start, self.SYNLIGE * rad_h,
                       len(kamper), self.SYNLIGE, self._scroll)

    def _tegn_rekorder(self, surf, y0):
        f  = Fonter.liten
        fn = Fonter.normal
        k  = self.klubb
        y  = y0

        # Season stats from division table
        if self.tabell:
            rad = self.tabell._rader.get(k.navn)
            if rad:
                pygame.draw.rect(surf, P.PANEL, (0, y, W_BASE, 28))
                tegn_tekst(surf, "SESONGSTATISTIKK", (8, y + 7), Fonter.fet, P.BLÅLL)
                y += 30

                sesong_info = [
                    ("Kamper:",     str(rad.kamp),          P.TEKST),
                    ("Seiere:",     str(rad.seier),         P.GRØNN),
                    ("Uavgjort:",   str(rad.uavgjort),      P.GULT),
                    ("Tap:",        str(rad.tap),           P.RØD),
                    ("Mål for:",    str(rad.mål_for),       P.TEKST),
                    ("Mål mot:",    str(rad.mål_mot),       P.TEKST),
                    ("Differanse:", (f"+{rad.mål_differanse}" if rad.mål_differanse > 0
                                    else str(rad.mål_differanse)),
                                   P.GRØNN if rad.mål_differanse > 0 else (P.RØD if rad.mål_differanse < 0 else P.TEKST_SVAK)),
                    ("Poeng:",      str(rad.poeng),         P.HVIT),
                ]
                col_w = W_BASE // 4
                for idx, (lbl, val, farge) in enumerate(sesong_info):
                    col = idx % 4
                    row = idx // 4
                    cx = col * col_w + 16
                    cy = y + row * 36
                    tegn_tekst(surf, lbl, (cx, cy + 2), f, P.TEKST_SVAK)
                    t_v = Fonter.stor.render(val, True, farge)
                    surf.blit(t_v, (cx, cy + 16))
                y += ((len(sesong_info) + 3) // 4) * 36 + 12

        # Player records from stat register
        if self.stat_register and hasattr(self.stat_register, '_data'):
            pygame.draw.rect(surf, P.PANEL, (0, y, W_BASE, 28))
            tegn_tekst(surf, "TOPPSCORERE (DIVISJON)", (8, y + 7), Fonter.fet, P.BLÅLL)
            y += 30

            alle = sorted(self.stat_register._data.values(),
                          key=lambda s: s.mål, reverse=True)
            spillere_id = {getattr(sp, 'id', None) for sp in k.spillerstall}

            KOL = [("#", 4), ("SPILLER", 36), ("KLUBB", 360), ("K", 480), ("MÅL", 520), ("RTG", 600)]
            _tegn_kolonne_header(surf, KOL, y=y, h=22)
            y += 22

            start = self._scroll
            for i, stat in enumerate(alle[start:start + self.SYNLIGE]):
                ry = y + i * 26
                er_fra_klubb = (stat.spiller_id in spillere_id)
                if i % 2 == 0:
                    farge_bg = P.RAD_MØRK
                else:
                    farge_bg = P.RAD_LYS
                pygame.draw.rect(surf, farge_bg, (0, ry, W_BASE - 10, 25))
                if er_fra_klubb:
                    pygame.draw.rect(surf, P.RAD_VALGT, (0, ry, W_BASE - 10, 25))

                navn_farge = P.GULT if er_fra_klubb else P.TEKST
                tegn_tekst(surf, str(start + i + 1), (6, ry + 5), f, P.TEKST_SVAK)
                tegn_tekst(surf, stat.spiller_navn, (38, ry + 5), fn, navn_farge, max_bredde=318)
                tegn_tekst(surf, str(stat.kamper), (482, ry + 5), f, P.TEKST_SVAK)
                tegn_badge(surf, str(stat.mål), (522, ry + 3), P.GRØNN, P.SVART, f)
                tegn_tekst(surf, f"{stat.snitt_rating:.1f}", (602, ry + 5), f, P.GULT)

            tegn_scrollbar(surf, W_BASE - 8, y, self.SYNLIGE * 26,
                           len(alle), self.SYNLIGE, self._scroll)

    # ── Events ────────────────────────────────────────────────────────────────

    def håndter_event(self, event, ui):
        maks = self._maks_scroll()

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.on_tilbake()
            elif event.key == pygame.K_TAB:
                self._fane = (self._fane + 1) % len(self.FANER)
                self._scroll = 0
            elif event.key == pygame.K_DOWN:
                self._scroll = min(maks, self._scroll + 1)
            elif event.key == pygame.K_UP:
                self._scroll = max(0, self._scroll - 1)
            elif event.key == pygame.K_LEFT:
                self._fane = (self._fane - 1) % len(self.FANER)
                self._scroll = 0
            elif event.key == pygame.K_RIGHT:
                self._fane = (self._fane + 1) % len(self.FANER)
                self._scroll = 0

        elif event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, min(maks, self._scroll - event.y))

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()

            # Tab clicks
            tab_w = (W_BASE - 8) // len(self.FANER)
            for fi in range(len(self.FANER)):
                tab_rect = (4 + fi * tab_w, 28, tab_w - 2, 22)
                tx, ty, tw, th = tab_rect
                if tx <= mx <= tx + tw and ty <= my <= ty + th:
                    self._fane = fi
                    self._scroll = 0
                    return

            # Back button
            btn_rect = (W_BASE // 2 - 90, H_BASE - 44, 180, 34)
            bx, by, bw, bh = btn_rect
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                self.on_tilbake()
                return

            # Player row clicks on SPILLERE tab
            if self._fane == 1 and self.on_spillerkort:
                innhold_y = 52
                rad_h = 26
                y_start = innhold_y + 22
                spillere = self._spillere_sortert()
                start = self._scroll
                for i in range(min(self.SYNLIGE, len(spillere) - start)):
                    ry = y_start + i * rad_h
                    if ry <= my < ry + rad_h and 0 <= mx < W_BASE - 10:
                        idx = start + i
                        self.on_spillerkort(spillere[idx], spillere, idx)
                        return


# ─────────────────────────────────────────────────────────────────────────────
# UI MOTOR
# ─────────────────────────────────────────────────────────────────────────────
class UIMotor:
    """
    Main UI engine.
    - Holds a screen stack — topmost screen is active
    - 1024x768 base canvas, SKALA=1 (no scaling)
    - Provides push/pop_skjerm for navigation
    - Driven by spillmotor.py via tikk()
    """

    def __init__(self):
        pygame.init()
        Fonter.init()
        self._skjerm  = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITTEL)
        self._klokke  = pygame.time.Clock()
        self._base    = pygame.Surface((W_BASE, H_BASE))
        self._stack: list[SkjermData] = []
        self._kjører  = True
        self._mus_pos = (0, 0)
        self._pauset  = False
        pygame.mouse.set_visible(True)
        # Optional manager info
        self.manager_fornavn    = ""
        self.manager_etternavn  = ""

    # ── Navigation ────────────────────────────────────────────────────────────
    def push_skjerm(self, skjerm: SkjermData):
        self._stack.append(skjerm)

    def pop_skjerm(self) -> Optional[SkjermData]:
        if self._stack:
            return self._stack.pop()
        return None

    def bytt_skjerm(self, skjerm: SkjermData):
        """Replace topmost screen."""
        if self._stack:
            self._stack[-1] = skjerm
        else:
            self._stack.append(skjerm)

    def tøm_og_sett(self, skjerm: SkjermData):
        """Clear stack and set new root screen."""
        self._stack.clear()
        self._stack.append(skjerm)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def base_mus(self) -> tuple:
        """Return mouse position in base coordinates (1024x768, SKALA=1)."""
        return self._mus_pos

    def mus_innenfor(self, rect: tuple) -> bool:
        """Check whether mouse is inside rect (x, y, w, h) in base coordinates."""
        x, y, w, h = rect
        mx, my = self._mus_pos
        return x <= mx < x + w and y <= my < y + h

    def avslutt(self):
        self._kjører = False

    # ── Main event loop ───────────────────────────────────────────────────────
    def tikk(self) -> bool:
        """
        Run one frame. Returns True while game is running.
        Called by spillmotor.py in its game loop.
        """
        self._klokke.tick(FPS)
        self._mus_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._kjører = False
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                self._pauset = not self._pauset

            if self._stack:
                self._stack[-1].håndter_event(event, self)

        # Draw topmost screen
        self._base.fill(P.BAKGRUNN)
        if self._stack:
            self._stack[-1].tegn(self._base, self)
            if self._pauset:
                _tegn_topplinje(self._base, "", "PAUSET", "P = FORTSETT",
                                is_pauset=True)

        # Blit 1:1 to window (SKALA=1)
        self._skjerm.blit(self._base, (0, 0))
        pygame.display.flip()

        return self._kjører

    def start_modal(self, skjerm: SkjermData) -> None:
        """
        Blocking modal: run UI loop until screen pops itself.
        Used by spillmotor for awaiting user input.
        """
        self.push_skjerm(skjerm)
        ferdig = False

        original_callback = None
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
        Run modal and return result.
        Screen sets self._resultat and calls on_ferdig().
        """
        self.push_skjerm(skjerm)
        while self._kjører:
            if not self.tikk():
                break
            if hasattr(skjerm, '_ferdig') and skjerm._ferdig:
                break
        self.pop_skjerm()
        return getattr(skjerm, '_resultat', None)
