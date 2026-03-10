import database
from person import Person

klubber = database.last_database(verbose=False)
molde = klubber["molde"]
print(f"Historisk styrke for Molde: {molde.historisk_styrke}")
for s in molde.spillerstall[:2]:
    print(vars(s))
