from math import sqrt
from collections import UserDict
from itertools import combinations
from typing import Union, Optional, Mapping
import casadi as cs
import numpy as np
from scipy.special import comb


SQRT2 = sqrt(2)


def log(
    x: Union[cs.SX, cs.MX, cs.DM],
    base: Union[None, cs.SX, cs.MX, cs.DM] = None
) -> Union[cs.SX, cs.MX, cs.DM]:
    '''Logarithm. With one argument, return the natural logarithm of `x` (to
    base `e`). With two arguments, return the logarithm of x to the given base,
    calculated as `log(x) / log(base)`.

    Parameters
    ----------
    x : Union[cs.SX, cs.MX, cs.DM]
        Value to compute the logarithm of.
    base : Union[None, cs.SX, cs.MX, cs.DM], optional
        Base of the logarithm, by default None

    Returns
    -------
    Union[cs.SX, cs.MX, cs.DM]
        The logarithm. of `x` with base `base`.
    '''
    return cs.log(x) if base is None else cs.log(x) / cs.log(base)


def prod(
    x: Union[cs.SX, cs.MX, cs.DM],
    axis: Optional[int] = None
) -> Union[cs.SX, cs.MX, cs.DM]:
    '''Computes the product of all the elements in `x` (CasADi version of
    `numpy.prod`).

    Parameters
    ----------
    x : Union[cs.SX, cs.MX, cs.DM]
        The variable whose entries must be multiplied together.
    axis : {0, 1, None}
        Axis or along which a product is performed. The default, `axis=None`,
        will calculate the product of all the elements in the matrix. If axis
        is negative it counts from the last to the first axis.

    Returns
    -------
    Union[cs.SX, cs.MX, cs.DM]
        Product of the elements.
    '''
    if axis is None:
        x = cs.vec(x)
        axis = 0
    elif axis < 0:
        axis = 2 + axis
    sum_ = cs.sum1 if axis == 0 else cs.sum2
    n_negatives = sum_(x < 0)
    p = cs.exp(sum_(cs.log(cs.fabs(x))))
    return cs.if_else(cs.mod(n_negatives, 2) == 0.0, 1, -1) * p


def quad_form(
    A: Union[cs.SX, cs.MX, cs.DM],
    x: Union[cs.SX, cs.MX, cs.DM]
) -> Union[cs.SX, cs.MX, cs.DM]:
    '''Calculates quadratic form `x.T*A*x`.

    Parameters
    ----------
    A : Union[cs.SX, cs.MX, cs.DM]
        The matrix of weights in the quadratic form. If a vector, a matrix with
        the vector as diagonal is used instead.
    x : Union[cs.SX, cs.MX, cs.DM]
        The vector in the quadratic form.

    Returns
    -------
    Union[cs.SX, cs.MX, cs.DM]
        The result of the quadratic form.

    Raises
    ------
    RuntimeError
        Raises if
         - `A` is not squared
         - `A` and `x` cannot be multiplied together
         - `x` is not a vector.
    '''
    if A.is_vector():
        A = cs.diag(A)
    return cs.bilin(A, x, x)


def norm_cdf(
    x: Union[cs.SX, cs.MX, cs.DM],
    loc: Union[cs.SX, cs.MX, cs.DM] = cs.DM(0),
    scale: Union[cs.SX, cs.MX, cs.DM] = cs.DM(1)
) -> Union[cs.SX, cs.MX, cs.DM]:
    '''Computes the cdf of a normal distribution. See `scipy.stats.norm.cdf`.

    Parameters
    ----------
    x : Union[cs.SX, cs.MX, cs.DM]
        The value at which the cdf is computed.
    loc : Union[cs.SX, cs.MX, cs.DM], optional
        Mean of the normal distribution. By default, `loc=0`.
    scale : Union[cs.SX, cs.MX, cs.DM], optional
        Standard deviation of the normal distribution. By default, `scale=0`.

    Returns
    -------
    Union[cs.SX, cs.MX, cs.DM]
        The cdf of the normal distribution.
    '''
    return 0.5 * (1 + cs.erf((x - loc) / SQRT2 / scale))


def norm_ppf(
    p: Union[cs.SX, cs.MX, cs.DM],
    loc: Union[cs.SX, cs.MX, cs.DM] = cs.DM(0),
    scale: Union[cs.SX, cs.MX, cs.DM] = cs.DM(1)
) -> Union[cs.SX, cs.MX, cs.DM]:
    '''Computes the quantile (invese of cdf) of a normal distribution. See
    `scipy.stats.norm.ppf`.

    Parameters
    ----------
    x : Union[cs.SX, cs.MX, cs.DM]
        The value at which the quantile is computed.
    loc : Union[cs.SX, cs.MX, cs.DM], optional
        Mean of the normal distribution. By default, `loc=0`.
    scale : Union[cs.SX, cs.MX, cs.DM], optional
        Standard deviation of the normal distribution. By default, `scale=0`.

    Returns
    -------
    Union[cs.SX, cs.MX, cs.DM]
        The quantile of the normal distribution.
    '''
    return SQRT2 * scale * cs.erfinv(2 * p - 1) + loc


def nchoosek(n: Union[int, np.ndarray], k: int) -> Union[int, np.ndarray]:
    '''Emulates the `nchoosek` function from Matlab. Returns the binomial
    coefficient, i.e.,  the number of combinations of `n` items taken `k` at a
    time. If `n` is an array, then it is flatten and all possible combinations
    of its elements are returned.

    Parameters
    ----------
    n : int or array_like
        Number of elements or array of elements to choose from.
    k : int
        Number of elements to choose.

    Returns
    -------
    int or array_like
        Depending on the type of input `n`, the output is either the total
        number of combinations or the combinations in a matrix.
    '''
    return (comb(n, k, exact=True)
            if isinstance(n, int) else
            np.row_stack(list(combinations(np.asarray(n).flatten(), k))))


def monomial_powers(d: int, k: int) -> np.ndarray:
    '''Computes the powers of all `d`-dimensional monomials of degree `k`.

    Parameters
    ----------
    d : int
        The number of monomial elements.
    k : int
        The degree of each monomial.

    Returns
    -------
    np.ndarray
        An array containing in each row the power of each index in order to
        obtain the desired monomial of power `k`.
    '''
    m = nchoosek(k + d - 1, d - 1)
    dividers = np.column_stack((
        np.zeros((m, 1), dtype=int),
        np.row_stack(nchoosek(np.arange(1, k + d), d - 1)),
        np.full((m, 1), k + d, dtype=int)
    ))
    return np.flipud(np.diff(dividers, axis=1) - 1).astype(int)


class Normalization(UserDict):
    '''Class for the normalization of quantities. It suffices to register the 
    range of the variable, and then it can be easily (de-)normalized according
    to such range.'''
    
    def can_normalize(self, name: str) -> bool:
        '''Checks whether there exists a range under the given name.

        Parameters
        ----------
        name : str
            Name of the normalization range.

        Returns
        -------
        bool
            Whether range `name` exists for normalization.
        '''
        return name in self.data

    def register(self, other: Mapping = None, **kwargs: np.ndarray) -> None:
        '''Registers new normalization ranges, but raises if duplicates occur.

        Parameters
        ----------
        other : Mapping, optional
            A mapping (e.g., dict) of normalization ranges, by default None.

        Raises
        ------
        KeyError
            Raises if a duplicate key is detected.
        '''
        for k in kwargs:
            if k in self.data:
                raise KeyError(
                    f'\'{k}\' already registered for normalization.')
        if other is None:
            return self.update(**kwargs)
        for k, _ in other.items() if isinstance(other, Mapping) else other:
            if k in self.data:
                raise KeyError(
                    f'\'{k}\' already registered for normalization.')
        return self.update(other, **kwargs)

    def normalize(self, name: str, x: np.ndarray) -> np.ndarray:
        '''Normalizes the value `x` according to the ranges of `name`.

        Parameters
        ----------
        name : str
            Ranges to be used.
        x : np.ndarray
            Value to be normalized. If an array, then take care that the last
            dimension matches the dimension of the normalization ranges,
            otherwise the output will have a different shape.

        Returns
        -------
        np.ndarray
            Normalized `x`.

        Raises
        ------~
        AssertionError
            Raises if normalized output's shape does not match input's shape.
        '''
        r: np.ndarray = self.data[name]
        if r.ndim == 1:
            out = (x - r[0]) / (r[1] - r[0])
        else:
            out = (x - r[:, 0]) / (r[:, 1] - r[:, 0])
        assert np.shape(out) == np.shape(x), \
            'Normalization altered input shape.'
        return out

        # '''Denormalizes the value `x` according to the ranges of `name`.'''

    def denormalize(self, name: str, x: np.ndarray) -> np.ndarray:
        '''Denormalizes the value `x` according to the ranges of `name`.

        Parameters
        ----------
        name : str
            Ranges to be used.
        x : np.ndarray
            Value to be denormalized.

        Returns
        -------
        np.ndarray
            Denormalized `x`.

        Raises
        ------
        AssertionError
            Raises if denormalized output's shape does not match input's shape.
        '''
        r: np.ndarray = self.data[name]
        if r.ndim == 1:
            out = (r[1] - r[0]) * x + r[0]
        else:
            out = (r[:, 1] - r[:, 0]) * x + r[:, 0]
        assert np.shape(out) == np.shape(x), \
            'Denormalization altered input shape.'
        return out

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}: {super().__repr__()}>'

    def __str__(self) -> str:
        return f'<{self.__class__.__name__}: {super().__str__()}>'
