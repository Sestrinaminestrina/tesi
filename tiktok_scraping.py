import csv
import os

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

# token di autenticazione apify, letto dalla variabile d'ambiente APIFY_API_TOKEN
# necessario per avviare gli actor e leggere i risultati dal proprio account apify
token_apify = os.environ.get("APIFY_API_TOKEN")


def ottieni_video_hashtag(hashtag, numero_video=30):
    # avvia l'actor apify "clockworks/tiktok-scraper" per un hashtag tiktok
    # restituisce una lista di dizionari con i dati principali di ogni video
    client = ApifyClient(token_apify)

    input_actor = {
        "hashtags": [hashtag],
        "resultsPerPage": numero_video,
    }

    # call() attende il termine dell'esecuzione e restituisce i metadati del run
    esecuzione = client.actor("clockworks/tiktok-scraper").call(run_input=input_actor)

    video_trovati = []

    # i risultati dell'actor vengono scritti in un dataset legato all'esecuzione
    for dati in client.dataset(esecuzione["defaultDatasetId"]).iterate_items():
        autore = dati.get("authorMeta", {}).get("name")
        id_video = dati.get("id")

        video_trovati.append({
            "id": id_video,
            "autore": autore,
            "descrizione": dati.get("text"),
            "like": dati.get("diggCount"),
            "commenti": dati.get("commentCount"),
            "condivisioni": dati.get("shareCount"),
            "visualizzazioni": dati.get("playCount"),
            "url": dati.get("webVideoUrl"),
        })

    return video_trovati


def salva_csv(video, percorso_file):
    # salva la lista di video in un file csv, una riga per video
    # non restituisce nulla
    if not video:
        print("nessun video da salvare")
        return

    campi = video[0].keys()

    with open(percorso_file, "w", newline="", encoding="utf-8") as file_csv:
        scrittore = csv.DictWriter(file_csv, fieldnames=campi)
        scrittore.writeheader()
        scrittore.writerows(video)


def main():
    # avvia lo scraping di un hashtag e salva i risultati in csv
    # non restituisce nulla
    hashtag = "mafia"
    percorso_file = "risultati_tiktok.csv"

    video = ottieni_video_hashtag(hashtag, numero_video=2)
    salva_csv(video, percorso_file)

    print(f"salvati {len(video)} video in {percorso_file}")


if __name__ == "__main__":
    main()
