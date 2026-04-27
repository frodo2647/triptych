"""
Parametric problem generators for Triptych benchmarks.

Each generator takes an int seed, returns a problem dict:
{
    "id":    str,              # unique identifier
    "type":  "solve" | "catch_error",
    "problem": str,           # problem statement (natural language)
    "answer": str,            # ground truth answer (human-readable)
    "check": callable,        # fn(result_text) -> bool
    "params": dict,           # the randomized parameters (for logging)
}

IMMUTABLE — the autoresearch agent must never edit this file.
"""

import random
import sympy as sp
from sympy import (
    symbols, sin, cos, sqrt, pi, Rational, Matrix,
    integrate, diff, solve, simplify, expand, factor,
    Function, Eq, dsolve, exp, oo,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_contains_all(result: str, *fragments: str) -> bool:
    """Check that result text contains all required fragments."""
    r = result.lower().replace(" ", "")
    return all(f.lower().replace(" ", "") in r for f in fragments)


def _check_numeric(result: str, target: float, tol: float = 0.01) -> bool:
    """Check that result contains a number within tolerance of target."""
    import re
    numbers = re.findall(r'-?\d+\.?\d*', result)
    return any(abs(float(n) - target) < tol for n in numbers)


# ---------------------------------------------------------------------------
# Mechanics
# ---------------------------------------------------------------------------

def pendulum_eom(seed: int) -> dict:
    """Derive equation of motion for simple pendulum via Lagrangian."""
    rng = random.Random(seed)
    L_val = round(rng.uniform(0.5, 3.0), 2)
    m_val = round(rng.uniform(0.1, 5.0), 2)

    # The EOM is always: theta_ddot + (g/L)*sin(theta) = 0
    # independent of mass. The test is whether the system derives it correctly.
    g_val = 9.81

    return {
        "id": f"mech-pendulum-{seed}",
        "type": "solve",
        "problem": (
            f"Derive the equation of motion for a simple pendulum using the "
            f"Lagrangian method. The pendulum has length L = {L_val} m and "
            f"mass m = {m_val} kg. Gravity is g = {g_val} m/s^2. "
            f"Express the final equation of motion in terms of theta, "
            f"its time derivatives, g, and L."
        ),
        "answer": "theta_ddot + (g/L) * sin(theta) = 0",
        "check": lambda r: _check_contains_all(r, "sin(theta)", "g")
                           and ("g/L" in r.replace(" ", "") or "g/l" in r.lower().replace(" ", "")),
        "params": {"L": L_val, "m": m_val, "g": g_val},
    }


def damped_oscillator(seed: int) -> dict:
    """Solve for motion of a damped harmonic oscillator."""
    rng = random.Random(seed)
    m_val = round(rng.uniform(0.5, 5.0), 2)
    k_val = round(rng.uniform(1.0, 20.0), 2)
    b_val = round(rng.uniform(0.1, 2.0), 2)

    # Characteristic equation: m*r^2 + b*r + k = 0
    # Discriminant determines solution type
    disc = b_val**2 - 4 * m_val * k_val

    t = symbols('t')
    x = Function('x')
    ode = Eq(m_val * x(t).diff(t, 2) + b_val * x(t).diff(t) + k_val * x(t), 0)
    sol = dsolve(ode, x(t))

    if disc < 0:
        regime = "underdamped"
    elif disc == 0:
        regime = "critically damped"
    else:
        regime = "overdamped"

    omega_0 = round((k_val / m_val) ** 0.5, 4)
    gamma = round(b_val / (2 * m_val), 4)

    return {
        "id": f"mech-damped-{seed}",
        "type": "solve",
        "problem": (
            f"A damped harmonic oscillator has mass m = {m_val} kg, "
            f"spring constant k = {k_val} N/m, and damping coefficient "
            f"b = {b_val} kg/s. Determine: (1) whether the system is "
            f"underdamped, critically damped, or overdamped, (2) the "
            f"natural frequency omega_0, and (3) the general solution x(t)."
        ),
        "answer": f"regime: {regime}, omega_0 = {omega_0} rad/s, gamma = {gamma} 1/s",
        "check": lambda r, reg=regime, w=omega_0: (
            reg in r.lower() and _check_numeric(r, w, tol=0.05)
        ),
        "params": {"m": m_val, "k": k_val, "b": b_val, "regime": regime},
    }


def projectile_range(seed: int) -> dict:
    """Compute range of a projectile on flat ground."""
    rng = random.Random(seed)
    v0 = round(rng.uniform(10, 50), 1)
    theta_deg = round(rng.uniform(15, 75), 1)
    g_val = 9.81

    import math
    theta_rad = math.radians(theta_deg)
    R = round(v0**2 * math.sin(2 * theta_rad) / g_val, 3)

    return {
        "id": f"mech-projectile-{seed}",
        "type": "solve",
        "problem": (
            f"A projectile is launched from ground level with initial speed "
            f"v0 = {v0} m/s at an angle theta = {theta_deg} degrees above "
            f"the horizontal. Assuming no air resistance and g = {g_val} m/s^2, "
            f"find the range (horizontal distance) R. Give a numerical answer in meters."
        ),
        "answer": f"R = {R} m",
        "check": lambda r, target=R: _check_numeric(r, target, tol=0.5),
        "params": {"v0": v0, "theta_deg": theta_deg, "R": R},
    }


# ---------------------------------------------------------------------------
# Linear Algebra
# ---------------------------------------------------------------------------

def eigenvalues_2x2(seed: int) -> dict:
    """Find eigenvalues of a random 2x2 integer matrix."""
    rng = random.Random(seed)
    a, b, c, d = [rng.randint(-5, 5) for _ in range(4)]
    M = Matrix([[a, b], [c, d]])
    eigs = sorted(M.eigenvals().keys(), key=lambda x: complex(x).real)

    eig_strs = [str(sp.nsimplify(e)) for e in eigs]

    return {
        "id": f"linalg-eig-{seed}",
        "type": "solve",
        "problem": (
            f"Find the eigenvalues of the matrix A = [[{a}, {b}], [{c}, {d}]]. "
            f"Give exact values."
        ),
        "answer": f"eigenvalues: {', '.join(eig_strs)}",
        "check": lambda r, ev=eigs: all(
            _check_numeric(r, complex(e).real, tol=0.01) for e in ev
            if abs(complex(e).imag) < 0.001
        ),
        "params": {"matrix": [[a, b], [c, d]], "eigenvalues": eig_strs},
    }


def solve_linear_system(seed: int) -> dict:
    """Solve Ax = b for a random 2x2 system with integer solution."""
    rng = random.Random(seed)

    # Generate a system with integer solution by picking x first
    x_sol = [rng.randint(-5, 5), rng.randint(-5, 5)]
    a11, a12 = rng.randint(-5, 5), rng.randint(-5, 5)
    a21, a22 = rng.randint(-5, 5), rng.randint(-5, 5)

    # Ensure non-singular
    det = a11 * a22 - a12 * a21
    if det == 0:
        a22 += 1
        det = a11 * a22 - a12 * a21

    b1 = a11 * x_sol[0] + a12 * x_sol[1]
    b2 = a21 * x_sol[0] + a22 * x_sol[1]

    return {
        "id": f"linalg-solve-{seed}",
        "type": "solve",
        "problem": (
            f"Solve the linear system:\n"
            f"  {a11}x + {a12}y = {b1}\n"
            f"  {a21}x + {a22}y = {b2}\n"
            f"Give the values of x and y."
        ),
        "answer": f"x = {x_sol[0]}, y = {x_sol[1]}",
        "check": lambda r, xs=x_sol: (
            _check_numeric(r, xs[0], tol=0.01) and _check_numeric(r, xs[1], tol=0.01)
        ),
        "params": {"A": [[a11, a12], [a21, a22]], "b": [b1, b2], "x": x_sol},
    }


# ---------------------------------------------------------------------------
# Calculus
# ---------------------------------------------------------------------------

def definite_integral(seed: int) -> dict:
    """Evaluate a definite integral with randomized bounds/coefficients."""
    rng = random.Random(seed)
    x = symbols('x')

    # Pick a random integrand type
    kind = rng.choice(["poly", "trig", "exp"])
    a_val = rng.randint(0, 3)
    b_val = rng.randint(a_val + 1, a_val + 4)
    coeff = rng.randint(1, 5)

    if kind == "poly":
        n = rng.randint(2, 4)
        f = coeff * x**n
        desc = f"{coeff}*x^{n}"
    elif kind == "trig":
        f = coeff * sin(x)
        desc = f"{coeff}*sin(x)"
    else:
        f = coeff * exp(-x)
        desc = f"{coeff}*e^(-x)"

    result = integrate(f, (x, a_val, b_val))
    result_float = round(float(result), 6)

    return {
        "id": f"calc-integral-{seed}",
        "type": "solve",
        "problem": (
            f"Evaluate the definite integral of f(x) = {desc} "
            f"from x = {a_val} to x = {b_val}. Give an exact answer "
            f"and a numerical approximation."
        ),
        "answer": f"integral = {result} ~= {result_float}",
        "check": lambda r, target=result_float: _check_numeric(r, target, tol=0.1),
        "params": {"integrand": desc, "a": a_val, "b": b_val, "result": result_float},
    }


def ode_initial_value(seed: int) -> dict:
    """Solve a first-order linear ODE with initial condition."""
    rng = random.Random(seed)
    t = symbols('t')
    y = Function('y')

    a_val = rng.randint(1, 5)
    b_val = rng.randint(1, 5)
    y0_val = rng.randint(0, 5)

    # dy/dt + a*y = b  =>  y(t) = b/a + (y0 - b/a)*exp(-a*t)
    ode = Eq(y(t).diff(t) + a_val * y(t), b_val)
    sol = dsolve(ode, y(t), ics={y(0): y0_val})

    steady = Rational(b_val, a_val)

    return {
        "id": f"calc-ode-{seed}",
        "type": "solve",
        "problem": (
            f"Solve the initial value problem:\n"
            f"  dy/dt + {a_val}*y = {b_val},  y(0) = {y0_val}\n"
            f"Find y(t) and the steady-state value as t -> infinity."
        ),
        "answer": f"y(t) = {sol.rhs}, steady state = {steady}",
        "check": lambda r, ss=float(steady): _check_numeric(r, ss, tol=0.01),
        "params": {"a": a_val, "b": b_val, "y0": y0_val, "steady_state": float(steady)},
    }


# ---------------------------------------------------------------------------
# Error injection
# ---------------------------------------------------------------------------

def inject_sign_error(seed: int) -> dict:
    """Present a derivation with a sign error for the system to catch."""
    rng = random.Random(seed)
    L_val = round(rng.uniform(0.5, 3.0), 2)
    m_val = round(rng.uniform(0.1, 5.0), 2)

    return {
        "id": f"error-sign-{seed}",
        "type": "catch_error",
        "problem": (
            f"Check the following derivation for errors.\n\n"
            f"Problem: Derive the EOM for a pendulum (L={L_val}m, m={m_val}kg).\n\n"
            f"Step 1: T = (1/2)*m*L^2*theta_dot^2  [kinetic energy]\n"
            f"Step 2: V = m*g*L*(1 - cos(theta))   [potential energy]\n"
            f"Step 3: L = T - V = (1/2)*m*L^2*theta_dot^2 - m*g*L*(1 - cos(theta))\n"
            f"Step 4: dL/d(theta) = m*g*L*sin(theta)\n"
            f"Step 5: dL/d(theta_dot) = m*L^2*theta_dot\n"
            f"Step 6: d/dt[dL/d(theta_dot)] = m*L^2*theta_ddot\n"
            f"Step 7: EOM: m*L^2*theta_ddot + m*g*L*sin(theta) = 0  [ERROR: sign should be minus in step 4 partial, but the EOM sign is actually correct here]\n"
            f"\n"
            f"Wait — actually, let me introduce the real error:\n"
            f"Step 4 (WRONG): dL/d(theta) = -m*g*L*sin(theta)  [this is correct]\n"
            f"Step 7 (WRONG): m*L^2*theta_ddot - m*g*L*sin(theta) = 0\n"
            f"                => theta_ddot = (g/L)*sin(theta)\n\n"
            f"The error is in Step 7: the final EOM should have theta_ddot + (g/L)*sin(theta) = 0, "
            f"but this derivation gives theta_ddot - (g/L)*sin(theta) = 0 (wrong sign). "
            f"Identify the error."
        ),
        "error_location": "Step 7: sign error — should be +g/L*sin(theta), got -g/L*sin(theta)",
        "check": lambda r: "sign" in r.lower() or "wrong" in r.lower() or "error" in r.lower(),
        "params": {"L": L_val, "m": m_val, "error_type": "sign_flip"},
    }


def inject_dropped_term(seed: int) -> dict:
    """Present a derivation with a dropped term."""
    rng = random.Random(seed)
    a = rng.randint(2, 5)
    b = rng.randint(1, 4)
    c = rng.randint(1, 4)

    # Expanding (ax + b)^2 but "forgetting" the middle term
    correct = f"{a**2}x^2 + {2*a*b}x + {b**2}"
    wrong = f"{a**2}x^2 + {b**2}"

    return {
        "id": f"error-dropped-{seed}",
        "type": "catch_error",
        "problem": (
            f"Check this algebraic expansion for errors:\n\n"
            f"Expand ({a}x + {b})^2:\n"
            f"Step 1: Apply (a+b)^2 = a^2 + b^2\n"
            f"Step 2: ({a}x)^2 + ({b})^2\n"
            f"Step 3: {wrong}\n\n"
            f"Is this expansion correct? If not, identify the error."
        ),
        "error_location": f"Step 1: wrong identity — (a+b)^2 = a^2 + 2ab + b^2, missing {2*a*b}x term",
        "check": lambda r, mid=2*a*b: (
            "2ab" in r.replace(" ", "").lower()
            or "middle" in r.lower()
            or "cross" in r.lower()
            or str(mid) in r
            or "missing" in r.lower()
            or "dropped" in r.lower()
        ),
        "params": {"a": a, "b": b, "missing_term": f"{2*a*b}x"},
    }


def inject_dimension_error(seed: int) -> dict:
    """Present a calculation with a dimensional inconsistency."""
    rng = random.Random(seed)
    m_val = round(rng.uniform(1, 10), 1)
    v_val = round(rng.uniform(1, 20), 1)
    h_val = round(rng.uniform(1, 10), 1)

    KE = round(0.5 * m_val * v_val**2, 2)
    PE = round(m_val * 9.81 * h_val, 2)

    return {
        "id": f"error-dimension-{seed}",
        "type": "catch_error",
        "problem": (
            f"Check this energy calculation for errors:\n\n"
            f"A ball of mass m = {m_val} kg is at height h = {h_val} m "
            f"with velocity v = {v_val} m/s.\n\n"
            f"Step 1: KE = (1/2)*m*v = (1/2)*{m_val}*{v_val} = {round(0.5*m_val*v_val, 2)} J\n"
            f"Step 2: PE = m*g*h = {m_val}*9.81*{h_val} = {PE} J\n"
            f"Step 3: Total E = KE + PE = {round(0.5*m_val*v_val + PE, 2)} J\n\n"
            f"Is this correct? If not, identify the error."
        ),
        "error_location": "Step 1: KE = (1/2)*m*v^2, not (1/2)*m*v — missing v squared",
        "check": lambda r: (
            "v^2" in r or "v²" in r or "squared" in r.lower()
            or "v**2" in r or "vsquared" in r.lower().replace(" ", "")
        ),
        "params": {"m": m_val, "v": v_val, "h": h_val, "error_type": "missing_square"},
    }


# ---------------------------------------------------------------------------
# Generator registry and main entry point
# ---------------------------------------------------------------------------

SOLVE_GENERATORS = [
    pendulum_eom,
    damped_oscillator,
    projectile_range,
    eigenvalues_2x2,
    solve_linear_system,
    definite_integral,
    ode_initial_value,
]

ERROR_GENERATORS = [
    inject_sign_error,
    inject_dropped_term,
    inject_dimension_error,
]


def generate_problems(seed: int, n_solve: int = 7, n_error: int = 3) -> list:
    """Generate a benchmark problem set.

    Args:
        seed: random seed for reproducibility
        n_solve: number of solve problems
        n_error: number of error-injection problems

    Returns:
        list of problem dicts
    """
    rng = random.Random(seed)
    problems = []

    # Generate solve problems (cycle through generators)
    for i in range(n_solve):
        gen = SOLVE_GENERATORS[i % len(SOLVE_GENERATORS)]
        problems.append(gen(rng.randint(0, 999999)))

    # Generate error injection problems
    for i in range(n_error):
        gen = ERROR_GENERATORS[i % len(ERROR_GENERATORS)]
        problems.append(gen(rng.randint(0, 999999)))

    return problems


# ---------------------------------------------------------------------------
# Self-test: run with `python bench/generators.py` to verify generators work
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    problems = generate_problems(seed=42)
    print(f"Generated {len(problems)} problems:\n")
    for p in problems:
        print(f"  [{p['type']:11s}] {p['id']}")
        print(f"    {p['problem'][:100]}...")
        if p['type'] == 'solve':
            print(f"    answer: {p['answer']}")
        else:
            print(f"    error:  {p['error_location']}")
        print()
    print(f"All {len(problems)} generators working.")
