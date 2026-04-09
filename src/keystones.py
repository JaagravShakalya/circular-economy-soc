"""Dynamic keystone analysis: which plants participate most in cascades?"""

import os
import numpy as np
import networkx as nx
from collections import Counter

from src.network import make_network, assign_attributes
from src.simulate import run_simulation
from src.config import ALPHA, BURN_IN


def compute_keystone_scores(
    topology="barabasi_albert", mean_degree=4, N=300, seed=42, T=200000,
):
    """
    Run a long simulation and compute the avalanche participation frequency
    for each plant. A plant's keystone score = (#avalanches it appears in) / (total #avalanches).
    """
    G = make_network(N=N, topology=topology, mean_degree=mean_degree, seed=seed)
    G = assign_attributes(G, seed=seed)

    sizes, participants = run_simulation(
        G, T=T, sigma=0.0, mu=0.0,
        burn_in=BURN_IN, seed=seed, alpha=ALPHA,
        record_participants=True,
    )

    # Count participation per node
    counter = Counter()
    n_avalanches = 0
    for sz, parts in zip(sizes, participants):
        if sz > 0:
            n_avalanches += 1
            for node in parts:
                counter[node] += 1

    # Normalize to frequencies
    dynamic = {n: counter.get(n, 0) / max(1, n_avalanches) for n in G.nodes()}
    return G, dynamic, n_avalanches


def compute_static_centralities(G):
    """Compute three standard static centrality measures."""
    return {
        "in_degree": dict(G.in_degree()),
        "betweenness": nx.betweenness_centrality(G),
        "pagerank": nx.pagerank(G),
    }