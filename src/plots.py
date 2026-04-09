"""Plotting functions for the report figures."""

import matplotlib.pyplot as plt
import numpy as np
from src.analysis import load_run, fit_power_law, log_binned_pdf


TOPOLOGY_LABELS = {
    "erdos_renyi": "Erdős–Rényi",
    "barabasi_albert": "Barabási–Albert",
    "modular": "Modular",
}
TOPOLOGY_COLORS = {
    "erdos_renyi": "#1f77b4",
    "barabasi_albert": "#d62728",
    "modular": "#2ca02c",
}


def figure1_topology_comparison(mean_degree=4, seed=42, save_path="figures/fig1_topology_comparison.png"):
    """Compare avalanche distributions across the three topologies at fixed k."""
    fig, ax = plt.subplots(figsize=(7, 5))

    for topo in ["erdos_renyi", "barabasi_albert", "modular"]:
        sizes = load_run(topo, mean_degree, seed)
        nonzero = sizes[sizes > 0]
        if len(nonzero) == 0:
            continue

        centers, pdf = log_binned_pdf(nonzero)
        ax.loglog(
            centers, pdf, "o-", markersize=6,
            color=TOPOLOGY_COLORS[topo],
            label=f"{TOPOLOGY_LABELS[topo]} (N={len(nonzero)})",
        )

    ax.set_xlabel("Avalanche size $s$", fontsize=12)
    ax.set_ylabel("$P(s)$", fontsize=12)
    ax.set_title(f"Avalanche size distribution by topology ($\\langle k \\rangle$ = {mean_degree})")
    ax.legend(fontsize=10)
    ax.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {save_path}")


def figure2_exponent_vs_connectivity(save_path="figures/fig2_exponent_vs_connectivity.png"):
    """Plot fitted tau vs mean degree for each topology, with error bars."""
    from src.sweep import TOPOLOGIES, MEAN_DEGREES, SEEDS

    fig, ax = plt.subplots(figsize=(8, 5))

    for topo in TOPOLOGIES:
        means = []
        stds = []
        for k in MEAN_DEGREES:
            taus = []
            for seed in SEEDS:
                sizes = load_run(topo, k, seed)
                fit = fit_power_law(sizes)
                if fit is not None and fit["R_exp"] > 0:
                    taus.append(fit["tau"])
            if taus:
                means.append(np.mean(taus))
                stds.append(np.std(taus))
            else:
                means.append(np.nan)
                stds.append(0)

        ax.errorbar(
            MEAN_DEGREES, means, yerr=stds,
            marker="o", markersize=8, capsize=4, linewidth=2,
            color=TOPOLOGY_COLORS[topo],
            label=TOPOLOGY_LABELS[topo],
        )

    ax.set_xlabel("Mean degree $\\langle k \\rangle$", fontsize=12)
    ax.set_ylabel("Power-law exponent $\\tau$", fontsize=12)
    ax.set_title("SOC exponent as a function of network connectivity")
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {save_path}")


def figure3_subcritical_to_supercritical(
    topology="barabasi_albert", seed=42,
    save_path="figures/fig3_subcritical_critical_supercritical.png"
):
    """Show how distribution shape changes with connectivity (the SOC transition)."""
    fig, ax = plt.subplots(figsize=(7, 5))

    ks_to_show = [2, 4, 8]
    colors = ["#3690c0", "#d62728", "#fdae6b"]
    labels = ["sparse", "intermediate", "dense"]

    for k, color, label in zip(ks_to_show, colors, labels):
        sizes = load_run(topology, k, seed)
        nonzero = sizes[sizes > 0]
        if len(nonzero) == 0:
            continue
        centers, pdf = log_binned_pdf(nonzero)
        ax.loglog(
            centers, pdf, "o-", markersize=6,
            color=color,
            label=f"$\\langle k \\rangle$ = {k} ({label})",
        )

    ax.set_xlabel("Avalanche size $s$", fontsize=12)
    ax.set_ylabel("$P(s)$", fontsize=12)
    ax.set_title(f"Connectivity-driven transition ({TOPOLOGY_LABELS[topology]})")
    ax.legend(fontsize=11)
    ax.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {save_path}")
