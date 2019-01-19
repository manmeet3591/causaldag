from typing import Any, Union, List, Optional
import numpy as np
from . import kernels
from scipy.stats import gamma
from ._utils import residuals, combined_mat


def hsic_test_vector(x: np.ndarray, y: np.ndarray, sig: float=1/np.sqrt(2), alpha=0.05):
    if x.ndim == 1:
        x = x.reshape((len(x), 1))
    if y.ndim == 1:
        y = y.reshape((len(y), 1))
    n = x.shape[0]
    if y.shape[0] != n:
        raise ValueError("Y should have the same number of samples as X")

    n = x.shape[0]
    H = np.eye(n) - np.ones([n, n])/n
    kernel_precision = 1/(sig**2)

    # === COMPUTE CENTRALIZED KERNEL MATRICES
    kx = kernels.rbf_kernel(x, kernel_precision)
    ky = kernels.rbf_kernel(y, kernel_precision)
    kx_centered = H @ kx @ H
    ky_centered = H @ ky @ H

    # === COMPUTE STATISTIC
    statistic = 1/n**2 * np.sum(kx_centered * ky_centered.T)  # SAME AS trace(kx_centered @ ky_centered)

    mu_x = 1/(n*(n-1)) * np.sum(kx - np.diag(np.diag(kx)))  # SUM OFF-DIAGONALS
    mu_y = 1/(n*(n-1)) * np.sum(ky - np.diag(np.diag(ky)))
    mean_approx = 1/n * (1 + mu_x*mu_y - mu_x - mu_y)
    var_approx = 2*(n-4)*(n-5)/(n*(n-1)*(n-2)*(n-3)) * np.sum(kx_centered * kx_centered.T) * np.sum(ky_centered * ky_centered.T) / n**4

    k_approx = mean_approx ** 2 / var_approx
    prec_approx = var_approx / mean_approx

    critval = gamma.ppf(1-alpha, k_approx, scale=prec_approx)
    p_value = 1 - gamma.cdf(statistic, k_approx, scale=prec_approx)

    return dict(statistic=statistic, critval=critval, p_value=p_value, reject=statistic > critval, mean_approx=mean_approx, var_approx=var_approx)


def hsic_test(
        suffstat: Any,
        i: int,
        j: int,
        cond_set: Union[List[int], int]=None,
        alpha: float=0.05
):
    if isinstance(cond_set, int):
        cond_set = [cond_set]
    if cond_set is None or len(cond_set) == 0:
        return hsic_test_vector(suffstat[:, i], suffstat[:, j], alpha=alpha)
    else:
        residuals_i, residuals_j = residuals(suffstat, i, j, cond_set)
        return hsic_test_vector(residuals_i, residuals_j, alpha=alpha)


def hsic_invariance_test(
        samples1: np.ndarray,
        samples2: np.ndarray,
        i: int,
        cond_set: Optional[Union[List[int], int]]=None,
        alpha: float=0.05
):
    if isinstance(cond_set, int):
        cond_set = [cond_set]
    if cond_set is None:
        cond_set = []

    mat = combined_mat(samples1, samples2, i, cond_set)
    return hsic_test(mat, 0, 1, list(range(2, 2+len(cond_set))), alpha=alpha)



