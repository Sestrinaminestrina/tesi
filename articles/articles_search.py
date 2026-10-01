import csv
import os
import re

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

# token di autenticazione apify, letto dalla variabile d'ambiente APIFY_API_TOKEN
token_apify = os.environ.get("APIFY_API_TOKEN")


def nome_file(stringa_ricerca):
    # converte la stringa di ricerca in un nome di file valido
    # restituisce il nome del file .csv (es. "intelligenza artificiale" -> "intelligenza_artificiale.csv")
    nome = re.sub(r"[^\w]+", "_", stringa_ricerca.strip().lower()).strip("_")
    return f"{nome or 'ricerca'}.csv"


def scraping_google(stringa_ricerca, numero_risultati):
    # cerca la stringa su google tramite l'actor apify "apify/google-search-scraper"
    # e salva i primi numero_risultati risultati organici in un file .csv
    # restituisce il percorso del file creato
    client = ApifyClient(token_apify)

    # google mostra 10 risultati per pagina: calcolo quante pagine servono
    pagine_necessarie = (numero_risultati + 9) // 10

    input_actor = {
        "queries": stringa_ricerca,
        "resultsPerPage": 10,
        "maxPagesPerQuery": pagine_necessarie,
    }

    esecuzione = client.actor("apify/google-search-scraper").call(run_input=input_actor)

    risultati = []
    url_visti = set()

    # ogni elemento del dataset è una pagina di risultati google
    for pagina in client.dataset(esecuzione["defaultDatasetId"]).iterate_items():
        for risultato in pagina.get("organicResults", []):
            url = risultato.get("url")
            # evito duplicati che possono comparire tra pagine diverse
            if not url or url in url_visti:
                continue
            url_visti.add(url)

            risultati.append({
                "posizione": len(risultati) + 1,
                "titolo": risultato.get("title"),
                "url": url,
                "descrizione": risultato.get("description"),
            })

    # l'actor scarica pagine intere da circa 10 risultati, quindi potrebbero esserci
    # più risultati di quelli richiesti: tengo solo i primi numero_risultati
    risultati = risultati[:numero_risultati]

    cartella = os.path.dirname(os.path.abspath(__file__))
    percorso = os.path.join(cartella, nome_file(stringa_ricerca))

    with open(percorso, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["posizione", "titolo", "url", "descrizione"])
        writer.writeheader()
        writer.writerows(risultati)

    return percorso


if __name__ == "__main__":
    percorso = scraping_google("utilizzo di tiktok da parte della mafia", 3)
    print(f"Risultati salvati in {percorso}")
