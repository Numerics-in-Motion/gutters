# Move one outlet: how much more rain can the same gutter take?

One straight, level eaves gutter made of the **same** 4 m lengths, unions, two stop ends and **one** running outlet.
Only the outlet's position changes; it swaps places with a union:

| arrangement | outlet | arms (six lengths, 24 m) |
|---|---|---|
| near the end | after one length | 4 m + 20 m |
| off-centre | after two lengths | 8 m + 16 m |
| centre | at the middle union | 12 m + 12 m |

The quantity is the **gutter-only design capacity, outlet assumed adequate**: the largest uniform total inflow (L/s)
that both arms carry at their BS EN 12056-3:2000 design capacity (5.1.2, 5.1.6; Table 6, nominally level column,
applied to each arm's drainage length from the outlet to its stop end). No rainfall intensity is chosen.

Section: the **idealised 150 mm true half-round of SR620's worked example 2** (W 75 mm, A_E 8835.73 mm2). It is a
worked-example section, not the profile of any product. The 4 m length is a common stock length of 150 mm half-round
PVC-U gutter (a manufacturer's product page, below); nothing else is taken from any product.

```sh
python reproduce.py      # a few seconds; standard library only
```

## Result

| lengths | F_L from | near the end | off-centre | centre (L/s) | centre / near the end |
|---|---|---|---|---|---|
| 6 (24 m) | Table 6 | 1.946 | 2.538 | 3.635 | x1.868 |
| 6 (24 m) | SR620 equations | 1.943 | 2.543 | 3.658 | x1.882 |
| 8 (32 m) | Table 6 | 1.669 | 2.063 | 3.384 | x2.027 |
| 10 (40 m) | Table 6 | 1.467 | 1.738 | 3.244 | x2.211 |

Worst case over 6, 8 and 10 lengths, both representations, the 5.3.3 strainer reduction (common to all, ratios
unchanged) and independent +-0.15 m shifts of each outlet (an illustrative stress, not a fitting dimension):
**off-centre / near the end x1.168, centre / off-centre x1.395, centre / near the end x1.822.** The numerical bound
of the calculation (Table 6 printed to two decimals, +-0.005 on the smallest F_L used, 0.614) is u = 0.81 %, so a pair
needs max(10 %, 3u) = 10 %; all three clear it and none reverses. Every arm's L/W (51-482) is inside Table 6.

Why: each arm drains its own share of the rain, and the longest arm governs. Moving the outlet shortens the longest
run to the outlet from 20 m to 16 m to 12 m. With the length factor switched off (F_L = 1) the ratios would be x1.25,
x1.333 and x1.667, so most of the gain is that geometry; Table 6's length factor adds the rest.

Controls: an outlet after five lengths gives exactly the near-the-end result (mirror); the outlet reference plane
taken at a lip instead of the centreline (h = 0-0.15 m, common to all) changes the ratios by at most 0.001.

## The water drawn in the video

An idealised steady profile in each arm (`gutter_capacity.profile`): uniform lateral inflow, level, Manning n 0.009-
0.011 (PVC with smooth inner walls, Engineering ToolBox, secondary), each arm ending at an ideal free terminal section
at the outlet. At each arrangement's capacity the deepest point reaches 59.5-62.5 mm of the 75 mm depth. It is a
picture of the calculation, not a prediction: the outlet junction, water leaving over the rim and the filling
transient are not modelled.

## Sources

| what | where |
|---|---|
| BS EN 12056-3:2000 5.1.2, 5.1.6, 5.3.3, Table 6 (secondary OCR transcription) | https://paperzz.com/doc/9168042/en-12056-3 |
| HR Wallingford SR620: worked example 2 (150 mm true half-round), drainage length per arm, equations (6.8)/(6.9) (secondary HTML transcription) | https://www.scribd.com/document/691751758/Manual-Roof-Drainage-System-HRWallingford-SR620 |
| 4 m lengths of 150 mm half-round PVC-U gutter (manufacturer's product page) | https://wavin.com/gb/p/e7f44307-a623-4e54-a83c-4bf9db76abcd/osrroo-pvcu-gutter-gy-150-l4 |
| Manning n 0.009-0.011, PVC with smooth inner walls (secondary) | https://www.engineeringtoolbox.com/mannings-roughness-d_799.html |
| Profile benchmark (reproduced by the rig): AEC Assistant long-eaves-gutter calculator | https://www.aecassistant.com.au/tools/long-eaves-gutter-calculator |

## Scope

Gutter-only design capacities under one code method; the outlet, downpipe, supports, sag and any real roof are not
assessed. Level, section and position are imposed.
