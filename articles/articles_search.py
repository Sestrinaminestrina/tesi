import csv
import json
import os
import re
from datetime import date
from urllib.parse import parse_qs, quote_plus, urlparse

import trafilatura
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

# token di autenticazione apify, letto dalla variabile d'ambiente APIFY_API_TOKEN
token_apify = os.environ.get("APIFY_API_TOKEN")

# numero massimo di pagine google da analizzare per una ricerca (10 risultati ciascuna),
# evita di consumare crediti all'infinito se gli articoli validi sono pochi
pagine_massime = 30

# lunghezza minima del testo estratto: sotto questa soglia la pagina non è un articolo
# (video, pagine indice) oppure è un articolo a pagamento troncato
lunghezza_minima = 1500

# età massima degli articoli da salvare, in anni
anni_massimi = 3

# siti di video e social: i loro risultati non sono articoli
domini_esclusi = (
    "youtube.com", "youtu.be", "www.tiktok.com", "instagram.com",
    "facebook.com", "twitter.com", "x.com", "linkedin.com",
)


def nome_file(testo, estensione):
    # converte un testo (stringa di ricerca o titolo) in un nome di file valido
    # restituisce il nome con l'estensione indicata (es. "Mafia e TikTok", "txt" -> "mafia_e_tiktok.txt")
    nome = re.sub(r"[^\w]+", "_", testo.strip().lower()).strip("_")
    # tronco i titoli troppo lunghi per non superare i limiti del file system
    nome = nome[:80].rstrip("_")
    return f"{nome or 'senza_nome'}.{estensione}"


def cerca_google(client, stringa_ricerca, pagina_iniziale, numero_pagine, data_limite):
    # scarica numero_pagine pagine di risultati google a partire da pagina_iniziale (contando da 0),
    # limitate ai risultati successivi a data_limite, tramite l'actor apify "apify/google-search-scraper"
    # restituisce la lista dei risultati organici in ordine, ciascuno con la sua posizione su google
    # tbs=cdr:1,cd_min:... è il filtro di google "intervallo di date personalizzato" (formato mese/giorno/anno)
    filtro_data = quote_plus(f"cdr:1,cd_min:{data_limite.month}/{data_limite.day}/{data_limite.year}")

    # una url di ricerca google per ogni pagina: start indica da quale risultato partire
    url_ricerca = [
        f"https://www.google.com/search?q={quote_plus(stringa_ricerca)}&tbs={filtro_data}&start={pagina * 10}"
        for pagina in range(pagina_iniziale, pagina_iniziale + numero_pagine)
    ]

    input_actor = {
        "queries": "\n".join(url_ricerca),
        "maxPagesPerQuery": 1,
    }

    esecuzione = client.actor("apify/google-search-scraper").call(run_input=input_actor)

    pagine = list(client.dataset(esecuzione["defaultDatasetId"]).iterate_items())

    # l'actor può restituire le pagine in ordine sparso: le riordino usando il parametro start
    def inizio_pagina(pagina):
        url = pagina.get("searchQuery", {}).get("url") or pagina.get("url") or ""
        return int(parse_qs(urlparse(url).query).get("start", ["0"])[0])

    risultati = []
    for pagina in sorted(pagine, key=inizio_pagina):
        inizio = inizio_pagina(pagina)
        for indice, risultato in enumerate(pagina.get("organicResults", [])):
            risultato["posizione"] = inizio + indice + 1
            risultati.append(risultato)

    return risultati


def analizza_articolo(url, data_limite):
    # scarica la pagina e ne estrae titolo, data di pubblicazione e testo con trafilatura
    # restituisce una coppia (articolo, motivo): articolo è un dizionario se la pagina è valida,
    # altrimenti è None e motivo spiega perché è stata scartata
    indirizzo = urlparse(url)
    dominio = indirizzo.netloc.lower()

    if any(dominio == escluso or dominio.endswith("." + escluso) for escluso in domini_esclusi):
        return None, "sito di video o social"
    if indirizzo.path.lower().endswith(".pdf"):
        return None, "documento pdf"
    if indirizzo.path in ("", "/"):
        return None, "home page di un sito"

    html = trafilatura.fetch_url(url)
    if not html:
        return None, "download bloccato o fallito"

    # i siti a pagamento segnalano a google i contenuti riservati con isAccessibleForFree = false
    if re.search(r'"isAccessibleForFree"\s*:\s*"?false', html, re.IGNORECASE):
        return None, "articolo a pagamento"

    # extensive_search=False: la data viene letta solo dai metadati della pagina,
    # senza tentare di indovinarla da altre date presenti nel testo (spesso sbagliate)
    estratto = trafilatura.extract(
        html,
        url=url,
        output_format="json",
        with_metadata=True,
        date_extraction_params={
            "extensive_search": False,
            "original_date": True,
            "max_date": date.today().isoformat(),
        },
    )
    if not estratto:
        return None, "testo non estraibile"

    dati = json.loads(estratto)
    testo = dati.get("text") or ""

    if len(testo) < lunghezza_minima:
        return None, "testo troppo breve (non è un articolo o è a pagamento)"
    if not dati.get("date"):
        return None, "data di pubblicazione non trovata"

    data_pubblicazione = date.fromisoformat(dati["date"][:10])
    if data_pubblicazione < data_limite:
        return None, f"pubblicato più di {anni_massimi} anni fa ({data_pubblicazione})"

    articolo = {
        "titolo": dati.get("title"),
        "data_pubblicazione": data_pubblicazione.isoformat(),
        "testo": testo,
    }
    return articolo, None


def scraping_google(stringa_ricerca, numero_risultati):
    # cerca la stringa su google tramite l'actor apify "apify/google-search-scraper" e salva
    # i primi numero_risultati articoli validi (pubblicati negli ultimi anni_massimi anni, gratuiti
    # e scaricabili): i dati in un file .csv e il testo di ciascun articolo in un file .txt
    # restituisce il percorso del file .csv creato
    client = ApifyClient(token_apify)

    oggi = date.today()
    try:
        data_limite = oggi.replace(year=oggi.year - anni_massimi)
    except ValueError:
        # oggi è il 29 febbraio e l'anno di destinazione non è bisestile: uso il 28
        data_limite = oggi.replace(year=oggi.year - anni_massimi, day=28)

    cartella = os.path.dirname(os.path.abspath(__file__))
    nome_ricerca = nome_file(stringa_ricerca, "csv")[:-4]
    # i file .txt vanno in una sottocartella con il nome della ricerca
    cartella_testi = os.path.join(cartella, nome_ricerca)
    os.makedirs(cartella_testi, exist_ok=True)

    # svuoto la cartella dai .txt di eventuali esecuzioni precedenti della stessa ricerca,
    # così restano solo i testi degli articoli presenti nel nuovo csv
    for nome_vecchio in os.listdir(cartella_testi):
        if nome_vecchio.endswith(".txt"):
            os.remove(os.path.join(cartella_testi, nome_vecchio))

    articoli = []
    url_visti = set()
    file_usati = set()
    pagina_corrente = 0

    while len(articoli) < numero_risultati and pagina_corrente < pagine_massime:
        # chiedo a google circa il doppio dei risultati mancanti, perché molti verranno scartati
        mancanti = numero_risultati - len(articoli)
        numero_pagine = min((mancanti * 2 + 9) // 10, pagine_massime - pagina_corrente)

        risultati = cerca_google(client, stringa_ricerca, pagina_corrente, numero_pagine, data_limite)
        pagina_corrente += numero_pagine

        # se google non ha altri risultati è inutile continuare
        if not risultati:
            break

        for risultato in risultati:
            url = risultato.get("url")
            # evito duplicati che possono comparire tra pagine diverse
            if not url or url in url_visti:
                continue
            url_visti.add(url)

            articolo, motivo = analizza_articolo(url, data_limite)
            if articolo is None:
                print(f"Scartato ({motivo}): {url}")
                continue

            # il titolo estratto dalla pagina è più completo di quello di google, che è troncato
            titolo = articolo["titolo"] or risultato.get("title") or "senza titolo"

            # se due articoli hanno lo stesso titolo aggiungo un numero al nome del file
            nome_testo = nome_file(titolo, "txt")
            contatore = 2
            while nome_testo in file_usati:
                nome_testo = nome_file(f"{titolo} {contatore}", "txt")
                contatore += 1
            file_usati.add(nome_testo)

            with open(os.path.join(cartella_testi, nome_testo), "w", encoding="utf-8") as file:
                file.write(articolo["testo"])

            articoli.append({
                "posizione": risultato["posizione"],
                "titolo": titolo,
                "data_pubblicazione": articolo["data_pubblicazione"],
                "url": url,
                "descrizione": risultato.get("description"),
                "file_testo": os.path.join(nome_ricerca, nome_testo),
            })
            print(f"Salvato ({len(articoli)}/{numero_risultati}): {titolo}")

            if len(articoli) == numero_risultati:
                break

    if len(articoli) < numero_risultati:
        print(f"Trovati solo {len(articoli)} articoli validi su {numero_risultati} richiesti")

    # ordino gli articoli per posizione su google, dal primo risultato all'ultimo
    articoli.sort(key=lambda articolo: articolo["posizione"])

    percorso = os.path.join(cartella, f"{nome_ricerca}.csv")

    with open(percorso, "w", newline="", encoding="utf-8") as file:
        campi = ["posizione", "titolo", "data_pubblicazione", "url", "descrizione", "file_testo"]
        writer = csv.DictWriter(file, fieldnames=campi)
        writer.writeheader()
        writer.writerows(articoli)

    return percorso


def unisci_csv(percorsi_csv, nome_unito):
    # unisce i file csv indicati in un unico csv chiamato nome_unito, nella cartella di questo script,
    # senza duplicati (stesso url) e con il campo csv_origine che indica da quale file proviene ogni riga
    # restituisce il percorso del file creato; i csv originali non vengono modificati
    righe_unite = {}

    for percorso_csv in percorsi_csv:
        nome_origine = os.path.basename(percorso_csv)
        with open(percorso_csv, newline="", encoding="utf-8") as file:
            for riga in csv.DictReader(file):
                url = riga["url"]
                if url in righe_unite:
                    # articolo già presente da un altro csv: aggiungo solo il nome di questo file
                    righe_unite[url]["csv_origine"] += f"; {nome_origine}"
                else:
                    riga["csv_origine"] = nome_origine
                    righe_unite[url] = riga

    percorso = os.path.join(os.path.dirname(os.path.abspath(__file__)), nome_unito)

    with open(percorso, "w", newline="", encoding="utf-8") as file:
        campi = ["posizione", "titolo", "data_pubblicazione", "url", "descrizione", "file_testo", "csv_origine"]
        writer = csv.DictWriter(file, fieldnames=campi)
        writer.writeheader()
        # i dizionari mantengono l'ordine di inserimento: le righe restano nell'ordine dei csv originali
        writer.writerows(righe_unite.values())

    return percorso


if __name__ == "__main__":
    # percorso = scraping_google("utilizzo di tiktok da parte della criminalità organizzata in Italia", 100)
    # print(f"Risultati salvati in {percorso}")

    # il csv della criminalità organizzata esiste già: ne ricavo solo il percorso, senza rifare la ricerca
    cartella = os.path.dirname(os.path.abspath(__file__))
    percorsi_csv = [
        os.path.join(cartella, nome_file("utilizzo di tiktok da parte della criminalità organizzata in Italia", "csv")),
    ]

    percorso = scraping_google("utilizzo di tiktok da parte della camorra", 20)
    print(f"Risultati salvati in {percorso}")
    percorsi_csv.append(percorso)

    percorso = scraping_google("utilizzo di tiktok da parte di cosa nostra", 20)
    print(f"Risultati salvati in {percorso}")
    percorsi_csv.append(percorso)

    percorso = scraping_google("utilizzo di tiktok da parte della 'ndrangheta", 20)
    print(f"Risultati salvati in {percorso}")
    percorsi_csv.append(percorso)

    percorso = scraping_google("utilizzo di tiktok da parte della sacra corona unita", 20)
    print(f"Risultati salvati in {percorso}")
    percorsi_csv.append(percorso)

    percorso = unisci_csv(percorsi_csv, "articoli_uniti.csv")
    print(f"Csv unito salvato in {percorso}")
