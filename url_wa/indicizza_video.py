import re
import sys
from numbers_parser import Document

FILE_INPUT = "/Users/macdiisabella/Documents/tesi_ravveduto/dati_familiarizzazione/analisi_profili_completi.numbers"
FILE_OUTPUT = "/Users/macdiisabella/Documents/tesi_ravveduto/dati_familiarizzazione/indice_video_tiktok.numbers"

# url di un contenuto tiktok (video o post foto) oppure link breve vm.tiktok.com;
# la query string si ferma al primo carattere non valido, così gli url
# incollati uno dopo l'altro con "/" vengono separati correttamente
REGEX_VIDEO = re.compile(
    r"https?://(?:www\.)?tiktok\.com/@[\w.\-]+/(?:video|photo)/(\d+)(?:\?[\w=&\-.]*)?"
    r"|https?://vm\.tiktok\.com/(\w+)/?"
)


def estrai_video(testo):
    """Trova gli url dei video tiktok in un testo.
    Restituisce una lista di coppie (url, id_contenuto) nell'ordine in cui compaiono."""
    risultati = []
    for trovato in REGEX_VIDEO.finditer(testo):
        id_contenuto = trovato.group(1) or trovato.group(2)
        risultati.append((trovato.group(0), id_contenuto))
    return risultati


def indicizza_righe(righe):
    """Scorre le righe della tabella (intestazione esclusa) e assegna a ogni url video
    l'indice nomeprofilo_n. Restituisce la lista di coppie [url, indice]."""
    intestazione = righe[0]
    col_profilo = intestazione.index("profilo")
    col_url_profilo = intestazione.index("url profilo")
    indice_finale = []
    for riga in righe[1:]:
        profilo = riga[col_profilo]
        if not profilo:
            continue
        visti = set()
        n = 0
        # le colonne vengono lette da sinistra a destra, così n segue l'ordine nella riga
        for col, valore in enumerate(riga):
            if col == col_url_profilo or not isinstance(valore, str):
                continue
            for url, id_contenuto in estrai_video(valore):
                # lo stesso video citato più volte nella riga riceve un solo indice
                if id_contenuto in visti:
                    continue
                visti.add(id_contenuto)
                n += 1
                indice_finale.append([url, f"{profilo.strip()}_{n}"])
    return indice_finale


def salva_numbers(coppie, percorso):
    """Crea un file numbers con le colonne 'url video' e 'indice'. Non restituisce nulla."""
    doc = Document(num_header_rows=1, num_header_cols=0)
    tabella = doc.sheets[0].tables[0]
    tabella.write(0, 0, "url video")
    tabella.write(0, 1, "indice")
    for i, (url, indice) in enumerate(coppie, start=1):
        tabella.write(i, 0, url)
        tabella.write(i, 1, indice)
    # la tabella di default ha colonne vuote in più: si tengono solo le due usate
    tabella.delete_column(tabella.num_cols - 2, start_col=2)
    doc.save(percorso)


if __name__ == "__main__":
    file_input = sys.argv[1] if len(sys.argv) > 1 else FILE_INPUT
    file_output = sys.argv[2] if len(sys.argv) > 2 else FILE_OUTPUT
    tabella = Document(file_input).sheets[0].tables[0]
    coppie = indicizza_righe(tabella.rows(values_only=True))
    salva_numbers(coppie, file_output)
    print(f"{len(coppie)} url indicizzati in {file_output}")
