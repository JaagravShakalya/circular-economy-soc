"""Cascade visualization: static snapshot and animated GIF."""

import os
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Patch

from src.network import make_network, assign_attributes
from src.simulate import initialize_loads, propagate_cascade
from src.config import ALPHA


def find_interesting_cascade(G, target_size=15, max_attempts=300, seed=0):
    """
    Find a single trip that produces a cascade of roughly target_size plants.
    Returns (initial_node, tripped_set, rounds_dict).
    """
    rng = np.random.default_rng(seed)
    nodes_list = list(G.nodes())
    best = None

    for _ in range(max_attempts):
        target = rng.choice(nodes_list)
        state = {"current_load": {n: G.nodes[n]["load"] for n in G.nodes()}}
        tripped, rounds = propagate_cascade(G, state, target, return_rounds=True)
        if len(tripped) == target_size:
            return target, tripped, rounds
        if best is None or abs(len(tripped) - target_size) < abs(len(best[1]) - target_size):
            best = (target, tripped, rounds)

    return best


def draw_cascade_state(G, pos, tripped_so_far, current_round_trips, ax):
    """Draw a single frame of the cascade."""
    healthy = [n for n in G.nodes() if n not in tripped_so_far]
    already_tripped = [n for n in tripped_so_far if n not in current_round_trips]
    new_trips = list(current_round_trips)

    # Edges (faded)
    nx.draw_networkx_edges(
        G, pos, ax=ax, edge_color="#bbb", width=0.6,
        arrows=True, arrowsize=8, arrowstyle="->",
        connectionstyle="arc3,rad=0.05",
    )
    # Highlight edges out of newly tripped plants
    if new_trips:
        cascade_edges = [(u, v) for u in new_trips for v in G.successors(u) if v not in tripped_so_far]
        if cascade_edges:
            nx.draw_networkx_edges(
                G, pos, edgelist=cascade_edges, ax=ax,
                edge_color="#ff6b35", width=1.8,
                arrows=True, arrowsize=12, arrowstyle="->",
                connectionstyle="arc3,rad=0.05",
            )

    # Healthy nodes (blue)
    if healthy:
        nx.draw_networkx_nodes(
            G, pos, nodelist=healthy, ax=ax,
            node_size=180, node_color="#4a90d9",
            edgecolors="black", linewidths=0.6,
        )
    # Already-tripped (dark red)
    if already_tripped:
        nx.draw_networkx_nodes(
            G, pos, nodelist=already_tripped, ax=ax,
            node_size=180, node_color="#7a1c1c",
            edgecolors="black", linewidths=0.6,
        )
    # Newly tripped this round (bright red)
    if new_trips:
        nx.draw_networkx_nodes(
            G, pos, nodelist=new_trips, ax=ax,
            node_size=260, node_color="#e63946",
            edgecolors="black", linewidths=1.2,
        )

    ax.axis("off")


def static_cascade_snapshot(
    save_path="figures/cascade_snapshot.png",
    N=80, topology="barabasi_albert", mean_degree=4, seed=42,
    target_size=12,
):
    """
    Make a single static figure showing a cascade in progress.
    Layout: 4 panels showing rounds 0, 1, 2, final.
    """
    G = make_network(N=N, topology=topology, mean_degree=mean_degree, seed=seed)
    G = assign_attributes(G, seed=seed)
    initialize_loads(G, alpha=ALPHA)

    initial, tripped, rounds = find_interesting_cascade(G, target_size=target_size, seed=1)
    max_round = max(rounds.values())
    print(f"Cascade: initial={initial}, total size={len(tripped)}, rounds={max_round}")

    pos = nx.spring_layout(G, seed=42, k=1.6 / (N ** 0.5))

    # Choose 4 representative rounds
    rounds_to_show = [0, max(1, max_round // 3), max(2, 2 * max_round // 3), max_round]
    rounds_to_show = sorted(set(rounds_to_show))

    fig, axes = plt.subplots(1, len(rounds_to_show), figsize=(4 * len(rounds_to_show), 4.2))
    if len(rounds_to_show) == 1:
        axes = [axes]

    for ax, r in zip(axes, rounds_to_show):
        tripped_so_far = {n for n, rr in rounds.items() if rr <= r}
        current = {n for n, rr in rounds.items() if rr == r}
        draw_cascade_state(G, pos, tripped_so_far, current, ax)
        ax.set_title(f"Round {r}\n({len(tripped_so_far)} tripped)", fontsize=11)

    legend_handles = [
        Patch(facecolor="#4a90d9", edgecolor="black", label="Healthy"),
        Patch(facecolor="#e63946", edgecolor="black", label="Newly tripped"),
        Patch(facecolor="#7a1c1c", edgecolor="black", label="Already tripped"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=3, fontsize=11, frameon=False, bbox_to_anchor=(0.5, -0.02))
    plt.suptitle(
        f"Cascade propagation ({topology.replace('_', '–')}, "
        f"$N$={N}, $\\langle k \\rangle$={mean_degree})",
        fontsize=13, y=1.02,
    )
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {save_path}")


def animated_cascade_gif(
    save_path="figures/cascade_animation.gif",
    N=120, topology="barabasi_albert", mean_degree=4, seed=42,
    n_cascades=4, fps=1.5,
):
    """
    Make an animated GIF showing several different cascades back-to-back,
    illustrating the variability in avalanche sizes (the SOC fingerprint).
    """
    G = make_network(N=N, topology=topology, mean_degree=mean_degree, seed=seed)
    G = assign_attributes(G, seed=seed)
    initialize_loads(G, alpha=ALPHA)

    pos = nx.spring_layout(G, seed=42, k=1.6 / (N ** 0.5))

    # Find n_cascades cascades of varied sizes
    target_sizes = [3, 8, 20, 45]  # small, medium, large, very large
    cascades = []  # list of (initial, tripped_set, rounds_dict)

    for i, target in enumerate(target_sizes[:n_cascades]):
        result = find_interesting_cascade(G, target_size=target, seed=10 + i)
        if result is not None:
            initial, tripped, rounds = result
            cascades.append((initial, tripped, rounds))
            print(f"Cascade {i+1}: initial={initial}, size={len(tripped)}, rounds={max(rounds.values())}")

    # Build the frame schedule: hold-start, cascade rounds, hold-end, then next cascade
    n_hold_start = 2
    n_hold_end = 3
    frame_schedule = []  # list of (cascade_idx, "type", round_num)

    for ci, (initial, tripped, rounds) in enumerate(cascades):
        max_round = max(rounds.values())
        for _ in range(n_hold_start):
            frame_schedule.append((ci, "start", 0))
        for r in range(max_round + 1):
            frame_schedule.append((ci, "round", r))
        for _ in range(n_hold_end):
            frame_schedule.append((ci, "end", max_round))

    fig, ax = plt.subplots(figsize=(8, 8))

    def animate(frame):
        ax.clear()
        ci, kind, r = frame_schedule[frame]
        initial, tripped, rounds = cascades[ci]
        max_round = max(rounds.values())

        if kind == "start":
            tripped_so_far = set()
            current = set()
            label = f"Cascade {ci+1}/{len(cascades)} — initial state"
        elif kind == "end":
            tripped_so_far = set(rounds.keys())
            current = set()
            label = f"Cascade {ci+1}/{len(cascades)} complete: {len(tripped)} of {N} plants tripped"
        else:
            tripped_so_far = {n for n, rr in rounds.items() if rr <= r}
            current = {n for n, rr in rounds.items() if rr == r}
            label = f"Cascade {ci+1}/{len(cascades)} — round {r}: {len(tripped_so_far)} tripped"

        draw_cascade_state(G, pos, tripped_so_far, current, ax)
        ax.set_title(label, fontsize=12)

    anim = animation.FuncAnimation(
        fig, animate, frames=len(frame_schedule),
        interval=int(1000 / fps), repeat=True,
    )
    anim.save(save_path, writer="pillow", fps=fps, dpi=100)
    plt.close(fig)
    print(f"Saved {save_path} ({len(frame_schedule)} frames)")

    def animate(frame):
        ax.clear()
        if frame == 0:
            tripped_so_far = set()
            current = set()
            label = "Initial state"
        elif frame > max_round + 1:
            tripped_so_far = set(rounds.keys())
            current = set()
            label = f"Cascade complete: {len(tripped)} plants tripped"
        else:
            r = frame - 1
            tripped_so_far = {n for n, rr in rounds.items() if rr <= r}
            current = {n for n, rr in rounds.items() if rr == r}
            label = f"Round {r}: {len(tripped_so_far)} tripped"

        draw_cascade_state(G, pos, tripped_so_far, current, ax)
        ax.set_title(label, fontsize=13)

    anim = animation.FuncAnimation(fig, animate, frames=n_frames, interval=1000 // fps, repeat=True)

    # Save as GIF using pillow writer
    anim.save(save_path, writer="pillow", fps=fps, dpi=100)
    plt.close(fig)
    print(f"Saved {save_path}")