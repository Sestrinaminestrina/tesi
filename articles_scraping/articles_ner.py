import os

import spacy


# Carica il modello italiano di spacy, scaricandolo se non è installato.
# Restituisce l'oggetto nlp di spacy.
def carica_modello(nome_modello="it_core_news_md"):
    try:
        return spacy.load(nome_modello)
    except OSError:
        spacy.cli.download(nome_modello)
        return spacy.load(nome_modello)


# Estrae le entità nominate di tipo persona dal testo e le stampa.
# Restituisce la lista dei nomi di persona trovati (senza duplicati).
def estrai_persone(testo, nlp):
    doc = nlp(testo)

    nomi_persona = []
    for entita in doc.ents:
        # Nei modelli italiani di spacy le persone hanno etichetta "PER"
        if entita.label_ == "PER" and entita.text not in nomi_persona:
            nomi_persona.append(entita.text)

    for nome in nomi_persona:
        print(nome)
    return nomi_persona


# Punto di ingresso: legge un articolo da file ed estrae i nomi di persona.
# Non restituisce nulla.
def main():
    nlp = carica_modello()
    # Percorso assoluto costruito a partire dalla cartella di questo script,
    # così funziona indipendentemente dalla cartella da cui lo si avvia
    cartella_script = os.path.dirname(os.path.abspath(__file__))
    percorso_file = os.path.join(
        cartella_script,
        "utilizzo_di_tiktok_da_parte_della_criminalità_organizzata_in_italia",
        "la_criminalità_giovanile_fra_rappresentazione_e_realtà_eurispes.txt")
    with open(percorso_file, "r", encoding="utf-8") as file:
        testo = file.read()
    estrai_persone(testo, nlp)


if __name__ == "__main__":
    main()
