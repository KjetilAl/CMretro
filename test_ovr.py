from person import Person, Posisjon, lag_spiller

spiller1 = lag_spiller("id1", Posisjon.SP, ovr_mål=15)
print(f"OVR for spiller 1 (mål: 15): {spiller1.ferdighet}")
