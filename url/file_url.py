import re

# Riconosce gli url tiktok con o senza protocollo e con qualsiasi sottodominio
# (www., vm., vt., m.), fermandosi al primo spazio, virgolette o separatore
PATTERN_TIKTOK = re.compile(
    r"(?:https?://)?(?:[\w-]+\.)?tiktok\.com/[^\s\"'<>,;()\[\]{}]+",
    re.IGNORECASE,
)


# Url di un singolo contenuto: /video/ o /photo/ (caroselli di foto) oppure
# link brevi di condivisione (vm., vt., /t/), che rimandano sempre a un contenuto
PATTERN_VIDEO = re.compile(
    r"/(?:video|photo)/\d+|//(?:vm|vt)\.tiktok\.com/|tiktok\.com/t/",
    re.IGNORECASE,
)

# Url di un profilo: tiktok.com/@nome senza altri segmenti di percorso
PATTERN_PROFILO = re.compile(r"tiktok\.com/@[^/?#]+/?(?:[?#]|$)", re.IGNORECASE)


def scrivi_righe(nome_file, lista_url):
    """
    Scrive in nome_file gli url di lista_url, uno per riga, sovrascrivendo
    il file se esiste già. Non restituisce nulla.
    """
    with open(nome_file, "w", encoding="utf-8") as f:
        for url in lista_url:
            f.write(url + "\n")


def estrai_url_tiktok(
    file_input,
    file_video="url_tiktok_video.txt",
    file_profilo="url_tiktok_profilo.txt",
):
    """
    Legge il file di testo file_input, estrae tutti gli url tiktok ignorando
    il resto del testo e li divide tra url di video (scritti in file_video)
    e url di profili (scritti in file_profilo), uno per riga.
    Restituisce la coppia (lista_video, lista_profili), senza duplicati e
    in ordine di apparizione.
    """
    with open(file_input, "r", encoding="utf-8") as f:
        testo = f.read()

    lista_video = []
    lista_profili = []
    for url in PATTERN_TIKTOK.findall(testo):
        # Rimuove la punteggiatura finale che non fa parte dell'url (es. fine frase)
        url = url.rstrip(".!?:")
        if not url.startswith("http"):
            url = "https://" + url

        if PATTERN_VIDEO.search(url):
            destinazione = lista_video
        elif PATTERN_PROFILO.search(url):
            destinazione = lista_profili
        else:
            # Altri url tiktok (es. pagine di hashtag o musica) vengono ignorati
            continue

        if url not in destinazione:
            destinazione.append(url)

    scrivi_righe(file_video, lista_video)
    scrivi_righe(file_profilo, lista_profili)

    return lista_video, lista_profili


if __name__ == "__main__":
    video, profili = estrai_url_tiktok("chat_wa_url.txt")
    print(f"video: {len(video)}, profili: {len(profili)}")
