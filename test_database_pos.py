import database

klubber = database.last_database(verbose=False)
for k_id, k in klubber.items():
    print(f"{k.navn}: {len(k.spillerstall)} spillere")
    for s in k.spillerstall[:2]:
        print(f"  {s.fullt_navn} - {s.primær_posisjon}")
