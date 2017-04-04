
import numpy as np

from .baker_jayaram_2008 import calc_correl
from . import ArrayLike


def calc_cond_mean_spectrum_vector(periods: ArrayLike,
                                   ln_psas: ArrayLike,
                                   ln_stds: ArrayLike,
                                   ln_psas_cond: np.ma.masked_array,
                                   ) -> (np.ndarray, np.ndarray):
    """Compute conditional mean spectrum vector (CMSV) proposed by Kishida 
    (2017).
    
    Kishida (2017) proposed specifying the target spectral acceleration at 
    multiple periods, rather than the single conditioning period by Cornell 
    and Baker (2008). 
    
    Parameters
    ----------
    periods: `array_like`
        Spectral periods of the response spectrum [sec]. This array must be 
        increasing.
    ln_psas: `array_like`
        Natural logarithm of the spectral acceleration. Same length as 
        `periods`.
    ln_stds: `array_like`
        Logarithmic standard deviation of the spectral acceleration. Same 
        length as `periods`.
    ln_psas_cond: :class:`np.ma.masked_array`
        The vector of conditioning spectral accelerations. This is a masked 
        array with the same length as `periods`. Masked values are not used 
        for defining the CMSV.
    
    Returns
    -------
    ln_psas_cmsv: :class:`np.ndarray`
        Natural logarithm of the conditional 5%-damped spectral accelerations.
        The spectral acceleration is equal to `ln_psas_cond` at each of the 
        conditioning periods.
    ln_stds_cmsv: :class:`np.ndarray`
        Logarithmic standard deviation of conditional spectrum.
    """
    periods = np.asarray(periods)
    ln_psas = np.asarray(ln_psas)
    ln_stds = np.asarray(ln_stds)

    if not np.all(np.diff(periods) > 0):
        raise ValueError("`periods` must be increasing")

    mask = ln_psas_cond.mask

    # Group the periods into those not being conditioned upon, and those used
    # for the conditioning. See Equations (14), (15), and (16)
    periods_grouped = np.r_[periods[mask], periods[~mask]]
    # Standard deviation matrix. Named V^{1/2} in Kishida, Equation (8)
    mat_ln_std = np.diag(np.r_[ln_stds[mask], ln_stds[~mask]])
    # Correlation matrix, Equation (9)
    mat_correl = np.vstack([calc_correl(periods_grouped, period_cond)
                            for period_cond in periods_grouped]).T
    # Covariance matrix, Equation (7)
    mat_covar = mat_ln_std @ mat_correl @ mat_ln_std
    # Extract the submatrices, Equation (6)
    n = np.ma.count_masked(ln_psas_cond)
    mat_covar_11 = mat_covar[0:n, 0:n]
    mat_covar_22 = mat_covar[n:, n:]
    mat_covar_12 = mat_covar[0:n, n:]
    mat_covar_21 = mat_covar[n:, 0:n]
    mat_covar_22_inv = np.linalg.inv(mat_covar_22)
    # Conditional mean value, Equation (3)
    mat_total_resids = np.asmatrix(ln_psas_cond[~mask] - ln_psas[~mask]).T
    ln_psas_cmsv = np.r_[
        ln_psas[mask] +
        np.ravel(mat_covar_12 @ mat_covar_22_inv @ mat_total_resids),
        ln_psas_cond[~mask].data
    ]
    # Compute standard deviation, Equation (4)
    ln_stds_cmsv = np.r_[
        np.sqrt(np.diag(mat_covar_11 -
                        mat_covar_12 @ mat_covar_22_inv @ mat_covar_21)),
        np.zeros(ln_psas_cond.count())
    ]
    # Sort to the original period indices
    indices = np.argsort(periods_grouped)
    ln_psas_cmsv = ln_psas_cmsv[indices]
    ln_stds_cmsv = ln_stds_cmsv[indices]

    return ln_psas_cmsv, ln_stds_cmsv
