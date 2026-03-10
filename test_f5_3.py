from person import _FERDIGHET_ATTRS
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

# The person.py has a factory lag_spiller that generates ferdigheter around an OVR goal, but database.py _fyll_inn_nullverdier does NOT do this for players coming from spillere.json.
# Wait, let's look at `_generer_attributter_for_posisjon(gruppe, base_styrke)` in database.py
# It takes gruppe and base_styrke. We have `ferdighet` in the player dictionary!
