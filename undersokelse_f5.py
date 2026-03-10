import database
from person import Person

# Inspect if _fyll_inn_nullverdier actually populates ferdighets-attributtene
# based on `ferdighet`.
d = {
    "id": "haikin_nikita",
    "fornavn": "Nikita",
    "etternavn": "Haikin",
    "alder": 28,
    "lag_id": "bodoglimt",
    "primær_posisjon": "K",
    "sekundær_posisjon": None,
    "ferdighet": 17,
    "utholdenhet": 14,
    "lojalitet": 0,
    "egoisme": 0,
    "presstoleranse": 0,
    "arbeidsvilje": 0
}

fylt = database._fyll_inn_nullverdier(d, 18)
print("Etter _fyll_inn_nullverdier:")
print(fylt)
