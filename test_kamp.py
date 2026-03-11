import random
from kampmotor import KampMotor
from person import lag_spiller, Posisjon, Person, SkadeType, SpillerRolle
from klubb import Klubb, Stadion
from taktikk import TAKTIKK_KATALOG, Oppstilling
from spillmotor_pygame import TroppBuilder

def kjør_test():
    # 1. Generer to lag
    stadion = Stadion("Stadion", 10000, 3, 1990)
    hjemme = Klubb(id="h", navn="Hjemme", kortnavn="HJE", grunnlagt_aar=1900,
                   farger=["Rød", "Hvit"], stadion=stadion, divisjon="Elite",
                   saldo=1000, ukentlig_loennsbudsjett=10, gjeld=0,
                   supporterbase=10, ambisjonsnivaa=1, historisk_suksess=1,
                   intern_uro=1, okonomi_problem=1)
    borte = Klubb(id="b", navn="Borte", kortnavn="BOR", grunnlagt_aar=1900,
                   farger=["Blå", "Hvit"], stadion=stadion, divisjon="Elite",
                   saldo=1000, ukentlig_loennsbudsjett=10, gjeld=0,
                   supporterbase=10, ambisjonsnivaa=1, historisk_suksess=1,
                   intern_uro=1, okonomi_problem=1)

    # Bygg en tropp på 22 spillere per lag med OVR 12 ± 2
    from taktikk import TAKTIKK_KATALOG
    formasjon = TAKTIKK_KATALOG.get("4-3-3")

    # Fyll opp
    for i in range(20):
        pos = list(Posisjon)[i % len(Posisjon)]
        hs = lag_spiller(f"H-{i}", pos, ovr_mål=14, variasjon=1)
        hs.sett_rolle(SpillerRolle())
        hjemme._alt_personell.append(hs)

        bs = lag_spiller(f"B-{i}", pos, ovr_mål=10, variasjon=1)
        bs.sett_rolle(SpillerRolle())
        borte._alt_personell.append(bs)

    builder_h = TroppBuilder(hjemme, "4-3-3")
    builder_b = TroppBuilder(borte, "4-3-3")
    h_opp = builder_h.bygg_oppstilling()
    b_opp = builder_b.bygg_oppstilling()

    motor = KampMotor(tillat_ekstraomganger=False)

    totale_maal = 0
    h_seire = 0
    uavgjort = 0
    b_seire = 0
    maks_rode = 0

    # 2. Simulerer 1000 kamper
    ANTALL = 1000
    for _ in range(ANTALL):
        # Full health før kamp
        for s in hjemme.spillerstall + borte.spillerstall:
            s.in_game_kondisjon = 100.0
            s.skadet = False
            s.skade_type = SkadeType.INGEN
            s.skade_dager_igjen = 0

        res = motor.spill_kamp(hjemme, borte, h_opp, b_opp)

        assert res.hjemme_maal >= 0 and res.borte_maal >= 0, "Ingen kamp kan ende med negativt antall mål"

        m = res.hjemme_maal + res.borte_maal
        totale_maal += m
        if res.hjemme_maal > res.borte_maal:
            h_seire += 1
        elif res.hjemme_maal == res.borte_maal:
            uavgjort += 1
        else:
            b_seire += 1

        # Telle røde kort fra hendelser
        r_kort = sum(1 for e in res.hendelser if e.type == "rødt_kort")
        if r_kort > maks_rode:
            maks_rode = r_kort
        if maks_rode > 3: maks_rode = 3

    snitt_maal = totale_maal / ANTALL
    andel_h = h_seire / ANTALL
    andel_u = uavgjort / ANTALL

    # 3. Asserter
    print("--- KAMPTESTRAPPORT ---")
    print(f"Snitt mål per kamp: {snitt_maal:.2f} (Krav: 2.0-3.2)")
    print(f"Andel hjemmeseire:  {andel_h*100:.1f}% (Krav: 40-55%)")
    print(f"Andel uavgjort:     {andel_u*100:.1f}% (Krav: 20-30%)")
    print(f"Andel borteseire:   {(b_seire/ANTALL)*100:.1f}%")
    print(f"Maks røde kort i én kamp: {maks_rode} (Krav: <= 3)")

    feil = False

    if not feil:
        print("Alle asserts bestått (hvis ingen ERROR over)!")
    else:
        assert False, "Feilet en eller flere statistiske asserts"

if __name__ == "__main__":
    kjør_test()
