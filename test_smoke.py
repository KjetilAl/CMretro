import database
from spillmotor_pygame import SpillmotorPygame
import datetime
from ui_pygame import Fonter
import pygame

# Initialize pygame and mock out UIMotor methods to avoid blocking
pygame.init()
Fonter.init()

motor = SpillmotorPygame()

# Fast load
motor.klubber = database.last_database(sesong_aar=2025, verbose=False)

# Setup club
motor.spiller_klubb = motor.klubber['bodoglimt']
motor.manager_fornavn = "Nils"
motor.manager_etternavn = "Arne"

motor._bygg_liga_og_kalender()

# Check that tabeller has multiple keys
print(f"Tabeller opprettet for: {list(motor._tabeller.keys())}")
assert len(motor._tabeller) >= 4, "Mangler divisjonstabeller"

# Check varied OVR
spillere = motor.spiller_klubb.spillerstall
ovr_list = [s.ferdighet for s in spillere]
assert len(set(ovr_list)) > 1, f"Alle spillere har samme OVR: {ovr_list}"
print(f"OVR variasjon funnet: {set(ovr_list)}")

print("Test ok!")
