"""Core simulation: dynamics and avalanche propagation."""

import numpy as np
import networkx as nx


def compute_realized_output(G, state):
    """
    Compute each plant's realized output using Liebig's law of the minimum.

    A plant's realized output is limited by the scarcest of its inputs.
    For each input stream from supplier u, the "supply ratio" is
    (actual flow received) / (expected flow). The plant's realized
    fraction = min over all input streams of these ratios.

    Plants with no suppliers run at their effective capacity (they're
    "source" plants — they import raw materials from outside the system).

    Tripped plants always have output 0.

    Parameters
    ----------
    G : networkx.DiGraph
        Network with node attribute 'Q_nominal' and edge attribute 'weight'.
    state : dict
        {
            'tripped': set of tripped node ids,
            'effective_capacity': dict {node: current effective Q},
        }

    Returns
    -------
    realized : dict
        {node: realized output (float)}
    """
    tripped = state["tripped"]
    eff_cap = state["effective_capacity"]
    realized = {}

    # First pass: source plants (no incoming edges) run at their effective cap
    for node in G.nodes():
        if node in tripped:
            realized[node] = 0.0
            continue
        if G.in_degree(node) == 0:
            realized[node] = eff_cap[node]

    # Iterative pass for the rest: a plant's output depends on its suppliers'
    # outputs. We iterate until convergence (or max_iter for safety).
    max_iter = 50
    for _ in range(max_iter):
        changed = False
        for node in G.nodes():
            if node in tripped or G.in_degree(node) == 0:
                continue

            # For each supplier u, expected flow = u's Q_nominal * weight(u->node)
            # Actual flow = u's realized output * weight(u->node)
            # Supply ratio = actual / expected = realized[u] / Q_nominal[u]
            # (assuming the weight cancels)
            ratios = []
            for u in G.predecessors(node):
                if u not in realized:
                    continue  # not computed yet
                q_nom_u = G.nodes[u]["Q_nominal"]
                if q_nom_u > 0:
                    ratios.append(realized[u] / q_nom_u)
                else:
                    ratios.append(0.0)

            if len(ratios) < G.in_degree(node):
                continue  # wait for all suppliers to be computed

            # Liebig: scarcest input sets the pace
            supply_fraction = min(ratios) if ratios else 1.0
            new_output = eff_cap[node] * supply_fraction

            if node not in realized or abs(realized[node] - new_output) > 1e-9:
                realized[node] = new_output
                changed = True

        if not changed:
            break

    # Any node still missing (cycles) gets 0
    for node in G.nodes():
        if node not in realized:
            realized[node] = 0.0

    return realized


def apply_noise(G, state, sigma, rng):
    """
    Perturb each non-tripped plant's effective capacity by a Gaussian factor.

    Q_eff(t) = Q_nominal * (1 + epsilon), epsilon ~ N(0, sigma)
    Capacities are clipped to [0, 2*Q_nominal] to avoid runaway values.

    Modifies state['effective_capacity'] in place.
    """
    for node in G.nodes():
        if node in state["tripped"]:
            state["effective_capacity"][node] = 0.0
            continue
        q_nom = G.nodes[node]["Q_nominal"]
        epsilon = rng.normal(0, sigma)
        new_cap = q_nom * (1 + epsilon)
        new_cap = max(0.0, min(new_cap, 2 * q_nom))
        state["effective_capacity"][node] = new_cap


def propagate_cascade(G, state):
    """
    Iteratively trip plants whose realized output falls below their threshold.

    Starting from the current state, repeatedly:
      1. Compute realized outputs.
      2. Find plants whose realized/Q_nominal < threshold.
      3. Add them to the tripped set.
      4. Repeat until no new trips occur.

    Returns
    -------
    newly_tripped : set
        The set of plants that tripped during this cascade
        (the avalanche; size = len(newly_tripped)).
    """
    newly_tripped = set()
    max_iter = 100

    for _ in range(max_iter):
        realized = compute_realized_output(G, state)
        trips_this_round = set()

        for node in G.nodes():
            if node in state["tripped"]:
                continue
            q_nom = G.nodes[node]["Q_nominal"]
            if q_nom <= 0:
                continue
            fraction = realized[node] / q_nom
            if fraction < G.nodes[node]["threshold"]:
                trips_this_round.add(node)

        if not trips_this_round:
            break

        state["tripped"].update(trips_this_round)
        newly_tripped.update(trips_this_round)
        # Tripped plants have effective capacity 0
        for node in trips_this_round:
            state["effective_capacity"][node] = 0.0

    return newly_tripped


def repair_step(G, state, mu, rng):
    """
    Each tripped plant comes back online with probability mu.
    Repaired plants resume at their nominal capacity.
    """
    repaired = set()
    for node in list(state["tripped"]):
        if rng.random() < mu:
            repaired.add(node)
    state["tripped"] -= repaired
    for node in repaired:
        state["effective_capacity"][node] = G.nodes[node]["Q_nominal"]


def run_simulation(G, T, sigma, mu, burn_in=0, seed=None, record_participants=False):
    """
    Run the full simulation for T timesteps.

    Each timestep:
      1. Apply noise to non-tripped plants.
      2. Propagate any cascade triggered by the noise.
      3. Record the avalanche size.
      4. Apply repair.

    Parameters
    ----------
    G : networkx.DiGraph
        Network with attributes assigned.
    T : int
        Total timesteps.
    sigma : float
        Noise amplitude.
    mu : float
        Repair probability per timestep.
    burn_in : int
        Number of initial timesteps to discard before recording.
    seed : int or None
        Random seed.
    record_participants : bool
        If True, also return per-avalanche participant sets (for keystone analysis).

    Returns
    -------
    avalanche_sizes : list of int
        Length (T - burn_in). Most entries will be 0 (no avalanche that step).
    participants : list of set, optional
        Only if record_participants=True.
    """
    rng = np.random.default_rng(seed)

    state = {
        "tripped": set(),
        "effective_capacity": {n: G.nodes[n]["Q_nominal"] for n in G.nodes()},
    }

    avalanche_sizes = []
    participants = []

    for t in range(T):
        apply_noise(G, state, sigma, rng)
        avalanche = propagate_cascade(G, state)
        repair_step(G, state, mu, rng)

        if t >= burn_in:
            avalanche_sizes.append(len(avalanche))
            if record_participants:
                participants.append(avalanche)

    if record_participants:
        return avalanche_sizes, participants
    return avalanche_sizes