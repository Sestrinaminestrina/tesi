import re

# Riconosce gli url tiktok con o senza protocollo e con qualsiasi sottodominio
# (www., vm., vt., m.), fermandosi al primo spazio, virgolette o separatore
PATTERN_TIKTOK = re.compile(
    r"(?:https?://)?(?:[\w-]+\.)?tiktok\.com/[^\s\"'<>,;()\[\]{}]+",
    re.IGNORECASE,
)

# Riconosce qualsiasi url con protocollo, fermandosi al primo spazio o virgolette
PATTERN_GENERICO = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)

# Domini di social e piattaforme video: i loro url non sono articoli web
PATTERN_SOCIAL = re.compile(
    r"//(?:[\w-]+\.)*(?:tiktok|instagram|youtube|youtu|facebook|fb|twitter|x)\.(?:com|be|me)\b",
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


def estrai_url(file_input, pattern, pattern_escluso=None, file_output=None):
    """
    Legge il file di testo file_input ed estrae tutti gli url riconosciuti da
    pattern, scartando quelli riconosciuti da pattern_escluso (se indicato).
    Se file_output è indicato, vi scrive gli url trovati, uno per riga.
    Restituisce la lista degli url, senza duplicati e in ordine di apparizione.
    """
    with open(file_input, "r", encoding="utf-8") as f:
        testo = f.read()

    lista_url = []
    for url in pattern.findall(testo):
        # Rimuove la punteggiatura finale che non fa parte dell'url (es. fine frase)
        url = url.rstrip(".!?:,;")
        # Rimuove l'ancora aggiunta dagli annunci google, che non identifica la pagina
        url = url.removesuffix("#google_vignette")
        if not url.startswith("http"):
            url = "https://" + url

        if pattern_escluso and pattern_escluso.search(url):
            continue
        if url not in lista_url:
            lista_url.append(url)

    if file_output:
        scrivi_righe(file_output, lista_url)

    return lista_url


def dividi_tiktok(
    lista_url,
    file_video="url_tiktok_video.txt",
    file_profilo="url_tiktok_profilo.txt",
):
    """
    Divide gli url tiktok di lista_url tra url di video (scritti in file_video)
    e url di profili (scritti in file_profilo), uno per riga; gli altri url
    tiktok (es. pagine di hashtag o musica) vengono ignorati.
    Restituisce la coppia (lista_video, lista_profili).
    """
    lista_video = [url for url in lista_url if PATTERN_VIDEO.search(url)]
    lista_profili = [
        url for url in lista_url
        if not PATTERN_VIDEO.search(url) and PATTERN_PROFILO.search(url)
    ]

    scrivi_righe(file_video, lista_video)
    scrivi_righe(file_profilo, lista_profili)

    return lista_video, lista_profili


if __name__ == "__main__":
    url_tiktok = estrai_url("chat_wa.txt", PATTERN_TIKTOK)
    video, profili = dividi_tiktok(url_tiktok)
    print(f"video: {len(video)}, profili: {len(profili)}")

    # Pagine web (articoli) indicizzate da google: tutti gli url tranne i social
    articoli = estrai_url(
        "chat_wa.txt",
        PATTERN_GENERICO,
        pattern_escluso=PATTERN_SOCIAL,
        file_output="url_google_articles.txt",
    )
    print(f"articoli: {len(articoli)}")
