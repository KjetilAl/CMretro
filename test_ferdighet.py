import database

klubber = database.last_database(verbose=False)
molde = klubber["molde"]
for s in molde.spillerstall[:5]:
    print(f"Navn: {s.fullt_navn}, Pos: {s.primær_posisjon}, OVR: {s.ferdighet}")
    print(f"Skudd: {s.skudd}, Pasning: {s.pasning}, OVR fra formel: {s._beregn_ovr(s.primær_posisjon)}")
