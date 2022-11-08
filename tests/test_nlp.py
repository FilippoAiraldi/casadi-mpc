import unittest
from itertools import product
import casadi as cs
import numpy as np
from casadi_nlp import Nlp
from casadi_nlp.solutions import subsevalf


OPTS = {
    'expand': True, 'print_time': False,
    'ipopt': {
        'max_iter': 500,
        'sb': 'yes',
        # for debugging
        'print_level': 1,
        'print_user_options': 'no',
        'print_options_documentation': 'no'
    }
}


class TestNlp(unittest.TestCase):
    def test_init__raises__with_invalid_sym_type(self):
        with self.assertRaises(Exception):
            Nlp(sym_type='a_random_sym_type')

    def test_parameter__creates_correct_parameter(self):
        shape1 = (4, 3)
        shape2 = (2, 2)
        _np = np.prod(shape1) + np.prod(shape2)
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            p1 = nlp.parameter('p1', shape1)
            p2 = nlp.parameter('p2', shape2)
            self.assertEqual(p1.shape, shape1)
            self.assertEqual(p2.shape, shape2)
            self.assertEqual(nlp.np, _np)

            p = cs.vertcat(cs.vec(p1), cs.vec(p2))
            if sym_type == 'SX':
                # symbolically for SX
                self.assertTrue(cs.is_equal(nlp.p, p))
            else:
                # only numerically for MX
                p1_ = np.random.randn(*p1.shape)
                p2_ = np.random.randn(*p2.shape)
                np.testing.assert_allclose(
                    subsevalf(nlp.p, [p1, p2], [p1_, p2_]),
                    subsevalf(p, [p1, p2], [p1_, p2_]),
                )

            i = 0
            for name, shape in [('p1', shape1), ('p2', shape2)]:
                for _ in range(np.prod(shape)):
                    self.assertEqual(name, nlp.debug.p_describe(i).name)
                    self.assertEqual(shape, nlp.debug.p_describe(i).shape)
                    i += 1
            with self.assertRaises(IndexError):
                nlp.debug.p_describe(_np + 1)

            self.assertTrue(cs.is_equal(nlp.parameters['p1'], p1))
            self.assertTrue(cs.is_equal(nlp.parameters['p2'], p2))

    def test_parameter__raises__with_parameters_with_same_name(self):
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            nlp.parameter('p')
            with self.assertRaises(ValueError):
                nlp.parameter('p')

    def test_variable__creates_correct_variable(self):
        shape1 = (4, 3)
        shape2 = (2, 2)
        lb1, ub1 = np.random.rand(*shape1) - 1, np.random.rand(*shape1) + 1
        lb2, ub2 = np.random.rand(*shape2) - 1, np.random.rand(*shape2) + 1
        nx = np.prod(shape1) + np.prod(shape2)
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            x1, lam1_lb, lam1_ub = nlp.variable('x1', shape1, lb=lb1, ub=ub1)
            x2, lam2_lb, lam2_ub = nlp.variable('x2', shape2, lb=lb2, ub=ub2)
            for o in (x1, lam1_lb, lam1_ub):
                self.assertEqual(o.shape, shape1)
            for o in (x2, lam2_lb, lam2_ub):
                self.assertEqual(o.shape, shape2)
            self.assertEqual(nlp.nx, nx)

            x = cs.vertcat(cs.vec(x1), cs.vec(x2))
            if sym_type == 'SX':
                # symbolically for SX
                self.assertTrue(cs.is_equal(nlp.x, x))
            else:
                # only numerically for MX
                x1_ = np.random.randn(*x1.shape)
                x2_ = np.random.randn(*x2.shape)
                np.testing.assert_allclose(
                    subsevalf(nlp.x, [x1, x2], [x1_, x2_]),
                    subsevalf(x, [x1, x2], [x1_, x2_]),
                )
            lb = cs.vertcat(cs.vec(lb1), cs.vec(lb2))
            ub = cs.vertcat(cs.vec(ub1), cs.vec(ub2))
            np.testing.assert_allclose(nlp.lbx, lb.full().flat)
            np.testing.assert_allclose(nlp.ubx, ub.full().flat)

            i = 0
            for name, shape in [('x1', shape1), ('x2', shape2)]:
                for _ in range(np.prod(shape)):
                    self.assertEqual(name, nlp.debug.x_describe(i).name)
                    self.assertEqual(shape, nlp.debug.x_describe(i).shape)
                    i += 1
            with self.assertRaises(IndexError):
                nlp.debug.x_describe(nx + 1)

            self.assertTrue(cs.is_equal(nlp.variables['x1'], x1))
            self.assertTrue(cs.is_equal(nlp.variables['x2'], x2))

    def test_variable__raises__with_variables_with_same_name(self):
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            nlp.variable('x')
            with self.assertRaises(ValueError):
                nlp.variable('x')

    def test_variable__raises__with_invalid_bounds(self):
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            with self.assertRaises(ValueError):
                nlp.variable('x', lb=1, ub=0)

    def test_minimize__raises__with_nonscalar_objective(self):
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            x = nlp.variable('x', (5, 1))[0]
            with self.assertRaises(ValueError):
                nlp.minimize(x)

    def test_minimize__sets_objective_correctly(self):
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            x = nlp.variable('x', (5, 1))[0]
            f = x.T @ x
            nlp.minimize(f)
            self.assertTrue(cs.is_equal(nlp.f, f))

    def test_constraint__raises__with_constraints_with_same_name(self):
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            x = nlp.variable('x')[0]
            nlp.constraint('c1', x, '<=', 5)
            with self.assertRaises(ValueError):
                nlp.constraint('c1', x, '<=', 5)

    def test_constraint__raises__with_unknown_operator(self):
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            x = nlp.variable('x')[0]
            for op in ['=', '>', '<']:
                with self.assertRaises(ValueError):
                    nlp.constraint('c1', x, op, 5)

    def test_constraint__raises__with_nonsymbolic_terms(self):
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            with self.assertRaises(TypeError):
                nlp.constraint('c1', 5, '==', 5)

    def test_constraint__creates_constraint_correctly(self):
        shape1, shape2 = (4, 3), (2, 2)
        nc = np.prod(shape1) + np.prod(shape2)
        for sym_type, ops in product(
                ['SX', 'MX'], [('==', '=='), ('==', '>='), ('>=', '>=')]):
            nlp = Nlp(sym_type=sym_type)
            x = nlp.variable('x', shape1)[0]
            y = nlp.variable('y', shape2)[0]
            c1, lam_c1 = nlp.constraint('c1', x, ops[0], 5)
            c2, lam_c2 = nlp.constraint('c2', 5, ops[1], y)

            self.assertTrue(c1.shape == lam_c1.shape == shape1)
            self.assertTrue(c2.shape == lam_c2.shape == shape2)
            self.assertEqual(nlp.ng + nlp.nh, nc)

            i, prev_op = 0, ops[0]
            for c, name, op in zip((c1, c2), ('c1', 'c2'), ops):
                grp = 'g' if op == '==' else 'h'
                if op != prev_op:
                    i = 0
                describe = getattr(nlp.debug, f'{grp}_describe')
                for _ in range(np.prod(c.shape)):
                    self.assertEqual(name, describe(i).name)
                    self.assertEqual(c.shape, describe(i).shape)
                    i += 1
                with self.assertRaises(IndexError):
                    describe(nc + 1)

            c = cs.vertcat(cs.vec(c1), cs.vec(c2))
            lam = cs.vertcat(cs.vec(lam_c1), cs.vec(lam_c2))
            expected_c = cs.vertcat(nlp.g, nlp.h)
            expected_lam = cs.vertcat(nlp.lam_g, nlp.lam_h)
            if sym_type == 'SX':
                # symbolically for SX
                self.assertTrue(cs.is_equal(expected_c, c))
                self.assertTrue(cs.is_equal(expected_lam, lam))
            else:
                # only numerically for MX
                x_ = np.random.randn(*shape1)
                y_ = np.random.randn(*shape2)
                np.testing.assert_allclose(
                    subsevalf(expected_c, [x, y], [x_, y_]),
                    subsevalf(c, [x, y], [x_, y_])
                )
                lam1_ = np.random.randn(*shape1)
                lam2_ = np.random.randn(*shape2)
                np.testing.assert_allclose(
                    subsevalf(expected_lam, [lam_c1, lam_c2], [lam1_, lam2_]),
                    subsevalf(lam, [lam_c1, lam_c2], [lam1_, lam2_])
                )

    def test_dual__returns_dual_variables_correctly(self):
        shape1, shape2 = (4, 3), (2, 2)
        for sym_type, ops in product(
                ['SX', 'MX'], [('==', '=='), ('==', '>='), ('>=', '>=')]):
            nlp = Nlp(sym_type=sym_type)
            x, lam_lb_x, lam_ub_x = nlp.variable('x', shape1)
            y, lam_lb_y, lam_ub_y = nlp.variable('y', shape2)
            _, lam_c1 = nlp.constraint('c1', x, ops[0], 5)
            _, lam_c2 = nlp.constraint('c2', 5, ops[1], y)

            dv = nlp.dual_variables
            c1_name = f'lam_{"g" if ops[0] == "==" else "h"}_c1'
            c2_name = f'lam_{"g" if ops[1] == "==" else "h"}_c2'
            self.assertTrue(cs.is_equal(dv['lam_lb_x'], lam_lb_x))
            self.assertTrue(cs.is_equal(dv['lam_ub_x'], lam_ub_x))
            self.assertTrue(cs.is_equal(dv['lam_lb_y'], lam_lb_y))
            self.assertTrue(cs.is_equal(dv['lam_ub_y'], lam_ub_y))
            self.assertTrue(cs.is_equal(dv[c1_name], lam_c1))
            self.assertTrue(cs.is_equal(dv[c2_name], lam_c2))

            lams = [lam_c1, lam_c2, lam_lb_x, lam_lb_y, lam_ub_x, lam_ub_y]
            actual_lam = cs.vertcat(*(cs.vec(o) for o in lams))
            expected_lam = nlp.lam
            if sym_type == 'SX':
                # symbolically for SX
                self.assertTrue(cs.is_equal(actual_lam, expected_lam))
            else:
                # only numerically for MX
                lams_ = [np.random.randn(*o.shape) for o in lams]
                np.testing.assert_allclose(
                    subsevalf(actual_lam, lams, lams_),
                    subsevalf(expected_lam, lams, lams_),
                )

    def test_h_lbx_ubx__returns_correct_indices(self):
        for flag in (True, False):
            nlp = Nlp(sym_type='SX', remove_reduntant_x_bounds=flag)

            x1, lam_lbx1, lam_ubx1 = nlp.variable('x1', (2, 1))
            (h_lbx, lam_lbx), (h_ubx, lam_ubx) = nlp.h_lbx, nlp.h_ubx
            if flag:
                self.assertTrue(all(o.is_empty()
                                for o in [h_lbx, lam_lbx, h_ubx, lam_ubx]))
            else:
                np.testing.assert_allclose(cs.evalf(h_lbx - (-np.inf - x1)), 0)
                np.testing.assert_allclose(cs.evalf(lam_lbx - lam_lbx1), 0)
                np.testing.assert_allclose(cs.evalf(h_ubx - (x1 - np.inf)), 0)
                np.testing.assert_allclose(cs.evalf(lam_ubx - lam_ubx1), 0)

            x2, lam_lbx2, lam_ubx2 = nlp.variable('x2', (2, 1), lb=0)
            (h_lbx, lam_lbx), (h_ubx, lam_ubx) = nlp.h_lbx, nlp.h_ubx
            if flag:
                self.assertTrue(all(o.is_empty() for o in [h_ubx, lam_ubx]))
                np.testing.assert_allclose(cs.evalf(h_lbx - (-x2)), 0)
                np.testing.assert_allclose(cs.evalf(lam_lbx - lam_lbx2), 0)
            else:
                np.testing.assert_allclose(cs.evalf(
                    h_lbx - cs.vertcat(-np.inf - x1, 0 - x2)), 0)
                np.testing.assert_allclose(cs.evalf(
                    lam_lbx - cs.vertcat(lam_lbx1, lam_lbx2)), 0)
                np.testing.assert_allclose(cs.evalf(
                    h_ubx - cs.vertcat(x1 - np.inf, x2 - np.inf)), 0)
                np.testing.assert_allclose(cs.evalf(
                    lam_ubx - cs.vertcat(lam_ubx1, lam_ubx2)), 0)

            x3, lam_lbx3, lam_ubx3 = nlp.variable('x3', (2, 1), ub=1)
            (h_lbx, lam_lbx), (h_ubx, lam_ubx) = nlp.h_lbx, nlp.h_ubx
            if flag:
                np.testing.assert_allclose(cs.evalf(h_lbx - (-x2)), 0)
                np.testing.assert_allclose(cs.evalf(lam_lbx - lam_lbx2), 0)
                np.testing.assert_allclose(cs.evalf(h_ubx - (x3 - 1)), 0)
                np.testing.assert_allclose(cs.evalf(lam_ubx - lam_ubx3), 0)
            else:
                np.testing.assert_allclose(cs.evalf(
                    h_lbx - cs.vertcat(-np.inf - x1, 0 - x2, -np.inf - x3)), 0)
                np.testing.assert_allclose(cs.evalf(
                    lam_lbx - cs.vertcat(lam_lbx1, lam_lbx2, lam_lbx3)), 0)
                np.testing.assert_allclose(cs.evalf(
                    h_ubx - cs.vertcat(x1 - np.inf, x2 - np.inf, x3 - 1)), 0)
                np.testing.assert_allclose(cs.evalf(
                    lam_ubx - cs.vertcat(lam_ubx1, lam_ubx2, lam_ubx3)), 0)

            x4, lam_lbx4, lam_ubx4 = nlp.variable('x4', (2, 1), lb=0, ub=1)
            (h_lbx, lam_lbx), (h_ubx, lam_ubx) = nlp.h_lbx, nlp.h_ubx
            if flag:
                np.testing.assert_allclose(cs.evalf(
                    h_lbx - cs.vertcat(-x2, -x4)), 0)
                np.testing.assert_allclose(
                    cs.evalf(lam_lbx - cs.vertcat(lam_lbx2, lam_lbx4)), 0)
                np.testing.assert_allclose(cs.evalf(
                    h_ubx - cs.vertcat(x3 - 1, x4 - 1)), 0)
                np.testing.assert_allclose(
                    cs.evalf(lam_ubx - cs.vertcat(lam_ubx3, lam_ubx4)), 0)
            else:
                np.testing.assert_allclose(cs.evalf(
                    h_lbx - cs.vertcat(
                        -np.inf - x1, 0 - x2, -np.inf - x3, 0 - x4)), 0)
                np.testing.assert_allclose(cs.evalf(
                    lam_lbx - cs.vertcat(
                        lam_lbx1, lam_lbx2, lam_lbx3, lam_lbx4)), 0)
                np.testing.assert_allclose(cs.evalf(
                    h_ubx - cs.vertcat(
                        x1 - np.inf, x2 - np.inf, x3 - 1, x4 - 1)), 0)
                np.testing.assert_allclose(cs.evalf(
                    lam_ubx - cs.vertcat(
                        lam_ubx1, lam_ubx2, lam_ubx3, lam_ubx4)), 0)

    def test_set_solver__saves_options_correctly(self):
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            opts = OPTS.copy()
            x = nlp.variable('x')[0]
            nlp.minimize(x**2)
            nlp.init_solver(opts)
            self.assertDictEqual(opts, nlp.solver_opts)

    def test_solve__raises__with_uninit_solver(self):
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            with self.assertRaises(RuntimeError):
                nlp.solve(None)

    def test_solve__raises__with_free_parameters(self):
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            x = nlp.variable('x')[0]
            p = nlp.parameter('p')
            nlp.minimize(p * (x**2))
            with self.assertRaises(RuntimeError):
                nlp.solve({})

    def test_solve__computes_correctly__example_0(self):
        for sym_type in ('MX', 'SX'):
            nlp = Nlp(sym_type=sym_type)
            x = nlp.variable('x', (2, 1))[0]
            y = nlp.variable('y', (3, 1))[0]
            p = nlp.parameter('p')
            nlp.minimize(p + (x.T @ x + y.T @ y))
            nlp.init_solver(OPTS)
            sol = nlp.solve({'p': 3})
            self.assertTrue(sol.success)
            np.testing.assert_allclose(sol.f, 3)
            for k in sol.vals.keys():
                np.testing.assert_allclose(sol.vals[k], 0)
            o = sol.value(p + (x.T @ x + y.T @ y))
            np.testing.assert_allclose(sol.f, o)

    def test_solve__computes_corretly__example_1a(self):
        # https://en.wikipedia.org/wiki/Lagrange_multiplier#Example_1a
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            x = nlp.variable('x')[0]
            y = nlp.variable('y')[0]
            nlp.constraint('c1', x**2 + y**2, '==', 1)
            nlp.minimize(-x - y)
            nlp.init_solver(OPTS)
            sol = nlp.solve()
            np.testing.assert_allclose(-sol.f, np.sqrt(2))
            for k in ('x', 'y'):
                np.testing.assert_allclose(
                    sol.vals[k], np.sqrt(2) / 2, atol=1e-9)
            np.testing.assert_allclose(
                sol.value(nlp.lam_g), 1 / np.sqrt(2), atol=1e-9)

    def test_solve__computes_corretly__example_1b(self):
        # https://en.wikipedia.org/wiki/Lagrange_multiplier#Example_1b
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            x = nlp.variable('x')[0]
            y = nlp.variable('y')[0]
            nlp.constraint('c1', x**2 + y**2, '==', 1)
            nlp.minimize((x + y)**2)
            nlp.init_solver(OPTS)
            sol = nlp.solve(vals0={
                'x': 0.5,
                'y': np.sqrt(1 - 0.5**2)
            })
            np.testing.assert_allclose(sol.f, 0, atol=1e-9)
            np.testing.assert_allclose(
                abs(sol.vals['x']), np.sqrt(2) / 2, atol=1e-9)
            np.testing.assert_allclose(
                abs(sol.vals['y']), np.sqrt(2) / 2, atol=1e-9)
            np.testing.assert_allclose(sol.value(nlp.lam_g), 0, atol=1e-9)

    def test_solve__computes_corretly__example_2(self):
        # https://en.wikipedia.org/wiki/Lagrange_multiplier#Example_2
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            x = nlp.variable('x')[0]
            y = nlp.variable('y')[0]
            nlp.constraint('c1', x**2 + y**2, '==', 3)
            nlp.minimize(x**2 * y)
            nlp.init_solver(OPTS)
            sol = nlp.solve(vals0={
                'x': np.sqrt(3 - 0.8**2),
                'y': -0.8
            })
            np.testing.assert_allclose(sol.f, -2, atol=1e-9)
            np.testing.assert_allclose(
                abs(sol.vals['x']), np.sqrt(2), atol=1e-9)
            np.testing.assert_allclose(sol.vals['y'], -1, atol=1e-9)
            np.testing.assert_allclose(
                sol.value(sol.vals['x'] * (sol.vals['y'] + nlp.lam_g)), 0,
                atol=1e-9)

    def test_solve__computes_corretly__example_3(self):
        # https://en.wikipedia.org/wiki/Lagrange_multiplier#Example_3:_Entropy
        n = 50
        log2 = lambda x: cs.log(x) / cs.log(2)
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            p = nlp.variable('p', (n, 1), lb=1 / n * 1e-6)[0]
            nlp.constraint('c1', cs.sum1(p), '==', 1)
            nlp.minimize(cs.sum1(p * log2(p)))
            nlp.init_solver(OPTS)
            sol = nlp.solve(vals0={'p': np.random.rand(n)})
            np.testing.assert_allclose(sol.vals['p'], 1 / n, atol=1e-9)
            np.testing.assert_allclose(
                sol.value(-(1 / cs.log(2) + log2(p)) - nlp.lam_g), 0,
                atol=1e-6)

    def test_solve__computes_corretly__example_4(self):
        # https://en.wikipedia.org/wiki/Lagrange_multiplier#Example_4:_Numerical_optimization
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            x = nlp.variable('x')[0]
            nlp.constraint('c1', x**2, '==', 1)
            nlp.minimize(x**2)
            nlp.init_solver(OPTS)
            sol = nlp.solve(vals0={'x': 1 + 0.1 * np.random.rand()})
            np.testing.assert_allclose(sol.f, 1, atol=1e-9)
            np.testing.assert_allclose(sol.value(nlp.lam_g), -1, atol=1e-9)

    def test_solve__computes_corretly__example_5(self):
        # https://personal.math.ubc.ca/~israel/m340/kkt2.pdf
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            x = nlp.variable('x', (2, 1), lb=0)[0]
            nlp.constraint('c1', x[0] + x[1]**2, '<=', 2)
            nlp.minimize(- x[0] * x[1])
            nlp.init_solver(OPTS)
            sol = nlp.solve(vals0={'x': [1, 1]})
            np.testing.assert_allclose(
                -sol.f, np.sqrt(2 / 3) * 4 / 3, atol=1e-9)
            np.testing.assert_allclose(
                sol.vals['x'].full().flatten(),
                [4 / 3, np.sqrt(2 / 3)],
                atol=1e-9)
            np.testing.assert_allclose(
                sol.value(cs.vertcat(nlp.lam_h, nlp.lam_lbx)).full().flatten(),
                [np.sqrt(2 / 3), 0, 0], atol=1e-7)

    def test_solve__computes_corretly__example_6(self):
        # https://www.reddit.com/r/cheatatmathhomework/comments/sw6nqs/optimization_using_kkt_conditions_for_constraints/
        for sym_type in ('SX', 'MX'):
            nlp = Nlp(sym_type=sym_type)
            x = nlp.variable('x', (3, 1), lb=0)[0]
            y = nlp.variable('y', (3, 1), lb=0)[0]
            z = nlp.variable('z', (3, 1), lb=0)[0]
            nlp.minimize(cs.sum1(cs.vertcat(x, y, z)))
            nlp.constraint(
                'c1', x.T @ [25, 15, 75] + 3 * cs.sqrt(cs.sumsqr(x)), '<=', 56)
            nlp.constraint(
                'c2', y.T @ [75, 3, 3] + 3 * cs.sqrt(cs.sumsqr(y)), '<=', 87)
            nlp.constraint(
                'c3', z.T @ [15, 22, 4] + 3 * cs.sqrt(cs.sumsqr(z)), '<=', 38)
            nlp.init_solver(OPTS)
            sol = nlp.solve()
            for (name, v) in [('x', x), ('y', y), ('z', z)]:
                val1 = sol.vals[name]
                val2 = sol.value(v)
                val3 = sol.value(nlp.variables[name])
                val4 = sol.value(nlp._vars[name])
                np.testing.assert_allclose(val1, val2, atol=1e-9)
                np.testing.assert_allclose(val2, val3, atol=1e-9)
                np.testing.assert_allclose(val3, val4, atol=1e-9)


if __name__ == '__main__':
    unittest.main()
