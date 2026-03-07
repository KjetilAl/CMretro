import json
import random
from typing import Optional

# =============================================================================
# KONFIGURASJON
# API-nøkkelen bør ligge i en .env-fil i produksjon:
#   pip install python-dotenv
#   fra .env: GEMINI_API_KEY=din_nøkkel
# =============================================================================
try:
    import google.generativeai as genai
    _GEMINI_TILGJENGELIG = True
except ImportError:
    _GEMINI_TILGJENGELIG = False

API_KEY = "DIN_API_NØKKEL_HER"   # Bytt ut med ekte nøkkel eller les fra .env

if _GEMINI_TILGJENGELIG and API_KEY != "DIN_API_NØKKEL_HER":
    genai.configure(api_key=API_KEY)
    _MODELL = genai.GenerativeModel('gemini-1.5-flash')
else:
    _MODELL = None


# =============================================================================
# STATISKE FALLBACK-MALER
# Brukes når Gemini ikke er tilgjengelig eller feiler.
# Nok variasjon til at det ikke føles mekanisk.
# =============================================================================
FALLBACK_MALER = {
    "LAV_FORM_STREAK": [
        {
            "overskrift": "{spiller} er en skygge av seg selv",
            "ingress":    "{spiller} har levert skuffende prestasjoner de siste kampene. "
                          "Presset fra supporterne øker.",
            "tweet":      "Tid for benk??? {spiller} er helt borte for tida 😤 "
                          "#{klubb_tag}",
        },
        {
            "overskrift": "Ekspertene er knallharde: – {spiller} må hvile",
            "ingress":    "Etter en rekke svake kamper mener kommentatorer at {spiller} "
                          "trenger en pause fra startoppstillingen.",
            "tweet":      "Samme gamle {spiller}... vi fortjener bedre. "
                          "#{klubb_tag} #Skuffet",
        },
        {
            "overskrift": "Formkrisen fortsetter for {spiller}",
            "ingress":    "{spiller} sliter med selvtilliten og leverer langt under sitt beste. "
                          "Manageren har en vanskelig beslutning foran seg.",
            "tweet":      "Selg ham!! {spiller} holder ikke mål på dette nivået lenger "
                          "#{klubb_tag} 😭",
        },
    ],
    "HØY_FORM_STREAK": [
        {
            "overskrift": "{spiller} er ustoppelig — {klubb} jubler",
            "ingress":    "Med nok en strålende prestasjon befester {spiller} seg som "
                          "en av seriens beste denne sesongen.",
            "tweet":      "DETTE ER FOTBALL!! {spiller} er på et annet nivå rn 🔥🔥 "
                          "#{klubb_tag}",
        },
        {
            "overskrift": "Stopp ham om du kan: {spiller} herjer i {klubb}",
            "ingress":    "{spiller} er i karrierens beste form og setter ligaen på hodene.",
            "tweet":      "Absolutt verdens beste spiller akkurat nå. "
                          "{spiller} 🐐 #{klubb_tag}",
        },
    ],
    "BENKEVARMER": [
        {
            "overskrift": "{spiller} krever svar: – Jeg er ikke fornøyd",
            "ingress":    "Etter å ha vært utelatt fra startelleveren i flere kamper på rad "
                          "melder {spiller} at han ønsker en avklaring med klubben.",
            "tweet":      "Skjønner ikke at {spiller} ikke starter! Skandale! "
                          "#{klubb_tag} #Benk",
        },
        {
            "overskrift": "Agenten til {spiller} ber om møte med {klubb}",
            "ingress":    "Etter en lang periode på benken vil representanten til {spiller} "
                          "diskutere spilletid med klubbledelsen.",
            "tweet":      "{spiller} fortjener mer enn dette. Selg ham til en klubb "
                          "som vil ha ham! #{klubb_tag}",
        },
    ],
    "LANGTIDSSKADET": [
        {
            "overskrift": "Stygg skade for {spiller} — ute i {dager} dager",
            "ingress":    "{klubb} må klare seg uten {spiller} en god stund etter at "
                          "han pådro seg en {skade_type} i trening.",
            "tweet":      "NEI NEI NEI. {spiller} ute?? Sesongen vår er ødelagt "
                          "#{klubb_tag} 😭😭",
        },
        {
            "overskrift": "{klubb}-profil til legen: – {dager} dager på sidelinjen",
            "ingress":    "Det er dyster beskjed fra {klubb}. {spiller} er ute i minst "
                          "{dager} dager etter undersøkelser bekreftet en {skade_type}.",
            "tweet":      "Håper {spiller} er tilbake snart. Send kake 🎂 "
                          "#{klubb_tag} #GetWellSoon",
        },
    ],
    "TAPENDE_REKKE": [
        {
            "overskrift": "KRISE I {klubb}: {tap_rekke} tap på rad",
            "ingress":    "Det stormer rundt {klubb} etter nok et tap. "
                          "Spekulasjonene om managerens fremtid tiltar.",
            "tweet":      "Sparken manager allerede?? Kan ikke fortsette sånn her. "
                          "#{klubb_tag} #Krise",
        },
        {
            "overskrift": "Supporterne er rasende — {klubb} stuper på tabellen",
            "ingress":    "Etter {tap_rekke} strake tap er stemningen blant supporterne "
                          "på et lavmål. Styret er innkalt til hastemøte.",
            "tweet":      "Skam dere {klubb}!! Dette er ikke godt nok!! "
                          "#{klubb_tag} #Ut #Skandale",
        },
    ],
    "VINNENDE_REKKE": [
        {
            "overskrift": "Uslåelige {klubb}: {seier_rekke} seire på rad!",
            "ingress":    "Intet lag kan stoppe {klubb} for øyeblikket. "
                          "Drømmene om gull begynner å ta form.",
            "tweet":      "DETTE LAGET ER FANTASTISK! {seier_rekke} på rad!! "
                          "#{klubb_tag} 🏆🏆🏆",
        },
    ],
    "NEDRYKKSFARE": [
        {
            "overskrift": "NEDRYKKSALARM: {klubb} i livsfarlig posisjon",
            "ingress":    "Med bare {runder_igjen} runder igjen er {klubb} i direkte "
                          "nedrykksposisjon. Det nærmer seg krisemøte i klubben.",
            "tweet":      "Ikke nedrykk ikke nedrykk ikke nedrykk 🙏🙏 "
                          "#{klubb_tag} #Nedrykk",
        },
    ],
    "EUROPA_UTSLÅTT": [
        {
            "overskrift": "Europa-eventyret er over for {klubb}",
            "ingress":    "{klubb} er slått ut av {turnering} etter et skuffende "
                          "resultat. Fokus er nå på ligaen.",
            "tweet":      "Kunne vært mye verre tbh. Fokus på ligaen nå! "
                          "#{klubb_tag} #{turnering_tag}",
        },
    ],
    "DEFAULT": [
        {
            "overskrift": "DRAMA I {klubb}!",
            "ingress":    "Store ting skjer rundt {klubb} for øyeblikket.",
            "tweet":      "Kan ikke tro det som skjer med #{klubb_tag} 😮",
        },
    ],
}


def _fyll_mal(mal: dict, kontekst: dict) -> dict:
    """Erstatter {plassholdere} i en mal med verdier fra kontekst-dicten."""
    resultat = {}
    for nøkkel, tekst in mal.items():
        try:
            resultat[nøkkel] = tekst.format(**kontekst)
        except KeyError:
            resultat[nøkkel] = tekst   # Behold originalen hvis plassholder mangler
    return resultat


def _hent_fallback(hendelse_type: str, kontekst: dict) -> dict:
    """Velger en tilfeldig statisk mal for hendelsestypen."""
    maler = FALLBACK_MALER.get(hendelse_type, FALLBACK_MALER["DEFAULT"])
    mal = random.choice(maler)
    return _fyll_mal(mal, kontekst)


# =============================================================================
# GEMINI-GENERATOR
# =============================================================================
def generer_stordrama(
    hendelse_type: str,
    klubb_navn: str,
    spiller_navn: Optional[str] = None,
    ekstra_info: str = "",
    kontekst: Optional[dict] = None,
) -> dict:
    """
    Genererer en dramatisk nyhetsartikkel via Gemini API.
    Faller tilbake på statiske maler hvis API ikke er tilgjengelig eller feiler.

    Returnerer dict med nøklene:
        overskrift  — tabloid tittel
        ingress     — 1–2 setninger
        tweet       — fiktiv supporter-reaksjon på X/Twitter
    """
    # Bygg kontekst for fallback-maler
    if kontekst is None:
        kontekst = {}
    kontekst.setdefault("spiller",      spiller_navn or "Spilleren")
    kontekst.setdefault("klubb",        klubb_navn)
    kontekst.setdefault("klubb_tag",    klubb_navn.replace(" ", "").replace("/", ""))
    kontekst.setdefault("turnering_tag", "Europa")

    # Ingen Gemini tilgjengelig → rett til fallback
    if not _MODELL:
        return _hent_fallback(hendelse_type, kontekst)

    prompt = f"""
Du er en tabloid sportsjournalist i Norge (tenk VG eller Dagbladet).
Skriv en kort, dramatisk nyhetssak om følgende hendelse i norsk fotball:

Hendelse: {hendelse_type}
Klubb: {klubb_navn}
Spiller/Manager: {spiller_navn if spiller_navn else 'Ingen spesifikk'}
Ekstra kontekst: {ekstra_info}

Svar KUN i gyldig JSON-format med disse nøklene (ingen markdown, ingen forklaring):
{{
  "overskrift": "En clickbait-aktig, tabloid overskrift på norsk",
  "ingress": "Maks to setninger som oppsummerer saken på norsk",
  "tweet": "En fiktiv, overdreven supporter-reaksjon på X/Twitter på norsk med emneknagg"
}}
"""

    try:
        respons = _MODELL.generate_content(prompt)
        tekst = respons.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(tekst)

        # Valider at alle nøkler er tilstede
        for nøkkel in ("overskrift", "ingress", "tweet"):
            if nøkkel not in data:
                raise ValueError(f"Mangler nøkkel: {nøkkel}")

        return data

    except Exception as e:
        print(f"[Nyhetsgenerator] Gemini-feil: {e} — bruker statisk mal.")
        return _hent_fallback(hendelse_type, kontekst)


# =============================================================================
# TEST
# =============================================================================
if __name__ == "__main__":
    print("Tester nyhetsgenerator med statiske maler...\n")

    tester = [
        ("LAV_FORM_STREAK",  "Brann",   "Bård Finne",  {"dager": ""}),
        ("HØY_FORM_STREAK",  "Rosenborg","Aasen",       {}),
        ("BENKEVARMER",      "Molde",   "Hansen",      {}),
        ("TAPENDE_REKKE",    "Viking",  None,          {"tap_rekke": 5}),
        ("LANGTIDSSKADET",   "Vålerenga","Berg",        {"dager": 28, "skade_type": "Muskelskade"}),
    ]

    for hendelse, klubb, spiller, ekstra_kontekst in tester:
        kontekst = ekstra_kontekst
        nyhet = generer_stordrama(hendelse, klubb, spiller, kontekst=kontekst)
        print(f"📰 {nyhet['overskrift']}")
        print(f"   {nyhet['ingress']}")
        print(f"   🐦 {nyhet['tweet']}")
        print()
