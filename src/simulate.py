"""Core simulation: Motter-Lai style cascading failures on a directed network.

Each plant has a load (mass throughput) and a capacity = (1+alpha)*load.
A small perturbation reduces one plant's capacity below its load, tripping it.
The tripped plant's load redistributes to downstream neighbors. If any neighbor's
new load exceeds its capacity, it also trips, and so on until the cascade ends.
"""

import numpy as np
import networkx as nx


def initialize_loads(G, alpha=0.3):
    """
    Compute the steady-state load on each plant from the network topology.
    Load on a plant = sum of weighted outflows from its suppliers,
    plus a base load if it's a source.
    Capacity = (1 + alpha) * load.
    """
    # Iterative load computation: start with sources, propagate downstream
    load = {n: 0.0 for n in G.nodes()}
    for n in G.nodes():
        if G.in_degree(n) == 0:
            load[n] = G.nodes[n].get("Q_nominal", 1.0)

    # Iterate to propagate loads through the network
    for _ in range(50):
        new_load = dict(load)
        for n in G.nodes():
            if G.in_degree(n) == 0:
                continue
            incoming = 0.0
            for u in G.predecessors(n):
                w = G.edges[u, n].get("weight", 1.0)
                incoming += w * load[u]
            base = G.nodes[n].get("Q_nominal", 1.0) * 0.3  # base load even with no suppliers
            new_load[n] = base + incoming
        if all(abs(new_load[n] - load[n]) < 1e-9 for n in G.nodes()):
            load = new_load
            break
        load = new_load

    for n in G.nodes():
        G.nodes[n]["load"] = load[n]
        G.nodes[n]["capacity"] = (1 + alpha) * load[n]


def propagate_cascade(G, state, initial_trip, return_rounds=False):
    """
    Cascade after one plant is tripped. Redistribute its load to downstream
    neighbors; any neighbor whose new load exceeds capacity also trips.
    Continues until no more trips.

    If return_rounds is True, also return a dict {node: round_number}
    indicating which propagation round each plant tripped in
    (initial trip = round 0).
    """
    tripped = set([initial_trip])
    rounds = {initial_trip: 0}
    current_load = dict(state["current_load"])
    queue = [(initial_trip, 0)]

    while queue:
        node, r = queue.pop(0)
        successors = list(G.successors(node))
        if not successors:
            continue

        total_w = sum(G.edges[node, v].get("weight", 1.0) for v in successors)
        if total_w == 0:
            continue
        load_to_distribute = current_load[node]

        for v in successors:
            if v in tripped:
                continue
            w = G.edges[node, v].get("weight", 1.0)
            extra = load_to_distribute * (w / total_w)
            current_load[v] += extra
            if current_load[v] > G.nodes[v]["capacity"]:
                tripped.add(v)
                rounds[v] = r + 1
                queue.append((v, r + 1))

    state["current_load"] = current_load
    if return_rounds:
        return tripped, rounds
    return tripped


def run_simulation(G, T, sigma, mu, burn_in=0, seed=None, record_participants=False, alpha=0.3):
    """
    Run T timesteps of the cascading-failure model.
    Each timestep:
      1. Pick a random plant and trip it (single-site drive).
      2. Cascade.
      3. Record avalanche size.
      4. Reset (plants recover instantly — this is the standard SOC protocol).
    
    Parameters
    ----------
    sigma : float
        UNUSED in this model. Kept for API compatibility. The "noise"
        is the random choice of which plant to trip each timestep.
    mu : float
        UNUSED. Kept for API compatibility.
    """
    rng = np.random.default_rng(seed)
    initialize_loads(G, alpha=alpha)

    base_load = {n: G.nodes[n]["load"] for n in G.nodes()}
    state = {"current_load": dict(base_load)}

    avalanche_sizes = []
    participants = []

    nodes_list = list(G.nodes())

    for t in range(T):
        # Reset loads to baseline
        state["current_load"] = dict(base_load)

        # Pick a random plant to trip
        target = rng.choice(nodes_list)

        # Cascade
        tripped = propagate_cascade(G, state, target)

        if t >= burn_in:
            avalanche_sizes.append(len(tripped))
            if record_participants:
                participants.append(tripped)

    if record_participants:
        return avalanche_sizes, participants
    return avalanche_sizes


# Kept for compatibility but no longer used internally
def compute_realized_output(G, state):
    return {n: G.nodes[n].get("load", 1.0) for n in G.nodes()}

def apply_noise(G, state, sigma, rng):
    pass

def repair_step(G, state, mu, rng):
    pass