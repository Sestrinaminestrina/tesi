import csv
import sys
import time
from pathlib import Path

import yt_dlp
from numbers_parser import Document

FILE_INDICE = "/Users/macdiisabella/Documents/tesi_ravveduto/dati_familiarizzazione/indice_video_tiktok_profili.numbers"
CARTELLA_VIDEO = Path("/Users/macdiisabella/Documents/tesi_ravveduto/dati_familiarizzazione/video_tiktok")
FILE_ERRORI = CARTELLA_VIDEO / "download_falliti.csv"
PAUSA_SECONDI = 2


def leggi_indice(percorso):
    """Legge il file numbers con le colonne 'url video' e 'indice'.
    Restituisce una lista di tuple (url, profilo, numero)."""
    righe = Document(percorso).sheets[0].tables[0].rows(values_only=True)
    voci = []
    for url, indice in (riga[:2] for riga in righe[1:]):
        if not url or not indice:
            continue
        # il profilo può contenere "_" o ".", quindi si divide solo sull'ultimo "_"
        profilo, numero = str(indice).rsplit("_", 1)
        voci.append((url.strip(), profilo, numero))
    return voci


def gia_scaricato(cartella, numero):
    """Controlla se nella cartella esiste già un file chiamato con quel numero.
    Restituisce True se esiste, False altrimenti."""
    return any(f.stem == numero for f in cartella.glob(f"{numero}.*") if not f.name.endswith(".part"))


def scarica_video(url, cartella, numero, browser=None):
    """Scarica un video tiktok salvandolo come cartella/numero.estensione.
    Restituisce None se va a buon fine, altrimenti il messaggio di errore."""
    opzioni = {
        "outtmpl": str(cartella / f"{numero}.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    if browser:
        # usa la sessione tiktok già aperta nel browser indicato
        opzioni["cookiesfrombrowser"] = (browser,)
    try:
        with yt_dlp.YoutubeDL(opzioni) as ydl:
            ydl.download([url])
        return None
    except Exception as errore:
        return str(errore)


if __name__ == "__main__":
    # argomento facoltativo: il browser da cui leggere il login tiktok (es. safari, chrome)
    browser = sys.argv[1] if len(sys.argv) > 1 else None
    voci = leggi_indice(FILE_INDICE)
    CARTELLA_VIDEO.mkdir(parents=True, exist_ok=True)
    falliti = []
    for i, (url, profilo, numero) in enumerate(voci, start=1):
        cartella = CARTELLA_VIDEO / profilo
        cartella.mkdir(exist_ok=True)
        # i video già presenti vengono saltati, così lo script si può rilanciare
        if gia_scaricato(cartella, numero):
            print(f"[{i}/{len(voci)}] {profilo}_{numero} già presente")
            continue
        errore = scarica_video(url, cartella, numero, browser)
        if errore:
            falliti.append([url, f"{profilo}_{numero}", errore])
            print(f"[{i}/{len(voci)}] {profilo}_{numero} ERRORE: {errore[:120]}")
        else:
            print(f"[{i}/{len(voci)}] {profilo}_{numero} scaricato")
        time.sleep(PAUSA_SECONDI)
    with open(FILE_ERRORI, "w", newline="") as f:
        scrittore = csv.writer(f)
        scrittore.writerow(["url video", "indice", "errore"])
        scrittore.writerows(falliti)
    print(f"Fatto: {len(voci) - len(falliti)} ok, {len(falliti)} falliti (vedi {FILE_ERRORI})")
