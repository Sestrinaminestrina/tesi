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
        # dizionario annidato, se non esistesse chiave authorMeta invece di dare errore restituisce dizionario vuoto (valore di default)
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


def ottieni_commenti_video(video, numero_commenti=50):
    # avvia l'actor apify "clockworks/tiktok-comments-scraper" sugli url dei video passati
    # restituisce una lista di dizionari con i commenti trovati, ciascuno collegato al video di origine
    if not video:
        return []

    # mappa ogni url del video al suo id, per poter ricollegare ogni commento al video corretto
    id_per_url = {v["url"]: v["id"] for v in video}

    client = ApifyClient(token_apify)

    input_actor = {
        "postURLs": list(id_per_url.keys()),
        "commentsPerPost": numero_commenti,
    }

    esecuzione = client.actor("clockworks/tiktok-comments-scraper").call(run_input=input_actor)

    commenti_trovati = []

    # l'actor restituisce "videoWebUrl" per ogni commento: e' il collegamento al video di origine
    for dati in client.dataset(esecuzione["defaultDatasetId"]).iterate_items():
        commenti_trovati.append({
            "id_video": id_per_url.get(dati.get("videoWebUrl")),
            "id_commento": dati.get("cid"),
            "autore": dati.get("uniqueId"),
            "testo": dati.get("text"),
            "like": dati.get("diggCount"),
            "risposte": dati.get("replyCommentTotal"),
            "data": dati.get("createTimeISO"),
        })

    return commenti_trovati


def salva_csv(righe, percorso_file):
    # salva una lista di dizionari in un file csv, una riga per elemento
    # sovrascrive sempre il file esistente allo stesso percorso
    # non restituisce nulla
    if not righe:
        print(f"nessun dato da salvare in {percorso_file}")
        return

    campi = righe[0].keys()

    with open(percorso_file, "w", newline="", encoding="utf-8") as file_csv:
        scrittore = csv.DictWriter(file_csv, fieldnames=campi)
        scrittore.writeheader()
        scrittore.writerows(righe)


def main():
    # avvia lo scraping di un hashtag e poi dei commenti dei video trovati
    # le due tabelle vengono sempre rigenerate insieme, cosi restano coerenti tra loro
    # non restituisce nulla
    hashtag = "mafia"
    percorso_video = "risultati_tiktok.csv"
    percorso_commenti = "risultati_commenti.csv"

    video = ottieni_video_hashtag(hashtag, numero_video=3)
    salva_csv(video, percorso_video)
    print(f"salvati {len(video)} video in {percorso_video}")

    commenti = ottieni_commenti_video(video, numero_commenti=10)
    salva_csv(commenti, percorso_commenti)
    print(f"salvati {len(commenti)} commenti in {percorso_commenti}")


if __name__ == "__main__":
    main()
