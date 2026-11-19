"""
Model 1: Hierarchical Bayesian Cognitive Capacity Estimation
============================================================
Uses a Gamma-Poisson conjugate Bayesian model to estimate each student's
personalized cognitive processing capacity from daily learning-activity counts.

Mathematical formulation
------------------------
Prior:     lambda ~ Gamma(alpha_0, beta_0)        [shape-rate parameterisation]
Likelihood: x_i ~ Poisson(lambda)  for i=1..n
Posterior: lambda | X ~ Gamma(alpha_post, beta_post)
  where:
    alpha_post = alpha_0 + sum(x_i)
    beta_post  = beta_0  + n

Posterior statistics:
  E[lambda|X]   = alpha_post / beta_post          (capacity point estimate)
  Var[lambda|X] = alpha_post / beta_post^2
  95% CI        = Gamma.ppf([0.025, 0.975], a=alpha_post, scale=1/beta_post)

Shrinkage property:
  When n=0 (new student), estimate = cohort prior alpha_0/beta_0
  As n -> inf, estimate -> empirical rate sum(x_i)/n

Note: clicks are behavioural observations, not direct measurements of
cognitive capacity. High click counts do not automatically imply high capacity.
Anomalous observations are excluded before the posterior update.

All default hyperparameters are marked PROVISIONAL until research validates them.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
import numpy as np
from scipy.stats import gamma as gamma_dist


# ---------------------------------------------------------------------------
# Default prior hyperparameters (PROVISIONAL)
# ---------------------------------------------------------------------------
# These institution-level hyperpriors must be replaced with Empirical Bayes
# estimates once a sufficient cohort is available. They are explicitly flagged
# so the system never silently treats them as validated research values.

DEFAULT_ALPHA_0: float = 2.0   # PROVISIONAL — shape hyperprior
DEFAULT_BETA_0: float  = 1.0   # PROVISIONAL — rate hyperprior
ANOMALY_ZSCORE_THRESHOLD: float = 3.5  # z-score beyond which daily count is flagged


@dataclass
class CapacityPrior:
    """Gamma prior hyperparameters for the student capacity estimate."""
    alpha_0: float = DEFAULT_ALPHA_0  # PROVISIONAL
    beta_0: float  = DEFAULT_BETA_0   # PROVISIONAL
    is_provisional: bool = True
    version: str = 'v1.0-provisional'

    @property
    def prior_mean(self) -> float:
        return self.alpha_0 / self.beta_0


@dataclass
class CapacityEstimate:
    """Full Bayesian posterior representing a student's estimated cognitive capacity."""
    student_id: str
    alpha_post: float              # Posterior shape
    beta_post: float               # Posterior rate
    mean_capacity: float           # Posterior mean = alpha_post / beta_post
    variance: float                # Posterior variance = alpha_post / beta_post^2
    ci_lower_95: float             # 2.5th percentile
    ci_upper_95: float             # 97.5th percentile
    n_observations: int            # Number of daily aggregates used
    n_anomalous_excluded: int      # Anomalous observations excluded
    is_provisional_params: bool    # True if using PROVISIONAL priors
    model_version: str
    calculated_at: datetime

    @property
    def uncertainty_width(self) -> float:
        """Width of 95% credible interval — a measure of estimation uncertainty."""
        return self.ci_upper_95 - self.ci_lower_95


def detect_anomalies(
    daily_counts: list[float],
    threshold_zscore: float = ANOMALY_ZSCORE_THRESHOLD,
) -> tuple[list[float], list[int]]:
    """
    Flag daily click counts that deviate more than `threshold_zscore` standard
    deviations from the rolling mean. These observations are excluded from the
    Bayesian posterior update to prevent capacity estimates being distorted by
    bot-like or erroneous activity.

    Returns
    -------
    valid_counts   : counts not flagged as anomalous
    anomaly_indices: indices of flagged observations
    """
    if len(daily_counts) < 3:
        return daily_counts, []  # Cannot detect anomalies with < 3 observations

    arr = np.array(daily_counts, dtype=float)
    mean = arr.mean()
    std  = arr.std(ddof=1)

    if std == 0.0:
        return daily_counts, []  # All identical — nothing to flag

    z_scores = np.abs((arr - mean) / std)
    anomaly_indices = [int(i) for i in np.where(z_scores > threshold_zscore)[0]]
    valid_counts = [c for i, c in enumerate(daily_counts) if i not in anomaly_indices]
    return valid_counts, anomaly_indices


def update_posterior(
    prior: CapacityPrior,
    daily_counts: list[float],
) -> tuple[float, float, int, int]:
    """
    Perform the Gamma-Poisson conjugate posterior update.

    Returns
    -------
    alpha_post         : updated shape parameter
    beta_post          : updated rate parameter
    n_valid            : number of valid observations used
    n_anomalous        : number of observations excluded
    """
    valid_counts, anomaly_indices = detect_anomalies(daily_counts)
    n_anomalous = len(anomaly_indices)

    n_valid  = len(valid_counts)
    sum_x    = float(sum(valid_counts))

    alpha_post = prior.alpha_0 + sum_x
    beta_post  = prior.beta_0  + n_valid

    return alpha_post, beta_post, n_valid, n_anomalous


def estimate_capacity(
    student_id: str,
    daily_counts: list[float],
    prior: Optional[CapacityPrior] = None,
    model_version: str = 'v1.0-provisional',
) -> CapacityEstimate:
    """
    Compute the full Bayesian posterior capacity estimate for a student.

    Parameters
    ----------
    student_id    : student UUID (string)
    daily_counts  : list of daily valid-click counts (non-negative floats)
    prior         : Gamma prior; defaults to PROVISIONAL institution hyperprior
    model_version : version string for audit traceability

    Returns
    -------
    CapacityEstimate with full posterior statistics
    """
    if prior is None:
        prior = CapacityPrior()

    if not daily_counts:
        # Cold-start: return pure prior (new student, no observations)
        alpha_p = prior.alpha_0
        beta_p  = prior.beta_0
        n_valid = 0
        n_anom  = 0
    else:
        alpha_p, beta_p, n_valid, n_anom = update_posterior(prior, daily_counts)

    mean_cap  = alpha_p / beta_p
    variance  = alpha_p / (beta_p ** 2)
    # Gamma distribution in scipy uses scale = 1/rate
    scale     = 1.0 / beta_p
    ci_lower  = float(gamma_dist.ppf(0.025, a=alpha_p, scale=scale))
    ci_upper  = float(gamma_dist.ppf(0.975, a=alpha_p, scale=scale))

    return CapacityEstimate(
        student_id=student_id,
        alpha_post=alpha_p,
        beta_post=beta_p,
        mean_capacity=mean_cap,
        variance=variance,
        ci_lower_95=ci_lower,
        ci_upper_95=ci_upper,
        n_observations=n_valid,
        n_anomalous_excluded=n_anom,
        is_provisional_params=prior.is_provisional,
        model_version=model_version,
        calculated_at=datetime.utcnow(),
    )


def update_cohort_prior_empirical_bayes(
    cohort_counts: list[list[float]],
) -> CapacityPrior:
    """
    Estimate institution-level hyperparameters (alpha_0, beta_0) via the
    Method of Moments applied to observed student daily rates.

    This is a simplified Empirical Bayes approach. For production, replace
    with Marginal Maximum Likelihood optimisation or MCMC (Celery task).

    Parameters
    ----------
    cohort_counts : list of daily count sequences, one per student

    Returns
    -------
    CapacityPrior with updated hyperparameters (marked not provisional
    once enough cohort data is available, i.e. n_students >= 30)
    """
    if len(cohort_counts) < 5:
        return CapacityPrior()  # Insufficient cohort; return default PROVISIONAL prior

    student_means = [np.mean(counts) for counts in cohort_counts if counts]
    if not student_means:
        return CapacityPrior()

    mu  = float(np.mean(student_means))
    var = float(np.var(student_means, ddof=1)) if len(student_means) > 1 else 1.0

    if var == 0.0 or mu == 0.0:
        return CapacityPrior()

    # Method of moments: E[lambda]=alpha/beta, Var[lambda]=alpha/beta^2
    # => beta = mu/var, alpha = mu*beta
    beta_0_est  = mu / var
    alpha_0_est = mu * beta_0_est

    is_prov = len(cohort_counts) < 30  # Still provisional below 30 students
    return CapacityPrior(
        alpha_0=alpha_0_est,
        beta_0=beta_0_est,
        is_provisional=is_prov,
        version='v1.1-empirical-bayes' if not is_prov else 'v1.0-provisional',
    )
