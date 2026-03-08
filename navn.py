"""
navn.py  –  Norsk Football Manager '95
Navnebank for spillergenerering.
Alle navn er typiske norske/skandinaviske fra 1990-tallet.
"""

from __future__ import annotations
import random

# ── Fornavn ───────────────────────────────────────────────────────────────────

FORNAVN_NORSK = [
    # Vanlige norske mannsnavn fra 90-tallet
    "Anders", "Andreas", "Bjørn", "Christian", "Daniel",
    "Erik", "Espen", "Fredrik", "Geir", "Gunnar",
    "Håkon", "Henrik", "Jan", "Joakim", "Johan",
    "Jon", "Jonas", "Kenneth", "Kim", "Kjell",
    "Kjetil", "Kristian", "Lars", "Leif", "Magne",
    "Magnus", "Marius", "Martin", "Morten", "Nils",
    "Odd", "Ole", "Ørjan", "Pål", "Per",
    "Rune", "Sigurd", "Simen", "Stian", "Svein",
    "Thomas", "Thor", "Tobias", "Tom", "Tommy",
    "Tor", "Trond", "Vegard", "Vidar", "Øyvind",
    "Arild", "Arvid", "Asbjørn", "Audun", "Eirik",
    "Frode", "Geir Arne", "Helge", "Henning", "Ivar",
    "Jens", "Karl", "Knut", "Kolbjørn", "Lasse",
    "Mattias", "Mads", "Mikael", "Nikolai", "Olaf",
    "Petter", "Ragnar", "Roger", "Roar", "Robert",
    "Robin", "Roy", "Ruben", "Sindre", "Stig",
    "Sturla", "Tarjei", "Terje", "Tore", "Torstein",
    "Truls", "Ulf", "Vidar", "Yngve", "Øyvind",
]

# Noen innvandrerbakgrunner som representerte norsk fotball på 90-tallet
FORNAVN_INTERNASJONAL = [
    "Abdisalam", "Attila", "Babacar", "Carlos", "Cheikh",
    "Daouda", "Ernest", "Frode", "Ibrahim", "Jürgen",
    "Karel", "Lamine", "Marcel", "Moussa", "Ndiaye",
    "Pavel", "Rachid", "Said", "Steffen", "Tore Andre",
    "Uwe", "Vladimir", "Wasiu", "Xavier", "Yaw",
]

ALLE_FORNAVN = FORNAVN_NORSK + FORNAVN_INTERNASJONAL


# ── Etternavn ─────────────────────────────────────────────────────────────────

ETTERNAVN_NORSK = [
    # -sen / -son
    "Andersen", "Carlsen", "Christensen", "Dahl", "Eide",
    "Eriksen", "Fossen", "Gjerde", "Halvorsen", "Hansen",
    "Haugen", "Henriksen", "Iversen", "Jacobsen", "Jensen",
    "Johansen", "Johnsen", "Karlsen", "Larsen", "Lie",
    "Lund", "Martinsen", "Moen", "Myhre", "Mæland",
    "Nygård", "Nygaard", "Nilsen", "Olsen", "Pedersen",
    "Pettersen", "Rasmussen", "Rønning", "Svendsen", "Sørensen",
    "Thomsen", "Thorsen", "Wilhelmsen",
    # Stedsnavn-etternavn
    "Almås", "Berg", "Berge", "Bakke", "Bø", "Dal",
    "Dalen", "Eid", "Fjeld", "Hagen", "Haug",
    "Holm", "Holt", "Ås", "Aas", "Ask",
    "Brekke", "Buvik", "Bye", "Dale", "Elven",
    "Fjeldheim", "Foss", "Grønn", "Grønvold", "Haugland",
    "Hegge", "Heitmann", "Helstad", "Hjelmbrekke", "Hofstad",
    "Huseklepp", "Høiland", "Jakobsen", "Koppinen", "Larssen",
    "Lindqvist", "Linge", "Listhaug", "Løchen", "Møller",
    "Nordli", "Norheim", "Noss", "Nyland", "Næss",
    "Oftedal", "Ogbu", "Orry", "Riseth", "Ro",
    "Rushfeldt", "Sand", "Skjeldal", "Skjelbred", "Skogen",
    "Solbakken", "Solli", "Soltvedt", "Stadheim", "Strand",
    "Stranden", "Sæther", "Søgaard", "Sørloth", "Tangen",
    "Taranger", "Tjelmeland", "Tjønn", "Tjøtta", "Toppmoedig",
    "Tunsberg", "Ulriksen", "Utvik", "Vaagan", "Varela",
    "Viken", "Vikestad", "Vik", "Vold", "Wangberg",
    "Wiig", "Wold", "Woldseth", "Wormdal",
    # Kjente norske fotballnavn-inspirerte (ikke ekte, men troverdige)
    "Aursnes", "Bjørnbak", "Bjørnstad", "Brenne", "Eikrem",
    "Elabdellaoui", "Flo", "Forren", "Gabrielsen", "Hestad",
    "Hussain", "Iversen", "Knudtzon", "Moldskred", "Mostrom",
    "Riseth", "Storflor", "Strandberg", "Tagseth", "Ødegaard",
]

ETTERNAVN_INTERNASJONAL = [
    "Boateng", "Diallo", "Diouf", "Dembélé", "García",
    "Gomez", "Kovač", "Müller", "N'Doye", "Nkosi",
    "Okonkwo", "Petit", "Sörensen", "Šilhavý", "Touré",
    "Traoré", "Varga", "Xhaka", "Yıldız", "Zidane",
]

ALLE_ETTERNAVN = ETTERNAVN_NORSK + ETTERNAVN_INTERNASJONAL


# ── Navngenerator ─────────────────────────────────────────────────────────────

class Navngenerator:
    """
    Trekker unike for- og etternavn fra bankene.
    Holder styr på brukte kombinasjoner slik at ingen to spillere
    i samme simuleringsøkt får identisk fullt navn.
    """

    def __init__(
        self,
        fornavn_bank: list[str] = ALLE_FORNAVN,
        etternavn_bank: list[str] = ALLE_ETTERNAVN,
    ) -> None:
        self._fornavn   = list(fornavn_bank)
        self._etternavn = list(etternavn_bank)
        self._brukte:   set[str] = set()

        # Bland bankene én gang ved oppstart
        random.shuffle(self._fornavn)
        random.shuffle(self._etternavn)

        # Roterende teller
        self._teller = 0

    def neste(self) -> tuple[str, str]:
        """
        Returnerer (fornavn, etternavn) — garantert unikt fullt navn.
        Bruker tilfeldig trekk med kollisjonshåndtering.
        """
        for _ in range(500):
            f = random.choice(self._fornavn)
            e = random.choice(self._etternavn)
            fullt = f"{f} {e}"
            if fullt not in self._brukte:
                self._brukte.add(fullt)
                return f, e

        # Nødutgang ved ekstremt mange spillere
        suffix = len(self._brukte)
        f = random.choice(self._fornavn)
        e = random.choice(self._etternavn)
        return f, f"{e} {suffix}"

    def reset(self) -> None:
        """Tøm brukte-settet (ny sesong / ny database)."""
        self._brukte.clear()
        self._teller = 0
        random.shuffle(self._fornavn)
        random.shuffle(self._etternavn)


# Global singleton — brukes av lag_spiller() og database-generatoren
_generator = Navngenerator()


def trekk_navn() -> tuple[str, str]:
    """Trekker ett unikt (fornavn, etternavn)-par fra den globale generatoren."""
    return _generator.neste()


def reset_navngenerator() -> None:
    """Nullstill for ny sesong eller test."""
    _generator.reset()
