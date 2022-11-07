from typing import Tuple, Union
import casadi as cs
import numpy as np
from casadi_nlp.wrappers.wrapper import Wrapper, NlpType
from casadi_nlp.util import cached_property, cached_property_reset


PRIMAL_DUAL_ORDER = ['x', 'g', 'h', 'h_lbx', 'h_ubx']


class DifferentiableNlp(Wrapper[NlpType]):
    '''
    Wraps an NLP to allow to perform numerical sensitivity analysis and compute
    its derivates.

    References
    ----------
    [1] Buskens, C. and Maurer, H. (2001). Sensitivity analysis and real-time 
        optimization of parametric nonlinear programming problems. In M. 
        Grotschel, S.O. Krumke, and J. Rambau (eds.), Online Optimization of 
        Large Scale Systems, 3–16. Springer, Berlin, Heidelberg.
    '''

    def __init__(
        self,
        nlp: NlpType,
        simplify_x_bounds: bool = True,
        include_barrier_term: bool = False
    ) -> None:
        '''Instantiates the wrapper.

        Parameters
        ----------
        nlp : NlpType
            The NLP problem to be wrapped.
        simplify_x_bounds : bool, optional
            If `True`, then redundant entries in `lbx` and `ubx` are removed;
            see properties `h_lbx` and `h_ubx` for more details. By default,
            `True`.
        include_barrier_term : bool, optional
            If `True`, includes in the KKT matrix a new symbolic variable that
            represents the barrier function of the interior-point solver. By 
            default `False`, so that no additional variable is added. See 
            property `kkt_matrix` for more details.
        '''
        super().__init__(nlp)
        self.remove_reduntant_x_bounds = simplify_x_bounds
        self.include_barrier_term = include_barrier_term

    @cached_property
    def h_lbx(self) -> Union[Tuple[cs.SX, cs.SX], Tuple[cs.MX, cs.MX]]:
        '''Gets the inequalities due to `lbx` and their multipliers. If 
        `simplify_x_bounds=True`, it removes redundant entries, i.e., where
        `lbx == -inf`; otherwise, returns all lower bound constraints.'''
        if self.remove_reduntant_x_bounds:
            idx = np.where(self.nlp._lbx != -np.inf)[0]
        else:
            idx = np.arange(self.nlp.nx)
        h = self.nlp._lbx[idx, None] - self.nlp._x[idx]
        return h, self.nlp._lam_lbx[idx]

    @cached_property
    def h_ubx(self) -> Union[Tuple[cs.SX, cs.SX], Tuple[cs.MX, cs.MX]]:
        '''Gets the inequalities due to `ubx` and their multipliers. If 
        `simplify_x_bounds=True`, it removes redundant entries, i.e., where
        `ubx == +inf`; otherwise, returns all upper bound constraints.'''
        if self.remove_reduntant_x_bounds:
            idx = np.where(self.nlp._ubx != np.inf)[0]
        else:
            idx = np.arange(self.nlp.nx)
        h = self.nlp._x[idx] - self.nlp._ubx[idx, None]
        return h, self.nlp._lam_ubx[idx]

    @cached_property
    def lagrangian(self) -> Union[cs.SX, cs.MX]:
        '''Gets the Lagrangian of the NLP problem.'''
        h_lbx, lam_h_lbx = self.h_lbx
        h_ubx, lam_h_ubx = self.h_ubx
        return (self.nlp._f +
                cs.dot(self.nlp._lam_g, self.nlp._g) +
                cs.dot(self.nlp._lam_h, self.nlp._h) +
                cs.dot(lam_h_lbx, h_lbx) +
                cs.dot(lam_h_ubx, h_ubx))

    @cached_property
    def primal_dual_variables(self) -> Union[cs.SX, cs.MX]:
        '''Gets the collection of primal-dual variables.'''
        args = []
        for o in _PRIMAL_DUAL_ORDER:
            if o == 'x':
                args.append(self.nlp._x)
            elif o == 'g':
                args.append(self.nlp._lam_g)
            elif o == 'h':
                args.append(self.nlp._lam_h)
            elif o == 'h_lbx':
                args.append(self.h_lbx[1])
            elif o == 'h_ubx':
                args.append(self.h_ubx[1])
            else:
                raise RuntimeError(
                    'Found unexpected primal-dual type. Code should never '
                    'reach this statement. Contact the developer, unless you '
                    'explicitly modified the `PRIMAL_DUAL_ORDER` list.')
        return cs.vertcat(*args)

    @cached_property_reset(h_lbx, h_ubx, lagrangian, primal_dual_variables)
    def variable(self, *args, **kwargs):
        return self.nlp.variable(*args, **kwargs)

    @cached_property_reset(lagrangian, primal_dual_variables)
    def constraint(self, *args, **kwargs):
        return self.nlp.constraint(*args, **kwargs)

    @cached_property_reset(lagrangian)
    def minimize(self, *args, **kwargs):
        return self.nlp.minimize(*args, **kwargs)
