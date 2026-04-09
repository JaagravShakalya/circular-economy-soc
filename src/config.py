"""Locked-in simulation parameters from Phase 3 tuning.

Motter-Lai cascading-failure model on a directed network.
At each timestep one randomly chosen plant is tripped; its load
redistributes to downstream neighbors via edge weights, and any
neighbor whose new load exceeds capacity (1+alpha)*baseline_load
also trips, recursively.

Phase 3 fitted exponent: tau = 1.96 +/- 0.01, R = 8578 vs exponential.
"""

ALPHA = 0.8
N = 300
T = 100000
BURN_IN = 10000
SEED = 999
