# Endringslogg

Dette dokumentet beskriver endringene som er gjort for å løse FEIL 1–6 i Norsk Football Manager '95.

## `ui_pygame.py`
* **Oppløsning (Feil 1):** Endret `W_BASE` og `H_BASE` fra 320x200 til 640x400 og justerte `SKALA` til 2. Økte alle standard fonter via `Fonter.init()` med ca. 50%.
* **GUI-skalering (Feil 1):** Gikk gjennom samtlige skjermklasser (`HovedmenySkjerm`, `VelgKlubbSkjerm`, `KampdagSkjerm`, `LaguttakSkjerm`, `SpillerstallSkjerm`, `TabellSkjerm`, `KamprapportSkjerm`, `InfoSkjerm`, `AndreResultaterSkjerm` og `SesongsSluttSkjerm`) og multipliserte alle hardkodede koordinater, bredder, og høyder med 2 for å tilpasses det nye 640x400 lerretet.
* **Divisjonsvisning (Feil 2):** Lagt til visning av separator-rader i `VelgKlubbSkjerm` (grå farge, ikke-klikkbare). Oppdaterte `TabellSkjerm` til å ta imot en dictionary med tabeller og vise dynamiske faner for hver av dem.
* **Ny Manager (Feil 3):** Implementerte den nye skjermen `OpprettManagerSkjerm` hvor brukeren kan taste inn fornavn og etternavn. Inkluderte visning av manager-navnet i toppbannere og på sesongslutt-skjermen.
* **Spillerkort (Feil 6):** Lagt til skjermen `SpillerkortSkjerm` for detaljert visning av spilleren (pixel-portrett, statistikk, stolpediagrammer for ferdigheter). Integrerte hendelseshåndtering for dobbeltklikk/ekstraklikk i `SpillerstallSkjerm` og `LaguttakSkjerm`.

## `spillmotor_pygame.py`
* **Klubb-valg fra alle divisjoner (Feil 2):** Modifiserte listebyggingen i `_lag_velg_klubb_skjerm` for å inkludere lag fra samtlige divisjoner. Lagene sorteres per divisjon og deretter historisk styrke, separert av divisjonsnavnet.
* **Flere tabeller (Feil 2):** Oppdaterte `_bygg_liga_og_kalender` til å opprette unike `Seriatabell`-objekter (nå referert til som en dictionary) for alle divisjoner som er i bruk. Modifiserte metoden `_vis_tabell` for å sende dictionaryen til GUI-et, og oppdaterte tabelloppdateringsrutinene i `_spill_kamp`.
* **Managerdata (Feil 3):** Implementerte lagring av managernavn (`self.manager_fornavn` og `self.manager_etternavn`) i startsekvensen før kalenderbygging.
* **AI-Simulering (Feil 4):** La til og kalte funksjonen `_simuler_alle_andre_kamper(dag)` FØR spillkamper blir vist. Dette sikrer at kalenderens uspilte kamper mellom datastyrte lag spilles med resultat og tabelloppdatering til følge.
* **Spillerkort Visning (Feil 6):** Implementerte metoden `_vis_spillerkort` som danner koblingen mellom interaksjon i GUI og instantiering av selve kortet.

## `database.py`
* **Realistisk Generering (Feil 5):** Skrev om logikken under `_generer_spiller` til å kalle på `person.lag_spiller`. Her settes nå et dynamisk `ovr_mål` basert på divisjon (Eliteserien 11–17, OBOS 9–14, Div 2 7–11, etc.) og lagets interne historiske styrke. Brukte variasjon 2-3.
* **Eksisterende Spillere (Feil 5):** Oppdaterte `_fyll_inn_nullverdier` slik at de eksisterende spillerne i databasen får populert sine 14 manglende tekniske ferdigheter, sentrert rundt deres tildelte OVR-ferdighet. `_bygg_person` er oppdatert for å pakke ut og tildele attributtene. Dette fjerner 10-sperren i hele stallen.
