# Self-Organized Criticality in Circular Economy Networks

> Course project for **CLL798 — Complexity Science in Chemical Industry**, IIT Delhi (April 2026)
> **Jaagrav Shakalya** · Entry No. 2023CH10222

<p align="center">
  <img src="figures/cascade_animation.gif" alt="Cascade animation" width="600"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12-blue" alt="Python"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License"/>
  <img src="https://img.shields.io/badge/status-complete-brightgreen" alt="Status"/>
  <img src="https://img.shields.io/badge/SOC-confirmed-orange" alt="SOC"/>
</p>

---

## Overview

A **circular economy** is an industrial system in which factories are tightly coupled together: one plant's waste becomes another plant's raw material, with nothing thrown away. The classic real-world example is the [Kalundborg eco-industrial park](https://en.wikipedia.org/wiki/Kalundborg_Eco-industrial_Park) in Denmark, where about thirty plants — a power station, an oil refinery, plasterboard and pharmaceutical factories, water utilities, and local farms — exchange steam, gypsum, fly ash, sulfur, and biomass through a dense network of pipes and conveyor belts. The arrangement is celebrated as efficient and sustainable.

But the same coupling that makes such systems efficient also makes them **fragile in an interesting way**. Because every plant depends on its neighbours, a small disruption at one site can cascade through the network: plant A trips, starving plant B of feedstock, which then trips and starves plants C and D, and so on. This project asks a specific question about that fragility:

> **Do circular-economy networks self-organize into a critical state, and what does that imply about their vulnerability?**

The notion of a "critical state" comes from physics. A system is **self-organized critical (SOC)** if, without any external tuning, it settles into a regime where small perturbations occasionally trigger cascades of every possible size — from tiny single-plant trips to system-spanning blackouts — with the cascade-size distribution following a power law. SOC is the same statistical signature seen in earthquake magnitudes (Gutenberg–Richter), neuronal avalanches in brain tissue, forest fires, and the Bak–Tang–Wiesenfeld sandpile that started the field in 1987. The hypothesis here is that an industrial symbiosis network is just another flavour of the same phenomenon.

---

## Approach

The project models a circular-economy network as a directed graph and runs an agent-based cascading-failure simulation on it (the **Motter–Lai model**, a standard tool in the cascading-failure literature). Each plant has a baseline load and a capacity slightly above its load. At every timestep:

1. One randomly chosen plant is perturbed below its capacity and trips
2. Its load redistributes to downstream neighbours along the edges of the network
3. Any neighbour now overloaded also trips, recursively, until the cascade resolves
4. The size of the cascade is recorded

The simulation is run across three different network topologies — **Erdős–Rényi** (random), **Barabási–Albert** (scale-free, the topology that real industrial networks resemble most), and **modular** (community-structured) — and across a range of mean degrees, to ask how the network's structural properties influence the cascade statistics.

---

## Main claims

### Claim 1 — These networks really are self-organized critical

The avalanche-size distribution follows a clean power law with exponent **τ ≈ 2** across all topologies tested. The small-avalanche behaviour is universal across system sizes (finite-size scaling holds), and the power law is overwhelmingly preferred over an exponential alternative (likelihood ratio R ≈ 8000, p < 10⁻⁴). This means circular-economy networks have an *intrinsic* statistical vulnerability to scale-free cascades that **cannot be optimized away** — it's a structural property, not a design flaw.

### Claim 2 — Standard centrality measures miss the most dynamically critical plants

The "keystone" plants identified by tracking which sites participate most often in real cascades (the *dynamic* keystones) correlate only weakly with the keystones identified by classical graph centrality measures:

| Centrality measure | Spearman ρ | Variance explained |
|---|---|---|
| In-degree            | 0.27 | 7%  |
| Betweenness          | 0.36 | 13% |
| PageRank             | 0.44 | 19% |

Even PageRank — the best of the three — explains less than 20% of the variance in dynamic importance. This suggests that vulnerability assessments based on topology alone, common in the industrial symbiosis literature, systematically underestimate certain **"hidden keystone" plants** whose criticality emerges only from cascade dynamics.

---

## Key results at a glance

| Quantity                                 | Value                |
|------------------------------------------|----------------------|
| Power-law exponent τ (BA, ⟨k⟩=4)         | **1.96 ± 0.01**      |
| Likelihood ratio vs exponential          | R = 7928, p < 10⁻⁴   |
| τ range across topologies                | 2.0 – 3.0            |
| Largest cascade observed (N=400)         | ~250 plants          |
| Total avalanches sampled                 | 1.9 × 10⁵            |
| Network sizes tested                     | 50, 100, 200, 400    |

---

## Reproducing the results

All results can be regenerated from scratch in about 10 minutes on a modern laptop.

### Setup

```bash
git clone https://github.com/JaagravShakalya/circular-economy-soc.git
cd circular-economy-soc
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run the simulations

```bash
python -m src.sweep
```

This runs the full connectivity sweep (45 runs across 3 topologies × 5 connectivities × 3 seeds) plus the finite-size scaling sweep, in about 5–10 minutes total.

### Regenerate the figures

```bash
python -c "from src.plots import *; \
  figure1_topology_comparison(); \
  figure2_exponent_vs_connectivity(); \
  figure3_subcritical_to_supercritical(); \
  figure4_finite_size_scaling(); \
  figure5_dynamic_vs_static_keystones(); \
  figure_kalundborg()"
```

### Generate the cascade visualizations

```bash
python -c "from src.cascade_viz import \
  static_cascade_snapshot, animated_cascade_gif; \
  static_cascade_snapshot(); animated_cascade_gif()"
```

The full report PDF is in `report/main.pdf`.

---

## Acknowledgements

This project was developed with the assistance of an LLM (Claude). All prompts used during development are logged verbatim in `prompts.md` and reproduced in Appendix A of the manuscript, as required by the course guidelines. The Motter–Lai cascading-failure model and the Clauset–Shalizi–Newman power-law fitting methodology are adopted from the published literature; full references are in the manuscript bibliography.

## License

Released under the [MIT License](LICENSE).
