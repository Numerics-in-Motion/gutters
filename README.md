# Gutters: design capacity of an eaves gutter, and the water in it

Code-based design capacity of eaves gutters (BS EN 12056-3:2000, clauses 5.1.2 and 5.1.6) and an idealised
steady water profile along a gutter that collects rain over its length. Standard-library Python only.

`gutter_capacity.py` is the rig's solver (plain functions):

* `q_n`, `arm_capacity`: Q_N = 2.78e-5 A_E^1.25 L/s and, for an eaves gutter, Q = 0.9 Q_N F_L, with the length
  factor F_L of a nominally level gutter from **Table 6** (linear interpolation of the printed level column) or from
  **SR620's equations (6.8)/(6.9)**; the two are kept as separate representations;
* `total_capacity`: a gutter with one outlet and two stop ends has two arms; each arm's drainage length runs from the
  outlet to its stop end. With uniform inflow along the whole gutter, the largest total both arms carry at their design
  capacity is `min_i Q_arm(L_i) x L_total / L_i`. The outlet is assumed adequate (free discharge): this is a
  **gutter-only** design capacity;
* `profile`: steady spatially varied flow with lateral inflow (momentum form, RK4), from 1.02 y_c (y_c: critical
  depth) at a free terminal section to the stop end. Used for pictures only: the outlet junction, water leaving over the rim and
  the filling transient are not modelled.

```sh
python -m pip install -r requirements.txt     # nothing to install: standard library only
python reproduce.py
```

`reproduce.py` checks the solver against printed examples and against `reference/rig_reference.json`:

| check | this rig | printed |
|---|---|---|
| SR620 worked example 2: 150 mm true half-round, level, 12.5 m, Q_N | 2.381 L/s | 2.38 L/s |
| the same, design capacity (SR620 equations / Table 6) | 1.810 / 1.800 L/s | 1.81 L/s |
| AEC Assistant long-eaves-gutter example: critical depth at the outlet | 37.0 mm | 37.0 mm |
| the same, maximum depth (10,000 and 40,000 steps agree to 1e-6 mm) | 56.6 mm | 56.6 mm |
| Table 6 vs SR620's equations over the printed rows | largest difference 0.0067 | |

## Studies on this rig

* [`move-one-outlet/`](move-one-outlet/) — the same straight gutter built from the same 4 m lengths, with its one
  outlet near the end, off-centre or at the centre: how much more rain can the same gutter take?

## Sources

| what | where |
|---|---|
| BS EN 12056-3:2000 5.1.2, 5.1.6, Table 6 (secondary OCR transcription) | https://paperzz.com/doc/9168042/en-12056-3 |
| HR Wallingford SR620: worked example 2, drainage length per arm, equations (6.8)/(6.9) in 6.1.6 (secondary HTML transcription) | https://www.scribd.com/document/691751758/Manual-Roof-Drainage-System-HRWallingford-SR620 |
| Spatially varied flow benchmark: AEC Assistant long-eaves-gutter calculator, its own example | https://www.aecassistant.com.au/tools/long-eaves-gutter-calculator |

## Scope

Code design capacities of an idealised, straight, level eaves gutter. Not a rating of any product, outlet or
downpipe, and not an assessment of any real roof.
