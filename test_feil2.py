import spillmotor_pygame
import ui_pygame
from ui_pygame import Fonter

# Test at instansiering av TabellSkjerm fungerer
import pygame
pygame.init()
Fonter.init()

class DummyTabell:
    def __init__(self, div):
        self.divisjon = div

    def sorter(self):
        return []
    def hent_rad(self, navn):
        return None

tabeller = {
    "Eliteserien": DummyTabell("Eliteserien"),
    "OBOS-ligaen": DummyTabell("OBOS-ligaen"),
}
s = ui_pygame.TabellSkjerm(tabeller, "Mitt lag", lambda: None)
surf = pygame.Surface((640, 400))
ui_mock = ui_pygame.UIMotor()

s.tegn(surf, ui_mock)
print("TabellSkjerm tegnet uten problemer")

from database import Klubb
class DummyKlubb:
    def __init__(self, navn, styrke):
        self.navn = navn
        self.historisk_styrke = styrke
        self.stadion = None

klubber = ["Eliteserien", DummyKlubb("Lag A", 10), "OBOS-ligaen", DummyKlubb("Lag B", 8)]
s2 = ui_pygame.VelgKlubbSkjerm(klubber, lambda x: None)
s2.tegn(surf, ui_mock)
print("VelgKlubbSkjerm tegnet uten problemer")
