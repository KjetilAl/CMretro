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
W_BASE, H_BASE = 640, 400
SKALA          = 2
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
            cls.liten  = pygame.font.SysFont("Courier New", 13,  bold=False)
            cls.normal = pygame.font.SysFont("Courier New", 15, bold=False)
            cls.fet    = pygame.font.SysFont("Courier New", 15, bold=True)
            cls.stor   = pygame.font.SysFont("Courier New", 20, bold=True)
            cls.tittel = pygame.font.SysFont("Courier New", 26, bold=True)
        except Exception:
            cls.liten  = pygame.font.Font(None, 15)
            cls.normal = pygame.font.Font(None, 18)
            cls.fet    = pygame.font.Font(None, 18)
            cls.stor   = pygame.font.Font(None, 24)
            cls.tittel = pygame.font.Font(None, 30)
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
def _tegn_topplinje(surf, venstre: str, midtre: str, høyre: str, font=None, is_pauset: bool=False):
    """Toppstripel i NAVY med tre tekstfelt."""
    if font is None:
        font = Fonter.liten
    pygame.draw.rect(surf, P.NAVY, (0, 0, W_BASE, 24))
    pygame.draw.rect(surf, P.BLÅL, (0, 23, W_BASE, 2))
    tegn_tekst(surf, venstre, (4, 4), font, P.GULT)
    mid_t = font.render(midtre, False, P.KREMHVIT)
    surf.blit(mid_t, (W_BASE//2 - mid_t.get_width()//2, 4))
    høyre_t = font.render(høyre, False, P.LYSBLÅ_UI)
    surf.blit(høyre_t, (W_BASE - høyre_t.get_width() - 4, 4))
    if is_pauset:
        pygame.draw.rect(surf, P.GULT, (W_BASE - 50, 4, 46, 16))
        tegn_tekst(surf, "PAUSET", (W_BASE - 48, 6), font, P.SVART)

def _tegn_bunnlinje(surf, tekst: str, font=None):
    """Statuslinje nederst."""
    if font is None:
        font = Fonter.liten
    pygame.draw.rect(surf, P.NAVY, (0, H_BASE-22, W_BASE, 22))
    pygame.draw.rect(surf, P.BLÅL, (0, H_BASE-24, W_BASE, 2))
    tegn_tekst(surf, tekst, (6, H_BASE-18), font, P.GRÅ_LYS)

def _tegn_bakgrunn(surf, farge=None):
    if farge is None:
        farge = P.GRÅ_PANEL
    surf.fill(farge)
    # Subtil horisontal rutenett-overlay
    for y in range(0, H_BASE, 16):
        pygame.draw.line(surf, (farge[0]+4, farge[1]+4, farge[2]+6), (0, y), (W_BASE, y))


# ─────────────────────────────────────────────────────────────────────────────
# SKJERM: OPPRETT MANAGER
# ─────────────────────────────────────────────────────────────────────────────
class OpprettManagerSkjerm(SkjermData):
    """
    Vises én gang ved ny sesong, etter at klubb er valgt.
    Spilleren skriver inn fornavn og etternavn med tastatur.
    """
    def __init__(self, klubb_navn: str, on_ferdig: Callable[[str, str], None]):
        self.klubb_navn  = klubb_navn
        self.on_ferdig   = on_ferdig
        self.fornavn     = ""
        self.etternavn   = ""
        self._aktiv_felt = 0   # 0=fornavn, 1=etternavn

    def tegn(self, surf, ui):
        surf.fill(P.NAVY)
        for y in range(H_BASE):
            mørkhet = y // 3
            r, g, b = P.NAVY
            pygame.draw.line(surf, (max(0, r-mørkhet//2),
                                    max(0, g-mørkhet//2),
                                    min(255, b+mørkhet//4)),
                             (0, y), (W_BASE, y))

        fb = Fonter.stor
        f  = Fonter.normal

        # Tittel
        tittel = f"NY MANAGER — {self.klubb_navn.upper()}"
        t = fb.render(tittel, False, P.GULT)
        surf.blit(t, (W_BASE//2 - t.get_width()//2, 40))

        # Felt 0: Fornavn
        pygame.draw.rect(surf, P.GRÅ_PANEL, (W_BASE//2 - 100, 100, 200, 30))
        kant_farge_0 = P.GULT if self._aktiv_felt == 0 else P.GRÅ_MØRK
        pygame.draw.rect(surf, kant_farge_0, (W_BASE//2 - 100, 100, 200, 30), 2)
        tegn_tekst(surf, "FORNAVN:", (W_BASE//2 - 100, 80), f, P.KREMHVIT)
        tegn_tekst(surf, self.fornavn + ("_" if self._aktiv_felt == 0 else ""),
                   (W_BASE//2 - 90, 106), f, P.HVIT)

        # Felt 1: Etternavn
        pygame.draw.rect(surf, P.GRÅ_PANEL, (W_BASE//2 - 100, 180, 200, 30))
        kant_farge_1 = P.GULT if self._aktiv_felt == 1 else P.GRÅ_MØRK
        pygame.draw.rect(surf, kant_farge_1, (W_BASE//2 - 100, 180, 200, 30), 2)
        tegn_tekst(surf, "ETTERNAVN:", (W_BASE//2 - 100, 160), f, P.KREMHVIT)
        tegn_tekst(surf, self.etternavn + ("_" if self._aktiv_felt == 1 else ""),
                   (W_BASE//2 - 90, 186), f, P.HVIT)

        begge_fylt = len(self.fornavn) >= 2 and len(self.etternavn) >= 2

        if begge_fylt:
            tegn_knapp(surf, (W_BASE//2 - 80, 260, 160, 30), "BEKREFT →", f,
                       hovered=ui.mus_innenfor(((W_BASE//2 - 80)*SKALA, 260*SKALA, 160*SKALA, 30*SKALA)))

        _tegn_bunnlinje(surf, "TAB=BYTT FELT  ENTER=BEKREFT")

    def håndter_event(self, event, ui):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            if W_BASE//2 - 100 <= mx <= W_BASE//2 + 100:
                if 100 <= my <= 130:
                    self._aktiv_felt = 0
                elif 180 <= my <= 210:
                    self._aktiv_felt = 1

            begge_fylt = len(self.fornavn) >= 2 and len(self.etternavn) >= 2
            if begge_fylt and W_BASE//2 - 80 <= mx <= W_BASE//2 + 80 and 260 <= my <= 290:
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
                    if self._aktiv_felt == 0 and len(self.fornavn) < 20:
                        self.fornavn += char
                    elif self._aktiv_felt == 1 and len(self.etternavn) < 20:
                        self.etternavn += char

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
        tegn_bane(surf, (0, H_BASE-80, W_BASE, 80), P.GRØNN, P.HVIT)

        # Logo-boks
        logo_rect = (40, 36, W_BASE-80, 140)
        pygame.draw.rect(surf, (10, 18, 50), logo_rect)
        pygame.draw.rect(surf, P.BLÅLL, logo_rect, 2)

        f_tittel = Fonter.tittel
        f_sub    = Fonter.normal

        t1 = f_tittel.render("NORSK FOOTBALL", False, P.GULT)
        t2 = f_tittel.render("MANAGER", False, P.GULT)
        t3 = f_sub.render("'95  EDITION", False, P.CYANL)

        surf.blit(t1, (logo_rect[0] + (logo_rect[2]-t1.get_width())//2, 52))
        surf.blit(t2, (logo_rect[0] + (logo_rect[2]-t2.get_width())//2, 88))
        surf.blit(t3, (logo_rect[0] + (logo_rect[2]-t3.get_width())//2, 128))

        # Pulserende «Trykk Enter»
        if (self._tick // 30) % 2 == 0:
            t4 = Fonter.liten.render("[ TRYKK ENTER FOR Å STARTE ]", False, P.KREMHVIT)
            surf.blit(t4, ((W_BASE - t4.get_width())//2, 200))

        # Versjon/copyright
        tv = Fonter.liten.render("v0.1  ©1995 ANTROPIKK SOFTWARE", False, P.GRÅ_MØRK)
        surf.blit(tv, ((W_BASE - tv.get_width())//2, H_BASE-100))

        # Knapper
        tegn_knapp(surf, (120, 236, 160, 28), "START", Fonter.normal,
                   hovered=ui.mus_innenfor((120*SKALA, 236*SKALA, 160*SKALA, 28*SKALA)))
        tegn_knapp(surf, (360, 236, 160, 28), "AVSLUTT", Fonter.normal,
                   hovered=ui.mus_innenfor((360*SKALA, 236*SKALA, 160*SKALA, 28*SKALA)))

    def håndter_event(self, event, ui):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.on_start()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            if 120 <= mx <= 280 and 236 <= my <= 264:
                self.on_start()
            elif 360 <= mx <= 520 and 236 <= my <= 264:
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
        self._SYNLIGE = 11

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)
        _tegn_topplinje(surf, "NFM'95", "VELG KLUBB", f"{len(self.klubber)} KLUBBER")

        # Kolonnehoder
        pygame.draw.rect(surf, P.BLÅL, (4, 26, W_BASE-8, 20))
        f = Fonter.liten
        tegn_tekst(surf, "KLUBB",        (8,   28), f, P.HVIT)
        tegn_tekst(surf, "STJERNER",     (260, 28), f, P.HVIT)
        tegn_tekst(surf, "STADION",      (400, 28), f, P.HVIT)

        # Klubbliste
        synlige  = self._SYNLIGE
        start    = self._scroll
        slutt    = min(start + synlige, len(self.klubber))
        rad_h    = 28
        y0       = 50

        mx, my = ui.base_mus()

        for i, idx in enumerate(range(start, slutt)):
            k     = self.klubber[idx]
            ry    = y0 + i * rad_h

            if isinstance(k, str):
                # Det er en divisjons-separator
                pygame.draw.rect(surf, P.GRÅ_MØRK, (8, ry, W_BASE-32, rad_h-2))
                tegn_tekst(surf, f"── {k.upper()} ──", (12, ry+4), f, P.GRÅ_LYS)
                continue

            er_hover  = (8 <= mx <= W_BASE-16 and ry <= my < ry+rad_h)
            er_valgt  = (idx == self._valgt)

            if er_valgt:
                pygame.draw.rect(surf, P.BLÅL, (8, ry, W_BASE-32, rad_h-2))
            elif er_hover:
                pygame.draw.rect(surf, P.GRÅ_MØRK, (8, ry, W_BASE-32, rad_h-2))
                self._hover = idx
            elif i % 2 == 0:
                pygame.draw.rect(surf, (38, 38, 52), (8, ry, W_BASE-32, rad_h-2))

            navn    = getattr(k, 'navn', str(k))
            styrke  = getattr(k, 'historisk_styrke', 0)
            stadion = getattr(k, 'stadion', None)
            kap     = getattr(stadion, 'kapasitet', 0) if stadion else 0
            stjerner_full = min(5, styrke // 4)
            stjerner_str  = "★" * stjerner_full + "☆" * (5 - stjerner_full)

            tkfarge = P.HVIT if er_valgt else P.KREMHVIT
            tegn_tekst(surf, navn[:22],   (12,   ry+4), f, tkfarge, max_bredde=240)
            tegn_tekst(surf, stjerner_str,(264,  ry+4), f, P.GULT)
            tegn_tekst(surf, f"{kap:,}",  (400, ry+4), f, P.LYSBLÅ_UI)

        # Scrollbar
        tegn_scrollbar(surf, W_BASE-14, y0, synlige*rad_h,
                        len(self.klubber), synlige, self._scroll)

        # Bekreft-knapp (aktiv når valgt)
        aktiv = self._valgt >= 0
        tegn_knapp(surf, (W_BASE//2-80, H_BASE-48, 160, 26), "VELG KLUBB",
                   Fonter.normal, aktiv=aktiv,
                   hovered=aktiv and ui.mus_innenfor(
                       ((W_BASE//2-80)*SKALA, (H_BASE-48)*SKALA, 160*SKALA, 26*SKALA)))

        _tegn_bunnlinje(surf, "↑↓/SCROLL  ENTER=VELG  ESC=TILBAKE")

    def håndter_event(self, event, ui):
        maks_scroll = max(0, len(self.klubber) - self._SYNLIGE)
        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, min(maks_scroll, self._scroll - event.y))

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            rad_h, y0 = 28, 50
            # Klikk på rad
            for i in range(self._SYNLIGE):
                idx = self._scroll + i
                if idx >= len(self.klubber):
                    break
                k = self.klubber[idx]
                if isinstance(k, str):
                    continue  # Kan ikke klikke på separator
                ry = y0 + i * rad_h
                if 8 <= mx <= W_BASE-16 and ry <= my < ry+rad_h:
                    if self._valgt == idx:
                        self.on_valgt(self.klubber[idx])
                    else:
                        self._valgt = idx
            # Bekreft-knapp
            if (self._valgt >= 0 and
                    (W_BASE//2-80)*SKALA <= event.pos[0] <= (W_BASE//2+80)*SKALA and
                    (H_BASE-48)*SKALA  <= event.pos[1] <= (H_BASE-22)*SKALA):
                self.on_valgt(self.klubber[self._valgt])

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                start_sok = max(0, self._valgt)
                for nv in range(start_sok + 1, len(self.klubber)):
                    if not isinstance(self.klubber[nv], str):
                        self._valgt = nv
                        if self._valgt >= self._scroll + self._SYNLIGE:
                            self._scroll = min(maks_scroll, self._valgt - self._SYNLIGE + 1)
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
        manager_str = ""
        if hasattr(ui, 'manager_fornavn') and ui.manager_fornavn:
            manager_str = f"Manager: {ui.manager_fornavn} {ui.manager_etternavn}"
        _tegn_topplinje(surf, sted, dato_str, manager_str)

        f = Fonter.normal
        fb = Fonter.fet
        fs = Fonter.liten

        # Kampheader
        pygame.draw.rect(surf, P.NAVY, (8, 28, W_BASE-16, 60))
        pygame.draw.rect(surf, P.BLÅL, (8, 28, W_BASE-16, 60), 2)

        hjemme_navn = getattr(self.kamp.hjemme, 'navn', '?')
        borte_navn  = getattr(self.kamp.borte,  'navn', '?')

        t_vs = f.render("VS", False, P.GRÅ_MØRK)
        t_h  = fb.render(hjemme_navn[:16], False,
                         P.GULT if er_hjemme else P.KREMHVIT)
        t_b  = fb.render(borte_navn[:16],  False,
                         P.GULT if not er_hjemme else P.KREMHVIT)

        surf.blit(t_h,  (16,  44))
        surf.blit(t_vs, (W_BASE//2 - t_vs.get_width()//2, 44))
        surf.blit(t_b,  (W_BASE - t_b.get_width() - 16, 44))

        tegn_linje_h(surf, P.BLÅL, 8, 88, W_BASE-16)

        # Meny
        rader = self._meny_rader()
        mx, my = ui.base_mus()
        meny_y = 104
        knapp_h = 36

        for i, (tekst, _) in enumerate(rader):
            ry = meny_y + i * (knapp_h + 4)
            er_hover = (20 <= mx <= W_BASE-20 and ry <= my < ry+knapp_h)
            tegn_knapp(surf, (20, ry, W_BASE-40, knapp_h), tekst,
                       fb, hovered=er_hover)

        # Neste kamp-info
        tegn_linje_h(surf, P.GRÅ_MØRK, 8, H_BASE-44, W_BASE-16)
        tegn_tekst(surf, "ESC = INGEN KAMP DENNE RUNDEN", (8, H_BASE-40), fs, P.GRÅ_MØRK)
        _tegn_bunnlinje(surf, "F1–F4  VELG HANDLING")

    def håndter_event(self, event, ui):
        rader = self._meny_rader()
        meny_y   = 104
        knapp_h  = 36

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
                if 20 <= mx <= W_BASE-20 and ry <= my < ry+knapp_h:
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

    def __init__(self, builder, motstandernavn: str, on_ferdig: Callable, on_spillerkort: Callable = None):
        self.builder       = builder
        self.motstandernavn = motstandernavn
        self.on_ferdig     = on_ferdig
        self.on_spillerkort = on_spillerkort
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

        manager_str = ""
        if hasattr(ui, 'manager_fornavn') and ui.manager_fornavn:
            manager_str = f"Manager: {ui.manager_fornavn} {ui.manager_etternavn}"
        elif self.motstandernavn:
            manager_str = f"vs {self.motstandernavn[:10]}"

        _tegn_topplinje(surf, "LAGUTTAK",
                         self.builder.klubb.navn[:18],
                         manager_str)

        # ── Venstre kolonne: startellever ────────────────────────
        rad_h = 26
        y0    = 28
        x0    = 4

        for i, s in enumerate(self.builder.startellever):
            ry     = y0 + i * rad_h
            er_v   = (i == self._valgt_start)
            farge  = P.BLÅL if er_v else (P.NAVY if i % 2 == 0 else (28, 32, 56))
            pygame.draw.rect(surf, farge, (x0, ry, 300, rad_h-2))
            pos    = getattr(s, 'primær_posisjon', None)
            pos_s  = pos.name if pos else '?'
            ferd   = getattr(s, 'ferdighet', 0)
            navn   = f"{getattr(s, 'fornavn', '?')[0]}. {getattr(s, 'etternavn', '?')}"
            kond   = getattr(s, 'kondisjon', 100.0)
            skadet = getattr(s, 'skadet', False)

            tkf = P.HVIT if er_v else P.KREMHVIT
            tegn_tekst(surf, f"{i+1:>2}", (x0+2, ry+4), f, P.GRÅ_LYS)
            tegn_tekst(surf, navn[:14],   (x0+28, ry+4), f, tkf, max_bredde=148)
            tegn_tekst(surf, pos_s,       (x0+180, ry+4), f, P.LYSBLÅ_UI)
            tegn_tekst(surf, str(ferd),   (x0+228, ry+4), f, P.GULT)
            tegn_kondisjon_bar(surf, x0+252, ry+8, 44, kond, skadet)

        # ── Benk (under startellevere) ────────────────────────────
        benk_y0 = y0 + 11 * rad_h + 8
        pygame.draw.rect(surf, P.BLÅL, (x0, benk_y0-2, 300, 16))
        tegn_tekst(surf, "── BENK ──", (x0+4, benk_y0), Fonter.liten, P.HVIT)
        benk_y0 += 18

        for j, s in enumerate(self.builder.benk):
            ry     = benk_y0 + j * (rad_h - 4)
            er_v   = (j == self._valgt_benk)
            farge  = P.BLÅLL if er_v else (P.GRÅ_MØRK if j % 2 == 0 else (48, 48, 48))
            pygame.draw.rect(surf, farge, (x0, ry, 300, rad_h-4))
            pos    = getattr(s, 'primær_posisjon', None)
            pos_s  = pos.name if pos else '?'
            ferd   = getattr(s, 'ferdighet', 0)
            navn   = f"{getattr(s, 'fornavn', '?')[0]}. {getattr(s, 'etternavn', '?')}"
            kond   = getattr(s, 'kondisjon', 100.0)
            skadet = getattr(s, 'skadet', False)

            tkf = P.NAVY if er_v else P.GRÅ_LYS
            tegn_tekst(surf, f"S{j+1}", (x0+2, ry+2), f, P.GRÅ_MØRK)
            tegn_tekst(surf, navn[:14], (x0+28, ry+2), f, tkf, max_bredde=148)
            tegn_tekst(surf, pos_s,     (x0+180, ry+2), f, P.LYSBLÅ_UI)
            tegn_tekst(surf, str(ferd), (x0+228, ry+2), f, P.GULT)
            tegn_kondisjon_bar(surf, x0+252, ry+6, 44, kond, skadet)

        # ── Høyre: formasjons-bane ────────────────────────────────
        bane_rect = (312, 28, 324, 300)
        tegn_formasjon_på_bane(surf, bane_rect, self.builder.startellever,
                                self.builder.formasjon_navn,
                                valgt_idx=self._valgt_start, font=Fonter.liten)

        # ── Formasjonsvelger ──────────────────────────────────────
        fv_y = 340
        pygame.draw.rect(surf, P.NAVY, (312, fv_y, 324, 32))
        pygame.draw.rect(surf, P.BLÅL, (312, fv_y, 324, 32), 2)
        tegn_tekst(surf, "◄", (316, fv_y+6), fb, P.GULT)
        t_f = Fonter.normal.render(self.builder.formasjon_navn, False, P.KREMHVIT)
        surf.blit(t_f, (312 + 164 - t_f.get_width()//2, fv_y+6))
        tegn_tekst(surf, "►", (612, fv_y+6), fb, P.GULT)

        # ── Ferdig-knapp ──────────────────────────────────────────
        tegn_knapp(surf, (312, H_BASE-28, 324, 24), "FERDIG / TILBAKE",
                   Fonter.normal,
                   hovered=ui.mus_innenfor((312*SKALA, (H_BASE-28)*SKALA,
                                            324*SKALA, 24*SKALA)))

        # ── Instruksjon ───────────────────────────────────────────
        _tegn_bunnlinje(surf, "KLIKK START→BENK FOR Å BYTTE  ◄► FORMASJON")

        # Marker bytte-modus
        if self._valgt_start >= 0 and self._valgt_benk >= 0:
            pygame.draw.rect(surf, P.GULT, (x0, 0, 300, 2))  # gul toppstripel

    def håndter_event(self, event, ui):
        from taktikk import TAKTIKK_KATALOG
        rad_h  = 26
        y0     = 28
        benk_y0 = y0 + 11 * rad_h + 8

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()

            # Formasjonspiler
            if 340 <= my <= 372:
                if 312 <= mx <= 340:  # Venstre pil
                    self._formasjon_idx = (self._formasjon_idx - 1) % len(self._TAKTIKK_LISTE)
                    self.builder.bytt_formasjon(self._TAKTIKK_LISTE[self._formasjon_idx])
                    self._valgt_start = -1; self._valgt_benk = -1
                    return
                if 610 <= mx <= 640:  # Høyre pil
                    self._formasjon_idx = (self._formasjon_idx + 1) % len(self._TAKTIKK_LISTE)
                    self.builder.bytt_formasjon(self._TAKTIKK_LISTE[self._formasjon_idx])
                    self._valgt_start = -1; self._valgt_benk = -1
                    return

            # Ferdig-knapp
            if my >= H_BASE-28 and 312 <= mx <= 636:
                self.on_ferdig()
                return

            # Klikk på startspiller
            if mx <= 304:
                for i in range(len(self.builder.startellever)):
                    ry = y0 + i * rad_h
                    if ry <= my < ry + rad_h:
                        if self._valgt_benk >= 0:
                            self.builder.bytt_spiller(i, self._valgt_benk)
                            self._valgt_start = -1; self._valgt_benk = -1
                        else:
                            if self._valgt_start == i:
                                if hasattr(self, 'on_spillerkort') and self.on_spillerkort:
                                    self.on_spillerkort(self.builder.startellever[i], self.builder.startellever, i)
                            else:
                                self._valgt_start = i
                        return

                # Klikk på benkespiller
                for j in range(len(self.builder.benk)):
                    ry = benk_y0 + j * (rad_h - 4)
                    if ry <= my < ry + rad_h-4:
                        if self._valgt_start >= 0:
                            self.builder.bytt_spiller(self._valgt_start, j)
                            self._valgt_start = -1; self._valgt_benk = -1
                        else:
                            if self._valgt_benk == j:
                                if hasattr(self, 'on_spillerkort') and self.on_spillerkort:
                                    self.on_spillerkort(self.builder.benk[j], self.builder.benk, j)
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
# SKJERM: SPILLERSTALL
# ─────────────────────────────────────────────────────────────────────────────
class SpillerstallSkjerm(SkjermData):
    def __init__(self, klubb, on_tilbake: Callable, on_spillerkort: Callable = None):
        self.klubb      = klubb
        self.on_tilbake = on_tilbake
        self.on_spillerkort = on_spillerkort
        self._scroll    = 0
        self._hover     = -1
        self._valgt     = -1
        self._alle_spillere = self._sorter_spillere()
        self._SYNLIGE   = 13

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

        manager_str = f"{len(self._alle_spillere)} SPILLERE"
        if hasattr(ui, 'manager_fornavn') and ui.manager_fornavn:
            manager_str = f"Mgr: {ui.manager_fornavn} {ui.manager_etternavn}"

        _tegn_topplinje(surf, "SPILLERSTALL", self.klubb.navn[:20], manager_str)

        # Kolonnehoder
        pygame.draw.rect(surf, P.BLÅL, (4, 26, W_BASE-8, 18))
        tegn_tekst(surf, "#",      (4,   28), f, P.HVIT)
        tegn_tekst(surf, "NAVN",   (24,  28), f, P.HVIT)
        tegn_tekst(surf, "POS",    (220, 28), f, P.HVIT)
        tegn_tekst(surf, "FERD",   (268, 28), f, P.HVIT)
        tegn_tekst(surf, "KOND",   (312, 28), f, P.HVIT)
        tegn_tekst(surf, "RYKTE",  (400, 28), f, P.HVIT)
        tegn_tekst(surf, "ALDER",  (480, 28), f, P.HVIT)
        tegn_tekst(surf, "KONTRAK",(550, 28), f, P.HVIT)

        # Spillerrader
        rad_h  = 26
        y0     = 48
        start  = self._scroll
        slutt  = min(start + self._SYNLIGE, len(self._alle_spillere))
        mx, my = ui.base_mus()

        for i, idx in enumerate(range(start, slutt)):
            s    = self._alle_spillere[idx]
            ry   = y0 + i * rad_h
            er_v = (idx == self._valgt)
            er_h = (4 <= mx <= W_BASE-16 and ry <= my < ry+rad_h)

            if er_v:
                pygame.draw.rect(surf, P.BLÅL, (4, ry, W_BASE-20, rad_h-2))
            elif er_h:
                pygame.draw.rect(surf, P.GRÅ_MØRK, (4, ry, W_BASE-20, rad_h-2))
            elif i % 2 == 0:
                pygame.draw.rect(surf, (34, 34, 48), (4, ry, W_BASE-20, rad_h-2))

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
            tegn_tekst(surf, str(idx+1),  (4,   ry+4), f, P.GRÅ_MØRK)
            tegn_tekst(surf, navn[:18],   (24,  ry+4), f, tkf, max_bredde=190)
            tegn_tekst(surf, pos_s,       (220, ry+4), f, P.LYSBLÅ_UI)
            tegn_badge(surf, str(ferd),   (264, ry+2),
                       P.GRØNN if ferd >= 14 else (P.BLÅL if ferd >= 10 else P.GRÅ_MØRK),
                       P.HVIT, f)
            if skadet:
                tegn_tekst(surf, "SKADET", (312, ry+4), f, P.RØD)
            else:
                tegn_kondisjon_bar(surf, 312, ry+8, 84, kond)
                tegn_tekst(surf, f"{kond:.0f}%", (400, ry+4), f,
                           P.GRØNN if kond >= 90 else (P.GULT if kond >= 75 else P.RØD))
            tegn_tekst(surf, str(rykte),  (480, ry+4), f, P.GULTL)
            tegn_tekst(surf, str(alder),  (520, ry+4), f, P.GRÅ_LYS)
            tegn_tekst(surf, kontr_s,     (556, ry+4), f, P.CYANL)

        # Scrollbar
        tegn_scrollbar(surf, W_BASE-10, y0, self._SYNLIGE*rad_h,
                        len(self._alle_spillere), self._SYNLIGE, self._scroll)

        # Tilbake-knapp
        tegn_knapp(surf, (W_BASE//2-70, H_BASE-26, 140, 22), "TILBAKE",
                   Fonter.normal,
                   hovered=ui.mus_innenfor(((W_BASE//2-70)*SKALA, (H_BASE-26)*SKALA,
                                             140*SKALA, 22*SKALA)))

        _tegn_bunnlinje(surf, "↑↓ SCROLL  ESC=TILBAKE")

    def håndter_event(self, event, ui):
        maks_scroll = max(0, len(self._alle_spillere) - self._SYNLIGE)

        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, min(maks_scroll, self._scroll - event.y))

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            rad_h, y0 = 26, 48
            for i in range(self._SYNLIGE):
                idx = self._scroll + i
                if idx >= len(self._alle_spillere):
                    break
                ry = y0 + i * rad_h
                if 4 <= mx <= W_BASE-16 and ry <= my < ry+rad_h:
                    if self._valgt == idx:
                        if hasattr(self, 'on_spillerkort') and self.on_spillerkort:
                            self.on_spillerkort(self._alle_spillere[idx], self._alle_spillere, idx)
                    else:
                        self._valgt = idx
            # Tilbake-knapp
            if (my >= (H_BASE-26) and
                    (W_BASE//2-70)*SKALA <= event.pos[0] <= (W_BASE//2+70)*SKALA):
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
    def __init__(self, tabeller: dict, aktiv_divisjon: str, spiller_klubb_navn: str, on_tilbake: Callable):
        self.tabeller = tabeller
        self.divisjoner = list(tabeller.keys())
        self._aktiv_div_idx = self.divisjoner.index(aktiv_divisjon) if aktiv_divisjon in self.divisjoner else 0
        self.spiller_klubb_navn = spiller_klubb_navn
        self.on_tilbake = on_tilbake
        self._fane = 0   # 0=tabell 1=toppscorere
        self._scroll = 0
        self._SYNLIGE = 16

    @property
    def aktiv_tabell(self):
        return self.tabeller[self.divisjoner[self._aktiv_div_idx]]

    def tegn(self, surf, ui):
        _tegn_bakgrunn(surf)
        f = Fonter.liten
        fb = Fonter.fet
        
        div_navn = self.divisjoner[self._aktiv_div_idx]
        _tegn_topplinje(surf, "SERIE", div_navn, "◄ PILER FOR DIVISJON ►")

        for fi, tekst in enumerate(["TABELL", "TOPPSCORERE"]):
            er_aktiv = fi == self._fane
            tegn_knapp(surf, (2 + fi*80, 13, 78, 10), tekst, f, valgt=er_aktiv)

        if self._fane == 0:
            self._tegn_tabell(surf, ui)
        else:
            self._tegn_toppscorere(surf, ui)

        tegn_knapp(surf, (W_BASE//2-30, H_BASE-13, 60, 11), "TILBAKE", Fonter.normal)
        _tegn_bunnlinje(surf, "TAB=FANE  ◄►=DIVISJON  ↑↓=SCROLL  ESC=TILBAKE")

    def _tegn_tabell(self, surf, ui):
        f = Fonter.liten
        rader = self.aktiv_tabell.sorter()

        pygame.draw.rect(surf, P.BLÅL, (2, 24, W_BASE-4, 10))
        titler = [("#", 2), ("KLUBB", 14), ("K", 142), ("S", 158), ("U", 172), ("T", 186), ("MF", 200), ("MM", 216), ("MD", 232), ("P", 252)]
        for t, x in titler:
            tegn_tekst(surf, t, (x, 26), f, P.HVIT)

        rad_h = 20
        y0 = 36
        start = self._scroll
        slutt = min(start + self._SYNLIGE, len(rader))

        for i, plass in enumerate(range(start, slutt)):
            rad = rader[plass]
            ry = y0 + i * rad_h
            er_min = (rad.klubb_navn == self.spiller_klubb_navn)
            farge_rad = P.BLÅL if er_min else ((34,34,48) if plass % 2 == 0 else (28,28,40))
            pygame.draw.rect(surf, farge_rad, (2, ry, W_BASE-9, rad_h-1))

            md = rad.mål_differanse
            md_s = f"+{md}" if md > 0 else str(md)
            tkf = P.GULT if er_min else P.KREMHVIT

            tegn_tekst(surf, str(plass+1), (2, ry+2), f, P.GRÅ_LYS)
            tegn_tekst(surf, rad.klubb_navn[:18], (14, ry+2), f, tkf, max_bredde=125)
            tegn_tekst(surf, str(rad.kamp), (142, ry+2), f, P.LYSBLÅ_UI)
            tegn_tekst(surf, str(rad.seier), (158, ry+2), f, P.GRØNN)
            tegn_tekst(surf, str(rad.uavgjort), (172, ry+2), f, P.GULT)
            tegn_tekst(surf, str(rad.tap), (186, ry+2), f, P.RØD)
            tegn_tekst(surf, str(rad.mål_for), (200, ry+2), f, P.KREMHVIT)
            tegn_tekst(surf, str(rad.mål_mot), (216, ry+2), f, P.KREMHVIT)
            tegn_tekst(surf, md_s, (232, ry+2), f, P.GRØNN if md > 0 else (P.RØD if md < 0 else P.GRÅ_LYS))
            tegn_badge(surf, str(rad.poeng), (252, ry+1), P.GULT if er_min else P.NAVY, P.NAVY if er_min else P.HVIT, f)

        tegn_scrollbar(surf, W_BASE-5, y0, self._SYNLIGE*rad_h, len(rader), self._SYNLIGE, self._scroll)

    def _tegn_toppscorere(self, surf, ui):
        # (Samme logikk som før, men bytt ut `self.tabell` med `self.aktiv_tabell`)
        f = Fonter.liten
        if not hasattr(self.aktiv_tabell, '_statistikk_register'):
            return
        
        pygame.draw.rect(surf, P.BLÅL, (2, 24, W_BASE-4, 8))
        titler = [("#", 2), ("SPILLER", 14), ("K", 158), ("MÅL", 174), ("RTG", 200)]
        for t, x in titler: tegn_tekst(surf, t, (x, 25), f, P.HVIT)

        topp = self.aktiv_tabell._statistikk_register.toppscorere(self._SYNLIGE)
        for i, stat in enumerate(topp):
            ry = 34 + i * 12
            farge_rad = (34,34,48) if i % 2 == 0 else (28,28,40)
            pygame.draw.rect(surf, farge_rad, (2, ry, W_BASE-4, 11))
            tegn_tekst(surf, str(i+1), (2, ry+2), f, P.GRÅ_LYS)
            tegn_tekst(surf, stat.spiller_navn[:20], (14, ry+2), f, P.KREMHVIT, max_bredde=140)
            tegn_tekst(surf, str(stat.kamper), (158, ry+2), f, P.LYSBLÅ_UI)
            tegn_badge(surf, str(stat.mål), (172, ry+1), P.GRØNN, P.HVIT, f)
            tegn_tekst(surf, f"{stat.snitt_rating:.1f}", (200, ry+2), f, P.GULT)

    def håndter_event(self, event, ui):
        maks_scroll = max(0, len(self.aktiv_tabell.sorter()) - self._SYNLIGE)
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
            # Fane-knapper: TABELL (x=2-80) og TOPPSCORERE (x=82-160) ved y=13-23
            for fi in range(2):
                bx = 2 + fi * 80
                if bx <= mx <= bx + 78 and 13 <= my <= 23:
                    self._fane = fi
                    self._scroll = 0
            # TILBAKE-knapp
            if W_BASE // 2 - 30 <= mx <= W_BASE // 2 + 30 and H_BASE - 13 <= my <= H_BASE - 2:
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
        pygame.draw.rect(surf, (10, 20, 60), (8, 26, W_BASE-16, 44))
        pygame.draw.rect(surf, P.BLÅLL, (8, 26, W_BASE-16, 44), 2)

        t_h  = Fonter.stor.render(r.hjemme_navn[:14], False, P.KREMHVIT)
        t_b  = Fonter.stor.render(r.borte_navn[:14],  False, P.KREMHVIT)
        score = f"{r.hjemme_maal}  –  {r.borte_maal}"
        if r.ekstraomganger:
            score += " e.o." if not r.straffer else " str."
        t_s  = Fonter.tittel.render(score, False, P.GULT)

        surf.blit(t_h, (12, 36))
        surf.blit(t_b, (W_BASE - t_b.get_width() - 12, 36))
        surf.blit(t_s, (W_BASE//2 - t_s.get_width()//2, 32))

        # Faner
        fane_navn = ["HENDELSER", "STATISTIKK", "SPILLERBØRS"]
        for fi, navn in enumerate(fane_navn):
            er_aktiv = fi == self._fane
            tegn_knapp(surf, (4 + fi*212, 74, 208, 18), navn, f,
                        valgt=er_aktiv,
                        hovered=(not er_aktiv and
                                 ui.mus_innenfor(((4+fi*212)*SKALA, 74*SKALA,
                                                   208*SKALA, 18*SKALA))))

        innhold_y = 96
        innhold_h = H_BASE - innhold_y - 28

        if self._fane == 0:
            self._tegn_hendelser(surf, innhold_y, innhold_h)
        elif self._fane == 1:
            self._tegn_statistikk(surf, innhold_y, innhold_h)
        else:
            self._tegn_bors(surf, innhold_y, innhold_h)

        tegn_knapp(surf, (W_BASE//2-70, H_BASE-26, 140, 22), "FORTSETT",
                   Fonter.normal,
                   hovered=ui.mus_innenfor(((W_BASE//2-70)*SKALA, (H_BASE-26)*SKALA,
                                             140*SKALA, 22*SKALA)))
        _tegn_bunnlinje(surf, "TAB=FANE  ENTER=FORTSETT")

    def _tegn_hendelser(self, surf, y0, h):
        f = Fonter.liten
        hendelser = sorted(self.resultat.hendelser, key=lambda x: x.minutt)
        synlige   = h // 20
        start     = self._scroll
        ikon_map  = {"mål": "⚽", "gult_kort": "🟨", "rødt_kort": "🟥",
                     "skade": "🚑", "bytte": "🔄"}

        for i, hend in enumerate(hendelser[start:start+synlige]):
            ry  = y0 + i * 20
            farge = (P.GULT if hend.type == "mål" else
                     P.GRÅ_LYS if hend.type == "bytte" else P.KREMHVIT)
            lag_s = "H" if hend.lag == "hjemme" else "B"
            navn  = getattr(hend.spiller, 'etternavn', '?')
            detalj = f" ({hend.detalj})" if hend.detalj else ""
            tegn_tekst(surf, f"{hend.minutt:>3}'  [{lag_s}]  {navn[:16]}{detalj[:20]}",
                       (8, ry), f, farge)

        if not hendelser:
            tegn_tekst(surf, "Ingen hendelser registrert.", (8, y0+20), f, P.GRÅ_MØRK)

        tegn_scrollbar(surf, W_BASE-12, y0, h, len(hendelser), synlige, self._scroll)

    def _tegn_statistikk(self, surf, y0, h):
        f  = Fonter.liten
        fb = Fonter.fet
        s  = self.resultat.statistikk
        r  = self.resultat
        bes_h, bes_b = s.ballbesittelse

        def rad(label, v_h, v_b, ry, farge_v=P.KREMHVIT):
            midtre = W_BASE // 2
            pygame.draw.rect(surf, (28,28,44), (8, ry, W_BASE-16, 18))
            tegn_tekst(surf, str(v_h), (midtre-80, ry+2), f, P.LYSBLÅ_UI)
            tegn_tekst(surf, label,    (midtre - Fonter.liten.size(label)[0]//2, ry+2),
                        f, P.GRÅ_LYS)
            tegn_tekst(surf, str(v_b), (midtre+60, ry+2), f, P.LYSBLÅ_UI)

        rad("Ballbesittelse",  f"{bes_h}%",  f"{bes_b}%",  y0+4)
        rad("Sjanser",         s.sjanser_hjemme,    s.sjanser_borte,    y0+26)
        rad("Skudd",           s.skudd_hjemme,      s.skudd_borte,      y0+48)
        rad("Skudd på mål",    s.skudd_paa_maal_hjemme, s.skudd_paa_maal_borte, y0+70)
        rad("Gule kort",       s.gule_kort_hjemme,  s.gule_kort_borte,  y0+92)
        rad("Røde kort",       s.røde_kort_hjemme,  s.røde_kort_borte,  y0+114)

        # Navnlinje
        pygame.draw.rect(surf, P.BLÅL, (8, y0+140, W_BASE-16, 16))
        t_h = Fonter.liten.render(r.hjemme_navn[:14], False, P.HVIT)
        t_b = Fonter.liten.render(r.borte_navn[:14],  False, P.HVIT)
        surf.blit(t_h, (12, y0+142))
        surf.blit(t_b, (W_BASE - t_b.get_width() - 12, y0+142))

    def _tegn_bors(self, surf, y0, h):
        f  = Fonter.liten
        alle = ([(s, True) for s in self.hjemme_spillere] +
                [(s, False) for s in self.borte_spillere])
        synlige = h // 20
        start   = self._scroll

        pygame.draw.rect(surf, P.BLÅL, (4, y0, W_BASE-8, 16))
        tegn_tekst(surf, "SPILLER",  (8,  y0+2), f, P.HVIT)
        tegn_tekst(surf, "LAG",      (300, y0+2), f, P.HVIT)
        tegn_tekst(surf, "RATING",   (380, y0+2), f, P.HVIT)

        for i, (s, er_hjemme) in enumerate(alle[start:start+synlige]):
            ry     = y0 + 18 + i * 20
            rating = self.resultat.statistikk.hent_rating(s)
            navn   = f"{getattr(s, 'fornavn','?')[0]}. {getattr(s,'etternavn','?')}"
            lag    = self.resultat.hjemme_navn[:6] if er_hjemme else self.resultat.borte_navn[:6]

            farge_rad = (34,34,48) if i%2==0 else (28,28,40)
            pygame.draw.rect(surf, farge_rad, (4, ry, W_BASE-8, 18))

            rtg_farge = (P.GRØNN if rating >= 7.5 else
                         P.GULT  if rating >= 6.5 else
                         P.RØD   if rating < 5.5 else P.GRÅ_LYS)

            tegn_tekst(surf, navn[:20], (8,  ry+2), f, P.KREMHVIT)
            tegn_tekst(surf, lag,       (300,ry+2), f, P.LYSBLÅ_UI)
            tegn_badge(surf, f"{rating:.1f}", (380, ry+2), rtg_farge, P.SVART, f)

        tegn_scrollbar(surf, W_BASE-12, y0+18, h-18, len(alle), synlige, self._scroll)

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
                if 4+fi*212 <= mx <= 212+fi*212 and 74 <= my <= 92:
                    self._fane  = fi
                    self._scroll = 0
                    return
            if my >= H_BASE-26:
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
        pygame.draw.rect(surf, (10, 18, 50, 200), (20, 40, W_BASE-40, 60))
        pygame.draw.rect(surf, P.BLÅLL, (20, 40, W_BASE-40, 60), 4)
        t = fb.render(self.tittel_tekst, False, P.GULT)
        surf.blit(t, (W_BASE//2 - t.get_width()//2, 54))

        # Linjer
        for i, linje in enumerate(self.linjer[:10]):
            tegn_tekst(surf, linje, (28, 120 + i*24), f, P.KREMHVIT)

        tegn_knapp(surf, (W_BASE//2-80, H_BASE-40, 160, 28), "FORTSETT →",
                   Fonter.normal,
                   hovered=ui.mus_innenfor(((W_BASE//2-80)*SKALA, (H_BASE-40)*SKALA,
                                             160*SKALA, 28*SKALA)))
        _tegn_bunnlinje(surf, "ENTER / KLIKK FOR Å FORTSETTE")

    def håndter_event(self, event, ui):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.on_ferdig()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            if H_BASE-40 <= my <= H_BASE-12 and W_BASE//2-80 <= mx <= W_BASE//2+80:
                self.on_ferdig()



# ─────────────────────────────────────────────────────────────────────────────
# SKJERM: SPILLERKORT
# ─────────────────────────────────────────────────────────────────────────────
class SpillerkortSkjerm(SkjermData):
    """
    Fullskjerm spillerkort for én spiller. Vises når man klikker
    på en spiller i SpillerstallSkjerm eller LaguttakSkjerm.
    """
    def __init__(self, spiller, spiller_liste: list, start_idx: int,
                 stat_register, on_tilbake: Callable, on_forrige: Callable=None, on_neste: Callable=None):
        self.spiller_liste = spiller_liste
        self.idx = start_idx
        self.stat_register = stat_register
        self.on_tilbake = on_tilbake
        self.on_forrige = on_forrige
        self.on_neste = on_neste
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
                if self.on_forrige: self.on_forrige()
            elif event.key == pygame.K_RIGHT:
                if self.on_neste: self.on_neste()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            if H_BASE-34 <= my <= H_BASE-10:
                if 20 <= mx <= 120:
                    if self.on_forrige: self.on_forrige()
                elif W_BASE//2-50 <= mx <= W_BASE//2+50:
                    self.on_tilbake()
                elif W_BASE-120 <= mx <= W_BASE-20:
                    if self.on_neste: self.on_neste()

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
            ry = 36 + i * 24
            farge_rad = (34,34,48) if i % 2 == 0 else (28,28,44)
            pygame.draw.rect(surf, farge_rad, (8, ry, W_BASE-16, 22))
            score = f"{hm} – {bm}"
            tegn_tekst(surf, h[:16],   (12,   ry+4), f, P.KREMHVIT)
            tegn_tekst(surf, score,    (W_BASE//2 - 24, ry+4), fb, P.GULT)
            t_b = f.render(b[:16], False, P.KREMHVIT)
            surf.blit(t_b, (W_BASE - t_b.get_width() - 12, ry+4))

        tegn_knapp(surf, (W_BASE//2-60, H_BASE-28, 120, 24), "OK →",
                   Fonter.normal,
                   hovered=ui.mus_innenfor(((W_BASE//2-60)*SKALA, (H_BASE-28)*SKALA,
                                             120*SKALA, 24*SKALA)))
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
        surf.blit(t1, (W_BASE//2 - t1.get_width()//2, 28))
        pygame.draw.rect(surf, P.BLÅL, (0, 60, W_BASE, 2))

        hist    = self.resultater
        seiere  = hist.count("S")
        uavgjort= hist.count("U")
        tap     = hist.count("T")
        poeng   = seiere*3 + uavgjort


        manager_str = ""
        if hasattr(ui, 'manager_fornavn') and ui.manager_fornavn:
            manager_str = f"Manager: {ui.manager_fornavn} {ui.manager_etternavn}"

        tegn_tekst(surf, self.klubb_navn, (16, 72), f, P.KREMHVIT)
        if manager_str:
            tegn_tekst(surf, manager_str, (16, 88), f, P.LYSBLÅ_UI)

        stats = [
            ("Kamper spilt:",  str(len(hist))),
            ("Seiere:",        str(seiere)),
            ("Uavgjort:",      str(uavgjort)),
            ("Tap:",           str(tap)),
            ("Poeng:",         str(poeng)),
        ]
        for i, (label, verdi) in enumerate(stats):
            ry = 100 + i*24
            tegn_tekst(surf, label, (16, ry), fs, P.GRÅ_LYS)
            tegn_tekst(surf, verdi, (260, ry), f, P.GULT)

        # Tabellplassering
        if self.tabell:
            plass = self.tabell.plass(self.klubb_navn)
            pygame.draw.rect(surf, (10, 18, 50), (8, 236, W_BASE-16, 32))
            tegn_tekst(surf, f"ENDELIG TABELLPLASS: {plass}. PLASS",
                        (16, 244), f, P.CYANL)

        tegn_knapp(surf, (W_BASE//2-80, H_BASE-40, 160, 28), "AVSLUTT",
                   Fonter.normal,
                   hovered=ui.mus_innenfor(((W_BASE//2-80)*SKALA, (H_BASE-40)*SKALA,
                                             160*SKALA, 28*SKALA)))

    def håndter_event(self, event, ui):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self.on_avslutt()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = ui.base_mus()
            if H_BASE-40 <= my <= H_BASE-12:
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
        self._pauset: bool = False
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
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                self._pauset = not self._pauset

            if self._stack:
                self._stack[-1].håndter_event(event, self)

        # Tegn øverste skjerm
        self._base.fill(P.GRÅ_PANEL)
        if self._stack:
            self._stack[-1].tegn(self._base, self)
            if self._pauset and hasattr(self._stack[-1], '__class__'):
                _tegn_topplinje(self._base, "", "PAUSET", "PAUSET", is_pauset=True)

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
