"""Connectivity sweep: run the simulation across topologies and mean degrees."""

import os
import numpy as np
from tqdm import tqdm

from src.network import make_network, assign_attributes
from src.simulate import run_simulation
from src.config import ALPHA, N, T, BURN_IN


TOPOLOGIES = ["erdos_renyi", "barabasi_albert", "modular"]
MEAN_DEGREES = [2, 3, 4, 6, 8]
SEEDS = [42, 123, 999]
DATA_DIR = "data/runs"


def run_one(topology, mean_degree, seed):
    """Run a single simulation and return the avalanche size array."""
    G = make_network(N=N, topology=topology, mean_degree=mean_degree, seed=seed)
    G = assign_attributes(G, seed=seed)
    sizes = run_simulation(
        G, T=T, sigma=0.0, mu=0.0,
        burn_in=BURN_IN, seed=seed, alpha=ALPHA,
    )
    return np.array(sizes)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    combos = [
        (topo, k, seed)
        for topo in TOPOLOGIES
        for k in MEAN_DEGREES
        for seed in SEEDS
    ]

    print(f"Running {len(combos)} simulations...")
    for topo, k, seed in tqdm(combos):
        path = f"{DATA_DIR}/{topo}_k{k}_seed{seed}.npy"
        if os.path.exists(path):
            continue  # skip if already computed
        sizes = run_one(topo, k, seed)
        np.save(path, sizes)

    print("Done.")


def finite_size_sweep(topology="barabasi_albert", mean_degree=4, sizes=(50, 100, 200, 400), seed=42):
    """Run the simulation at multiple system sizes for finite-size scaling."""
    os.makedirs(DATA_DIR, exist_ok=True)
    for N_size in sizes:
        path = f"{DATA_DIR}/{topology}_k{mean_degree}_N{N_size}_seed{seed}.npy"
        if os.path.exists(path):
            print(f"Skipping {path} (exists)")
            continue
        print(f"Running N={N_size}...")
        G = make_network(N=N_size, topology=topology, mean_degree=mean_degree, seed=seed)
        G = assign_attributes(G, seed=seed)
        avalanches = run_simulation(
            G, T=T, sigma=0.0, mu=0.0,
            burn_in=BURN_IN, seed=seed, alpha=ALPHA,
        )
        np.save(path, np.array(avalanches))
        print(f"  saved {path}")


if __name__ == "__main__":
    main()
    print("\nFinite-size scaling sweep:")
    finite_size_sweep()