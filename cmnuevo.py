import random
import time

# 1. Databasen: Definerer hvordan en spiller og et lag ser ut
class Spiller:
    def __init__(self, navn, posisjon, ferdighet):
        self.navn = navn
        self.posisjon = posisjon  # 'K' (Keeper), 'F' (Forsvar), 'M' (Midtbane), 'A' (Angrep)
        self.ferdighet = ferdighet # Skala 1-20

class Lag:
    def __init__(self, navn, spillere):
        self.navn = navn
        self.spillere = spillere
        
    def hent_lagdel_styrke(self, posisjon):
        # Regner ut gjennomsnittlig ferdighet for en spesifikk lagdel
        lagdel = [s for s in self.spillere if s.posisjon == posisjon]
        if not lagdel: 
            return 0
        total_ferdighet = sum(s.ferdighet for s in lagdel)
        return total_ferdighet / len(lagdel)

# 2. Kampmotoren: Håndterer selve kampen
class Kamp:
    def __init__(self, hjemmelag, bortelag):
        self.hjemme = hjemmelag
        self.borte = bortelag
        self.maal_hjemme = 0
        self.maal_borte = 0

    def spill_kamp(self):
        print(f"--- KAMPSTART: {self.hjemme.navn} vs {self.borte.navn} ---")
        
        for minutt in range(1, 91):
            # 5 % sjanse for at en målsjanse oppstår i hvert minutt
            if random.random() < 0.05:
                self.simuler_sjanse(minutt)
            
            # time.sleep(0.05) # Fjern emneknaggen her for å få den klassiske "teksten ruller"-følelsen

        print("\n--- KAMPSLUTT ---")
        print(f"Resultat: {self.hjemme.navn} {self.maal_hjemme} - {self.maal_borte} {self.borte.navn}")

    def simuler_sjanse(self, minutt):
        # Forenklet: 50/50 sjanse for hvem som får angrepet
        if random.random() < 0.5:
            angriper, forsvarer = self.hjemme, self.borte
        else:
            angriper, forsvarer = self.borte, self.hjemme
            
        angrep_styrke = angriper.hent_lagdel_styrke('A')
        forsvar_styrke = forsvarer.hent_lagdel_styrke('F')
        
        print(f"{minutt}. min: Sjanse til {angriper.navn}!")
        time.sleep(1) # Liten pause for spenningens skyld
        
        # Matematikken bak et mål: Angrep vs Forsvar pluss et "terningkast"
        if (angrep_styrke + random.randint(1, 10)) > (forsvar_styrke + random.randint(1, 10)):
            print(f" -> MÅÅÅL! Fantastisk avslutning av {angriper.navn}!")
            if angriper == self.hjemme:
                self.maal_hjemme += 1
            else:
                self.maal_borte += 1
        else:
            print(" -> Avslutningen går rett på keeper.")

# 3. Teste spillet!
if __name__ == "__main__":
    # Lager noen spillere
    spillere_glimt = [
        Spiller("Khaikin", "K", 15), Spiller("Moe", "F", 14), 
        Spiller("Berg", "M", 17), Spiller("Pellegrino", "A", 16)
    ]
    spillere_brann = [
        Spiller("Dyngeland", "K", 14), Spiller("Crone", "F", 13), 
        Spiller("Nilsen", "M", 15), Spiller("Finne", "A", 16)
    ]
    
    # Oppretter lagene
    glimt = Lag("Bodø/Glimt", spillere_glimt)
    brann = Lag("Brann", spillere_brann)
    
    # Starter kampen
    dagens_kamp = Kamp(glimt, brann)
    dagens_kamp.spill_kamp()
