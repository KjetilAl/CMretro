import database
from taktikk import Posisjon, POSISJON_GRUPPE

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

# we can fill attributes using the person.py logic, or modify `_fyll_inn_nullverdier` to fill in `_FERDIGHET_ATTRS`.
# Wait, let's see what `_generer_attributter_for_posisjon` does in database.py
# It is used for generated players.
