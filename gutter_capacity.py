"""Gutters rig: design capacity of an eaves gutter (BS EN 12056-3:2000 5.1.2 / 5.1.6) and an idealised
spatially-varied-flow water profile along it. Plain functions, standard library only.

Capacity (the claim):
    Q_N = 2.78e-5 * A_E**1.25                     (L/s, A_E in mm2)       5.1.2
    Q   = 0.9 * Q_N * F_L                         (eaves gutter)           5.1.6
    F_L : length factor for a nominally level gutter (0-3 mm/m) as a function of L/W, Table 6; L is the drainage
          length of ONE arm (outlet to the adjacent stop end), W the gutter width (top), both in mm.
Two representations of F_L are kept: the printed Table 6 (level column, linear interpolation between rows) and the
straight-line equations (6.8)/(6.9) of HR Wallingford SR620 6.1.6 for the same relationship. They are run as separate calculations,
never mixed.

A gutter with one outlet and two stop ends has two arms. With a UNIFORM inflow along its whole length, arm i receives
Q_tot * L_i / L_tot, so the largest uniform total inflow both arms carry at their design capacity is
    Q_tot = min_i  Q_arm(L_i) * L_tot / L_i.
The outlet itself is assumed adequate (free discharge): this is a GUTTER-ONLY design capacity.

Water profile (the picture only): steady spatially varied flow with lateral inflow entering with no longitudinal
momentum,
    dy/dx = (S0 - Sf - 2 Q q / (g A^2)) / (1 - Q^2 B / (g A^3)),   Q = q x,   Sf = n^2 Q^2 / (A^2 R^(4/3)),
integrated (RK4) from the free terminal section at the outlet (started at 1.02 x critical depth) to the stop end.
The outlet is an ideal free terminal section for each arm; no junction, no overflow and no filling transient are
modelled.
"""
from __future__ import annotations

import math

G = 9.81

# BS EN 12056-3:2000 Table 6, nominally level gutters (0-3 mm/m): L/W -> F_L
TABLE6_LW = (50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400, 425, 450, 475, 500)
TABLE6_FL = (1.00, .97, .93, .90, .86, .83, .80, .78, .77, .75, .73, .72, .70, .68, .67, .65, .63, .62, .60)
LW_MAX = 500.0          # the table stops here; nothing is extrapolated


def fl_table(lw):
    """F_L from the printed Table 6 (level column), linear interpolation between rows."""
    if lw <= TABLE6_LW[0]:
        return 1.0
    if lw > LW_MAX:
        raise ValueError("L/W %.1f is beyond Table 6 (500); not extrapolated" % lw)
    for i in range(len(TABLE6_LW) - 1):
        a, b = TABLE6_LW[i], TABLE6_LW[i + 1]
        if a <= lw <= b:
            return TABLE6_FL[i] + (TABLE6_FL[i + 1] - TABLE6_FL[i]) * (lw - a) / (b - a)
    raise ValueError(lw)


def fl_equations(lw):
    """F_L from SR620 6.1.6, nominally level gutters: 1 for L/W <= 50, eq. (6.8) 1.0 - (0.2/150)(L/W - 50) for
    50 < L/W <= 200, eq. (6.9) 0.8 - (0.2/300)(L/W - 200) for 200 < L/W <= 500."""
    if lw <= 50:
        return 1.0
    if lw > LW_MAX:
        raise ValueError("L/W %.1f is beyond 500; not extrapolated" % lw)
    if lw <= 200:
        return 1.0 - 0.2 / 150.0 * (lw - 50.0)
    return 0.8 - 0.2 / 300.0 * (lw - 200.0)


FL = {"table": fl_table, "equations": fl_equations}


def sr620_half_round_150():
    """The idealised 150 mm true half-round gutter of SR620's worked example 2: A_E = the half circle of radius
    75 mm (8835.73 mm2) and W = 75 mm, the value that worked example uses in L/W (it reproduces the printed
    2.38 / 1.81 L/s). An idealised worked-example section, not any product's profile."""
    r = 75.0
    return {"W_mm": 75.0, "A_E_mm2": 0.5 * math.pi * r * r, "depth_mm": r, "radius_mm": r}


def q_n(a_e_mm2):
    """Nominal capacity of a short gutter, L/s (5.1.2)."""
    return 2.78e-5 * a_e_mm2 ** 1.25


def arm_capacity(arm_m, section, rep="table", strainer=False):
    """Design capacity of one arm of an eaves gutter, L/s (5.1.6). A strainer (5.3.3) halves it."""
    f = FL[rep](arm_m * 1000.0 / section["W_mm"])
    return (0.5 if strainer else 1.0) * 0.9 * q_n(section["A_E_mm2"]) * f


def total_capacity(arms_m, section, rep="table", strainer=False, lip_m=0.0):
    """Largest UNIFORM total inflow (L/s) a gutter with these arms carries with every arm at its design capacity.
    `lip_m` is the outlet half-width under the alternative 'lip' convention: each arm's drainage length is shortened
    by it while the arm still receives the rain on its full length (arm + lip)."""
    total = sum(arms_m) + 0.0
    return min(arm_capacity(a - lip_m, section, rep, strainer) * total / a for a in arms_m)


# ---- spatially varied flow profile (picture only) ----------------------------------------------------------------
def rect(width_m):
    return (lambda y: width_m * y, lambda y: width_m, lambda y: width_m * y / (width_m + 2 * y))


def half_round_flow(radius_m):
    """(area, top width, hydraulic radius) of the water in a half-round gutter at depth y (bottom at y = 0)."""
    def area(y):
        th = 2 * math.acos(1 - y / radius_m)
        return radius_m * radius_m * (th - math.sin(th)) / 2

    def top(y):
        return 2 * math.sqrt(max(radius_m * radius_m - (radius_m - y) ** 2, 1e-12))

    def hyd(y):
        th = 2 * math.acos(1 - y / radius_m)
        return area(y) / (radius_m * th)
    return area, top, hyd


def critical_depth(q_m3s, sec, ymax):
    area, top, _ = sec
    lo, hi = 1e-7, ymax
    for _ in range(90):
        m = 0.5 * (lo + hi)
        if q_m3s * q_m3s * top(m) / (G * area(m) ** 3) > 1:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


def profile(length_m, q_out_m3s, sec, slope, n, ymax, steps=20000):
    """Water depth along one arm with uniform lateral inflow, from the stop end (x = 0) to the outlet (x = length).
    Returns (xs, ys, yc): xs ascending from 0 to length (m), depths (m), critical depth at the outlet (m)."""
    area, top, hyd = sec
    q = q_out_m3s / length_m
    yc = critical_depth(q_out_m3s, sec, ymax)
    x, y = length_m, 1.02 * yc
    dx = -length_m / steps
    xs, ys = [x], [y]

    def f(x, y):
        Q = q * max(x, 0.0)
        a = area(y)
        sf = n * n * Q * Q / (a * a * hyd(y) ** (4 / 3))
        return (slope - sf - 2 * Q * q / (G * a * a)) / (1 - Q * Q * top(y) / (G * a ** 3))

    for _ in range(steps):
        k1 = f(x, y)
        k2 = f(x + dx / 2, y + dx / 2 * k1)
        k3 = f(x + dx / 2, y + dx / 2 * k2)
        k4 = f(x + dx, y + dx * k3)
        y += dx / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        x += dx
        xs.append(x)
        ys.append(y)
    xs.reverse()
    ys.reverse()
    xs[0] = 0.0
    return xs, ys, yc
