import csv
import subprocess
import sys
import time
from pathlib import Path

CARTELLA_VIDEO = Path("/Users/macdiisabella/Documents/tesi_ravveduto/dati_familiarizzazione/video_tiktok")
FILE_FALLITI = CARTELLA_VIDEO / "download_falliti.csv"
FILE_ERRORI_FOTO = CARTELLA_VIDEO / "foto_fallite.csv"
PAUSA_SECONDI = 2


def leggi_post_foto(percorso):
    """Legge il csv dei download falliti e tiene solo i post foto (url con /photo/).
    Restituisce una lista di tuple (url, profilo, numero)."""
    with open(percorso, newline="") as f:
        righe = list(csv.DictReader(f))
    post = []
    for riga in righe:
        if "/photo/" not in riga["url video"]:
            continue
        # come per i video, il profilo si separa dal numero sull'ultimo "_"
        profilo, numero = riga["indice"].rsplit("_", 1)
        post.append((riga["url video"], profilo, numero))
    return post


def scarica_post(url, cartella, browser):
    """Scarica immagini e audio di un post foto dentro la cartella indicata:
    le immagini come 1.jpg, 2.jpg, ... e l'audio come audio.mp3.
    Restituisce None se va a buon fine, altrimenti il messaggio di errore."""
    comando = [
        sys.executable, "-m", "gallery_dl",
        "--cookies-from-browser", browser,
        "-D", str(cartella),
        # gallery-dl numera l'audio come 0 e le immagini da 1 in poi
        "-f", "{num}.{extension}",
        url,
    ]
    esito = subprocess.run(comando, capture_output=True, text=True)
    audio = cartella / "0.mp3"
    if audio.exists():
        audio.rename(cartella / "audio.mp3")
    file_scaricati = [f for f in cartella.iterdir() if not f.name.endswith(".part")] if cartella.exists() else []
    if esito.returncode != 0 or not file_scaricati:
        return (esito.stderr or esito.stdout or "nessun file scaricato").strip()
    return None


if __name__ == "__main__":
    # argomento facoltativo: il browser da cui leggere il login tiktok (default chrome)
    browser = sys.argv[1] if len(sys.argv) > 1 else "chrome"
    post = leggi_post_foto(FILE_FALLITI)
    falliti = []
    for i, (url, profilo, numero) in enumerate(post, start=1):
        cartella = CARTELLA_VIDEO / profilo / numero
        # i post con la cartella già piena vengono saltati, così lo script si può rilanciare
        if cartella.exists() and any(cartella.iterdir()):
            print(f"[{i}/{len(post)}] {profilo}_{numero} già presente")
            continue
        errore = scarica_post(url, cartella, browser)
        if errore:
            falliti.append([url, f"{profilo}_{numero}", errore])
            print(f"[{i}/{len(post)}] {profilo}_{numero} ERRORE: {errore[:150]}")
        else:
            print(f"[{i}/{len(post)}] {profilo}_{numero} scaricato")
        time.sleep(PAUSA_SECONDI)
    with open(FILE_ERRORI_FOTO, "w", newline="") as f:
        scrittore = csv.writer(f)
        scrittore.writerow(["url video", "indice", "errore"])
        scrittore.writerows(falliti)
    print(f"Fatto: {len(post) - len(falliti)} ok, {len(falliti)} falliti (vedi {FILE_ERRORI_FOTO})")
