"""Network generation for the circular economy SOC model."""

import networkx as nx
import numpy as np


def make_network(N, topology, mean_degree, seed=None):
    """
    Generate a directed graph of N plants with the specified topology.

    Parameters
    ----------
    N : int
        Number of plants (nodes).
    topology : str
        One of "erdos_renyi", "barabasi_albert", "modular".
    mean_degree : float
        Target mean degree per node.
    seed : int or None
        Random seed for reproducibility.

    Returns
    -------
    G : networkx.DiGraph
        Directed graph representing the symbiosis network.
    """
    rng = np.random.default_rng(seed)

    if topology == "erdos_renyi":
        # p chosen so that expected out-degree = mean_degree
        p = mean_degree / (N - 1)
        G = nx.erdos_renyi_graph(N, p, seed=seed, directed=True)

    elif topology == "barabasi_albert":
        # BA is undirected; m = mean_degree / 2 gives ~mean_degree total degree
        m = max(1, int(round(mean_degree / 2)))
        G_und = nx.barabasi_albert_graph(N, m, seed=seed)
        # Orient each edge randomly to make it directed
        G = nx.DiGraph()
        G.add_nodes_from(G_und.nodes())
        for u, v in G_und.edges():
            if rng.random() < 0.5:
                G.add_edge(u, v)
            else:
                G.add_edge(v, u)

    elif topology == "modular":
        # Build communities, dense within, sparse between
        n_communities = 4
        sizes = [N // n_communities] * n_communities
        sizes[-1] += N - sum(sizes)  # absorb remainder
        p_in = mean_degree / (sizes[0] - 1) * 0.8
        p_out = mean_degree / (N - 1) * 0.2
        p_matrix = [[p_in if i == j else p_out
                     for j in range(n_communities)]
                    for i in range(n_communities)]
        G_und = nx.stochastic_block_model(sizes, p_matrix, seed=seed)
        G = nx.DiGraph()
        G.add_nodes_from(G_und.nodes())
        for u, v in G_und.edges():
            if rng.random() < 0.5:
                G.add_edge(u, v)
            else:
                G.add_edge(v, u)

    else:
        raise ValueError(f"Unknown topology: {topology}")

    return G


def assign_attributes(G, threshold=0.5, q_low=0.5, q_high=1.5, seed=None):
    """
    Assign nominal capacities and thresholds to nodes,
    and normalized weights to edges.

    Each node gets:
        - Q_nominal : float, drawn uniformly from [q_low, q_high]
        - threshold : float, the failure threshold (default 0.5)

    Each edge (u -> v) gets:
        - weight : float, fraction of u's output sent to v
        Outgoing weights from each node sum to 1.

    Modifies G in place and also returns it.
    """
    rng = np.random.default_rng(seed)

    # Node attributes
    for node in G.nodes():
        G.nodes[node]["Q_nominal"] = float(rng.uniform(q_low, q_high))
        G.nodes[node]["threshold"] = threshold

    # Edge weights — normalize per source node
    for node in G.nodes():
        out_edges = list(G.out_edges(node))
        if not out_edges:
            continue
        raw = rng.uniform(0.5, 1.5, size=len(out_edges))
        normalized = raw / raw.sum()
        for (u, v), w in zip(out_edges, normalized):
            G.edges[u, v]["weight"] = float(w)

    return G


import matplotlib.pyplot as plt


def visualize_network(G, path, title=None):
    """
    Save a PNG visualization of the network.
    Node size scales with Q_nominal, edge width with weight.
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    pos = nx.spring_layout(G, seed=42, k=1.5 / (G.number_of_nodes() ** 0.5))

    node_sizes = [300 * G.nodes[n].get("Q_nominal", 1.0) for n in G.nodes()]
    edge_widths = [3 * G.edges[u, v].get("weight", 0.5) for u, v in G.edges()]

    nx.draw_networkx_nodes(
        G, pos, node_size=node_sizes,
        node_color="#4a90d9", edgecolors="black", linewidths=0.8, ax=ax,
    )
    nx.draw_networkx_edges(
        G, pos, width=edge_widths, edge_color="#666",
        arrows=True, arrowsize=12, arrowstyle="->",
        connectionstyle="arc3,rad=0.1", ax=ax,
    )
    nx.draw_networkx_labels(G, pos, font_size=8, ax=ax)

    if title:
        ax.set_title(title, fontsize=14)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)