import database
import person

klubber = database.last_database(verbose=False)

molde = klubber["molde"]
for s in molde.spillerstall[:2]:
    print(f"{s.fullt_navn} (OVR: {s.ferdighet})")
    print(f"Skudd: {s.skudd}, Pasning: {s.pasning}, Fart: {s.fart}")
