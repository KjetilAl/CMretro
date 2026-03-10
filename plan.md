# 1. FEIL 1 - Oppløsning (ui_pygame.py)
Update W_BASE, H_BASE to 640, 400 and SKALA to 2. Wait, the problem is that every coordinate is hardcoded. So I will multiply all x, y, width, height constants by 2 in `ui_pygame.py`.
Since `W_BASE = 320 -> 640`, and `H_BASE = 200 -> 400`, we just double every number.
Font sizes: liten=13, normal=15, fet=15, bold=True, stor=20, tittel=26.
Also `max_bredde` in `tegn_tekst` calls need to be doubled.

# 2. FEIL 2 - Divisjoner i VelgKlubbSkjerm (spillmotor_pygame.py)
In `_lag_velg_klubb_skjerm`:
```python
DIVISJON_REKKEFØLGE = {
    'Eliteserien': 0, 'OBOS-ligaen': 1,
    'Div 2': 2, 'Div 3': 3,
}
# flatten clubs, sort by DIVISJON_REKKEFØLGE, then historisk_styrke desc
alle_lag = sorted(
    self.klubber.values(),
    key=lambda k: (DIVISJON_REKKEFØLGE.get(getattr(k, 'divisjon', ''), 99),
                   -getattr(k, 'historisk_styrke', 0))
)
```
In `VelgKlubbSkjerm`, check if the element is a string (division name) or club. If string, draw gray separator.
Update `_bygg_liga_og_kalender` to create `Seriatabell` for all divisions.
In `TabellSkjerm`, add a tab for the current division, maybe other divisions too if requested. The instruction: `vis en fane per divisjon spillerens klubb tilhører` - actually, a club can only belong to one division. But maybe it means "vis en fane for tabellen til divisjonen spillerens klubb tilhører"? No, wait. "vis en fane per divisjon spillerens klubb tilhører" - maybe it means "vis en fane per divisjon [komma] [som] spillerens klubb tilhører" ? Wait. Let's look at `_bygg_liga_og_kalender()` and `_vis_tabell()`. Wait, "vis en fane per divisjon [hvis?] spillerens klubb tilhører"? "vis en fane per divisjon [punktum] spillerens klubb tilhører [vises som standard?]" No. "vis en fane per divisjon [komma] [pluss fane for] spillerens klubb tilhører"? No. "vis en fane per divisjon som finnes, ..." No, "vis en fane per divisjon [som] spillerens klubb tilhører" - ah! Wait! The user says "vis en fane per divisjon. [Default tab:] spillerens klubb tilhører". Ah, it says "vis en fane per divisjon spillerens klubb tilhører" - No, it's just "vis en fane per divisjon spillerens klubb tilhører" which probably means "vis en fane for tabellen" is what it is now, but wait, a single TabellSkjerm takes `self._tabell`. If there are multiple divisions, `spillmotor_pygame.py` needs to pass a dict of `Seriatabell` objects. And the UI will have tabs for each division.

# 3. FEIL 3 - OpprettManagerSkjerm (ui_pygame.py & spillmotor_pygame.py)
Implement `OpprettManagerSkjerm` class.
Call it in `spillmotor_pygame.py` before `_bygg_liga_og_kalender()`.

# 4. FEIL 4 - Andre lags kamper (spillmotor_pygame.py)
Implement `_simuler_alle_andre_kamper(self, dag)` and call it.

# 5. FEIL 5 - Ferdigheter (database.py / person.py / ui_pygame.py)
Fix A: The issue is B: database.py doesn't set ovr_mål correctly when generating players, and it doesn't generate attributes for existing players in `spillere.json`.
Actually, if I fix `database.py` to call `person.lag_spiller` when generating, and for existing players, if they don't have technical attributes, I can use the same logic. But wait, `lag_spiller` in `person.py` uses `random`. Wait! The instruction says:
"Sannsynlig årsak A — OVR-formelen returnerer alltid 10: FIL: person.py, property ferdighet() Sjekk _OVR_VEKTER-oppslaget og at primær_posisjon er satt riktig når lag_spiller() kalles fra database.py."
"Sannsynlig årsak B — database.py genererer alle spillere med ovr_mål=10: FIL: database.py — finn kallet til lag_spiller() og sjekk at ovr_mål varierer realistisk per klubb og posisjon: Eliteserien-lag: OVR 11–17 (topplaget ~16–17, bunnlag ~11–12) OBOS-ligaen: OVR 9–14 Div 2: OVR 7–11 Div 3: OVR 5–9 Sørg for at variasjon=2 eller 3 brukes."
"Sannsynlig årsak C — SpillerstallSkjerm i ui_pygame.py viser feil felt: Sjekk at tegn_tekst(..., str(ferd), ...) faktisk henter getattr(s, 'ferdighet', 0) der s er et Person-objekt med primær_posisjon satt."
"Fix alle tre mulige årsaker."
I need to fix all three:
- A: In `person.py`, `_beregn_ovr` fallback? Wait, in `lag_spiller`, it might not set `primær_posisjon` correctly? I'll check.
- B: In `database.py`, `_generer_spiller` should call `person.lag_spiller` with the correct `ovr_mål` based on division/historisk_styrke! Wait, currently `database.py` has its own `_generer_spiller` implementation! I should modify it to call `lag_spiller`! And for existing players, I should also make sure they get technical attributes generated.
- C: In `SpillerstallSkjerm`, `tegn_badge(..., str(ferd))` shows `ferd = getattr(s, 'ferdighet', 0)`. That's already there! But wait, is `primær_posisjon` an Enum? In `database.py`, it sets `person.primær_posisjon = Posisjon[d["primær_posisjon"]]`. `Posisjon` is an enum. But wait, if it's an enum, does `person.py` use `posisjon.name` or `posisjon`? `_OVR_VEKTER` uses `Posisjon.K`. Wait, in `database.py` it sets `person.primær_posisjon = primær_pos`. But wait, `person.py`'s `lag_spiller` uses `posisjon: Posisjon`.

# 6. FEIL 6 - Spillerkort (ui_pygame.py & spillmotor_pygame.py)
Implement `SpillerkortSkjerm` and `_vis_spillerkort`.
