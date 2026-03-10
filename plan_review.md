# Plan Review Request

The issue has 6 bugs to fix.

## FEIL 1 — Oppløsning er for lav
*   **File**: `ui_pygame.py`
*   **Action**: Change `W_BASE, H_BASE` to `640, 400` and `SKALA` to `2`.
*   **Action**: Multiply all x, y, width, height constants by 2 in `ui_pygame.py` for all coordinates and rect definitions in `HovedmenySkjerm`, `VelgKlubbSkjerm`, `KampdagSkjerm`, `LaguttakSkjerm`, `SpillerstallSkjerm`, `TabellSkjerm`, `KamprapportSkjerm`, and `InfoSkjerm`. Leave `FORMASJON_KOORDINATER` alone.
*   **Action**: Increase all font sizes by ~50% in `Fonter.init()`: `liten=13, normal=15, fet=15 (bold), stor=20, tittel=26`. Double `max_bredde` values in `tegn_tekst` calls.
*   **Verification**: Run a quick test script to import the file.

## FEIL 2 — Kan bare velge Eliteserien-lag
*   **File**: `spillmotor_pygame.py` & `ui_pygame.py`
*   **Action**: In `_lag_velg_klubb_skjerm`, group and sort all clubs by `DIVISJON_REKKEFØLGE = {'Eliteserien': 0, 'OBOS-ligaen': 1, 'Div 2': 2, 'Div 3': 3}`. Return a flat list with string separators for each division. Handle the separator in `VelgKlubbSkjerm` (draw gray, not clickable).
*   **Action**: In `_bygg_liga_og_kalender`, create `Seriatabell` objects (which I have confirmed exists in `tabell.py` as `class Seriatabell:`) for ALL divisions present in the clubs, storing them in a dict `self._tabeller`.
*   **Action**: In `_vis_tabell()`, change `TabellSkjerm` to accept the dict of tables and the current division, and show a tab for each division.
*   **Verification**: Run a test script to check `_bygg_liga_og_kalender`.

## FEIL 3 — Ingen manageroppretting ved oppstart
*   **File**: `ui_pygame.py` & `spillmotor_pygame.py`
*   **Action**: Create `OpprettManagerSkjerm(SkjermData)` in `ui_pygame.py` matching the description (two text fields, CM95 style).
*   **Action**: In `spillmotor_pygame.py`, add `self.manager_fornavn = ""` and `self.manager_etternavn = ""` in `__init__`.
*   **Action**: Before calling `_bygg_liga_og_kalender()`, show `OpprettManagerSkjerm` modally and save names.
*   **Action**: Update `_tegn_topplinje` calls or `SesongsSluttSkjerm` to show the manager's name.
*   **Verification**: Run a test script to import and instantiate the screen.

## FEIL 4 — Andre lags kamper simuleres ikke
*   **File**: `spillmotor_pygame.py`
*   **Action**: Add `_simuler_alle_andre_kamper(self, dag)` method. Call it in `_vis_hendelsesdag(self, dag, dato)` BEFORE checking `mine_kamper`.
*   **Verification**: Run `python -c "import spillmotor_pygame"`.

## FEIL 5 — Alle spillere viser samme "ferdighet"
*   **File**: `database.py`
*   **Action**: In the `_generer_spiller` function (confirmed via `grep` on line 125 of `database.py`), replace its attribute generation logic with a call to `person.lag_spiller()`. Calculate `ovr_mål` dynamically based on `historisk_styrke` and `divisjon` (Eliteserien: 11-17, OBOS-ligaen: 9-14, Div 2: 7-11, Div 3: 5-9) with `variasjon=2` or `3`.
*   **Action**: In `_fyll_inn_nullverdier` (confirmed via `grep` on line 228 of `database.py`), populate the technical attributes by using `_generer_attributter_for_posisjon(gruppe, base_styrke=spiller_dict.get('ferdighet') or styrke_calculated)`.
*   **Verification**: Run a script to load the database and inspect the generated and filled player attributes.

## FEIL 6 — Spillerkort mangler
*   **File**: `ui_pygame.py` & `spillmotor_pygame.py`
*   **Action**: Create `SpillerkortSkjerm` in `ui_pygame.py` matching the description.
*   **Action**: Add `_vis_spillerkort(spiller, spiller_liste, idx, on_tilbake)` in `spillmotor_pygame.py`.
*   **Action**: In `SpillerstallSkjerm` and `LaguttakSkjerm`, bind double-click (or single click when already selected) to call the callback for `SpillerkortSkjerm`.
*   **Verification**: Run a python script importing `SpillerkortSkjerm` to verify syntax.

## TESTPROSEDYRE
*   **Action**: Execute `test_smoke.py` if available, or write a short bash/python script to verify the game loop runs without crashing. Create an `ENDRINGSLOGG.md` describing the changes.

## Pre-commit & Submit
*   Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
*   Submit with descriptive commit message.
