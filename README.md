# Norsk Football Manager '95

## Installasjon
pip install pygame

## Kjøring
python spillmotor_pygame.py

## Arkitektur
En enkel tekstlig dataflyt-oversikt:
SpillKalender → simuler_neste_dag() → dag.kamper
dag.kamper → KampMotor.spill_kamp() → KampResultat
KampResultat → Seriatabell.registrer_resultat()
KampResultat → HendelsesManager.registrer_kampresultat()
KampResultat → SpillerkortSkjerm / KamprapportSkjerm (via UIMotor)

## Filstruktur
- **cup.py**: Håndterer cupsystem og cuptrekninger.
- **database.py**: Laster spillere og klubber fra fil og genererer ny database.
- **europa.py**: Modul for europeisk spill.
- **hendelser.py**: Genererer hendelser, nyheter og skjult statistikk.
- **kalender.py**: Holder rede på kampdatoer og hendelser over året.
- **kampmotor.py**: Kjerne for fotballsimulering og kamplogikk.
- **klubb.py**: Dataklasser for fotballklubber og stadioner.
- **liga.py**: Bygger seriesystemet, avdelinger og ligastruktur.
- **navn.py**: Tilfeldige norske navn generator.
- **nyhetsgenerator.py**: Lager tekstlige nyheter om kamper og hendelser.
- **okonomi.py**: AIManager, SpillerMarked og økonomiregler.
- **person.py**: Spiller, attributter og markedsverdi.
- **spillmotor_pygame.py**: Koordinator for game-loop og Pygame-visning.
- **tabell.py**: Tabellhåndtering og statistikk-register.
- **taktikk.py**: Taktikkkatalog og oppstillinger for lag.
- **ui_pygame.py**: Frontend Pygame moduler for menyer og GUI-skjermer.

## Kjente begrensninger
Overgangs-UI, lagring/lasting ikke implementert ennå
