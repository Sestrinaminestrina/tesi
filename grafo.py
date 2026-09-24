import csv

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


def visualizza_grafo(grafo):
    # disegna il grafo con matplotlib: spessore dell'arco proporzionale al numero di commenti
    # non restituisce nulla, apre una finestra con l'immagine del grafo
    posizioni = nx.spring_layout(grafo, seed=42)

    pesi = [grafo[u][v]["weight"] for u, v in grafo.edges()]

    nx.draw_networkx_nodes(grafo, posizioni, node_size=300, node_color="skyblue")
    nx.draw_networkx_labels(grafo, posizioni, font_size=8)
    nx.draw_networkx_edges(grafo, posizioni, width=pesi, edge_color="gray", arrows=True, arrowsize=15)

    plt.axis("off")
    plt.show()


if __name__ == "__main__":
    grafo = crea_grafo_commenti("risultati_tiktok.csv", "risultati_commenti.csv")
    print(f"grafo creato: {grafo.number_of_nodes()} nodi, {grafo.number_of_edges()} archi")

    visualizza_grafo(grafo)
