import networkx as nx
from networkx.algorithms import approximation
import tqdm


def deduplicate(distance_matrix, thres):
    # The larger the value, the more similar.
    # Find the maximum disjoint set of dissimilarities.
    n = distance_matrix
    G = nx.Graph()

    for i in tqdm.tqdm(range(n)):
        G.add_node(i)
        for j in range(n):
            if distance_matrix[i, j] < thres:
                G.add_edge(i, j)

    cl = list(approximation.clique.max_clique(G))
    return cl
