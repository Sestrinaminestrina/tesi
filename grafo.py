import csv
import math

import matplotlib.pyplot as plt
import networkx as nx


def carica_righe_csv(percorso_file):
    # legge un file csv e restituisce le righe come lista di dizionari
    with open(percorso_file, newline="", encoding="utf-8") as file_csv:
        return list(csv.DictReader(file_csv))


def crea_grafo_commenti(percorso_video, percorso_commenti):
    # costruisce un grafo orientato: nodi = autori, archi = commenti da un autore all'autore del video commentato
    # il peso di un arco conta quanti commenti un utente ha lasciato a un altro (self loop se commenta i propri video)
    # restituisce un oggetto networkx.DiGraph
    video = carica_righe_csv(percorso_video)
    commenti = carica_righe_csv(percorso_commenti)

    # mappa ogni id video al suo autore, per risalire al "destinatario" di ogni commento
    autore_per_id_video = {v["id"]: v["autore"] for v in video}

    grafo = nx.DiGraph()

    for c in commenti:
        autore_commento = c.get("autore")
        autore_video = autore_per_id_video.get(c.get("id_video"))

        # scarta il commento se manca l'autore o non troviamo il video di origine corrispondente
        if not autore_commento or not autore_video:
            continue

        if grafo.has_edge(autore_commento, autore_video):
            grafo[autore_commento][autore_video]["weight"] += 1
        else:
            grafo.add_edge(autore_commento, autore_video, weight=1)

    return grafo


def layout_a_componenti(grafo, k=0.8, seed=42, spaziatura=2.5):
    # calcola la posizione dei nodi disponendo ogni componente connesso in una cella separata di una griglia
    # cosi gli archi di componenti diversi non si intersecano mai tra loro
    # restituisce un dizionario {nodo: (x, y)}, nello stesso formato di nx.spring_layout
    componenti = list(nx.weakly_connected_components(grafo))
    numero_colonne = math.ceil(math.sqrt(len(componenti)))

    posizioni = {}

    for indice, nodi_componente in enumerate(componenti):
        sottografo = grafo.subgraph(nodi_componente)

        # layout del singolo componente, calcolato in isolamento e centrato sull'origine
        posizioni_locali = nx.spring_layout(sottografo, k=k, seed=seed)

        # sposta il componente nella sua cella della griglia, cosi non si sovrappone alle altre
        riga = indice // numero_colonne
        colonna = indice % numero_colonne
        offset_x = colonna * spaziatura
        offset_y = riga * spaziatura

        for nodo, (x, y) in posizioni_locali.items():
            posizioni[nodo] = (x + offset_x, y + offset_y)

    return posizioni


def visualizza_grafo(grafo):
    # disegna il grafo con matplotlib: spessore dell'arco proporzionale al numero di commenti
    # non restituisce nulla, apre una finestra con l'immagine del grafo
    posizioni = layout_a_componenti(grafo, k=0.8, seed=42)

    pesi = [grafo[u][v]["weight"] for u, v in grafo.edges()]

    # figura piu' grande del default, per dare piu' spazio ai nodi ed evitare che risultino ammassati
    plt.figure(figsize=(10, 8))

    nx.draw_networkx_nodes(grafo, posizioni, node_size=300, node_color="skyblue")
    nx.draw_networkx_labels(grafo, posizioni, font_size=8)
    nx.draw_networkx_edges(grafo, posizioni, width=pesi, edge_color="gray", arrows=True, arrowsize=15)

    plt.axis("off")
    plt.show()


if __name__ == "__main__":
    grafo = crea_grafo_commenti("risultati_tiktok.csv", "risultati_commenti.csv")
    print(f"grafo creato: {grafo.number_of_nodes()} nodi, {grafo.number_of_edges()} archi")

    visualizza_grafo(grafo)
