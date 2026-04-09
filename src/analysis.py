"""Analysis helpers: power-law fitting and run loading."""

import numpy as np
import powerlaw


def load_run(topology, mean_degree, seed, data_dir="data/runs"):
    """Load a saved avalanche-size array."""
    return np.load(f"{data_dir}/{topology}_k{mean_degree}_seed{seed}.npy")


def fit_power_law(sizes):
    """
    Fit a power law to avalanche sizes.

    Returns None if the data is too degenerate to fit
    (e.g. almost all events the same size).
    """
    nonzero = sizes[sizes > 0]
    if len(nonzero) < 50:
        return None
    if len(np.unique(nonzero)) < 3:
        return None  # not enough variation to fit anything

    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fit = powerlaw.Fit(nonzero, discrete=True, verbose=False)
            R_exp, p_exp = fit.distribution_compare("power_law", "exponential")
        if not np.isfinite(fit.power_law.alpha):
            return None
        return {
            "tau": fit.power_law.alpha,
            "sigma_tau": fit.power_law.sigma,
            "x_min": fit.power_law.xmin,
            "R_exp": R_exp,
            "p_exp": p_exp,
            "n_above_xmin": int((nonzero >= fit.power_law.xmin).sum()),
        }
    except (ValueError, RuntimeWarning, Exception):
        return None


def log_binned_pdf(sizes, n_bins=25):
    """Compute a log-binned PDF for plotting on log-log axes."""
    sizes = np.array([s for s in sizes if s > 0])
    if len(sizes) == 0:
        return np.array([]), np.array([])
    s_min, s_max = sizes.min(), sizes.max()
    bins = np.logspace(np.log10(s_min), np.log10(s_max + 1), n_bins)
    counts, edges = np.histogram(sizes, bins=bins)
    widths = np.diff(edges)
    centers = np.sqrt(edges[:-1] * edges[1:])
    total = counts.sum()
    pdf = counts / (widths * total)
    mask = counts > 0
    return centers[mask], pdf[mask]
