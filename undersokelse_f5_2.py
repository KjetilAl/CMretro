import database

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

# The problem is that database._fyll_inn_nullverdier does NOT generate the technical attributes!
# So all 14 technical skills are completely missing from the dict, and when built via `fra_dict` or `_bygg_person`, they get the default value (10).

print("Test run")
