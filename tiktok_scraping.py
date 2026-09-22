import asyncio
import csv
import os

from TikTokApi import TikTokApi

# token di sessione da copiare dai cookie del browser (chiave "msToken")
# necessario perché tiktok richiede una verifica anti-bot per accettare le richieste
ms_token = os.environ.get("ms_token_tiktok")


async def ottieni_video_hashtag(hashtag, numero_video=30):
    # recupera i video pubblicati sotto un determinato hashtag di tiktok
    # restituisce una lista di dizionari con i dati principali di ogni video
    video_trovati = []

    async with TikTokApi() as api:
        # headless=False e webkit riducono il rischio che tiktok rilevi il bot
        await api.create_sessions(
            ms_tokens=[ms_token],
            num_sessions=1,
            sleep_after=3,
            headless=False,
            browser="webkit",
        )

        tag = api.hashtag(name=hashtag)

        async for video in tag.videos(count=numero_video):
            dati = video.as_dict
            autore = dati.get("author", {}).get("uniqueId")
            id_video = dati.get("id")

            video_trovati.append({
                "id": id_video,
                "autore": autore,
                "descrizione": dati.get("desc"),
                "like": dati.get("stats", {}).get("diggCount"),
                "commenti": dati.get("stats", {}).get("commentCount"),
                "condivisioni": dati.get("stats", {}).get("shareCount"),
                "visualizzazioni": dati.get("stats", {}).get("playCount"),
                "url": f"https://www.tiktok.com/@{autore}/video/{id_video}",
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


async def main():
    # avvia lo scraping di un hashtag e salva i risultati in csv
    # non restituisce nulla
    hashtag = "python"
    percorso_file = "risultati_tiktok.csv"

    video = await ottieni_video_hashtag(hashtag, numero_video=30)
    salva_csv(video, percorso_file)

    print(f"salvati {len(video)} video in {percorso_file}")


if __name__ == "__main__":
    asyncio.run(main())
