# uHumans2 3DSG Planning Baseline

## Graph

- Place nodes: 1593
- Place edges: 5303
- Connected components: 13
- Largest component: 1554 nodes
- Largest-component coverage: 97.55%
- Mean node degree: 6.66
- Median node degree: 5
- Clearance range: 0.400 m to 3.162 m

## Planning pair

- Start: p1321
- Goal: p98505

## Deterministic shortest path

- Path length: 60.50 m
- Nodes: 27
- Minimum interior clearance: 0.447 m

## Clearance / uncertainty sweep

| Perception uncertainty | Required clearance | Route | Length | Interior min clearance |
|---|---:|---:|---:|---:|
| 0.15 m | 0.40 m | 0 | 60.50 m | 0.447 m |
| 0.35 m | 0.60 m | 1 | 61.06 m | 0.748 m |
| 0.55 m | 0.80 m | 2 | 61.48 m | 0.980 m |
| 0.75 m | 1.00 m | 3 | 61.84 m | 1.000 m |
| 0.95 m | 1.20 m | infeasible | - | - |

## Interpretation

Increasing assumed perception uncertainty increases the required clearance.
As the certified operating envelope tightens, the planner rejects narrow
routes and selects progressively wider alternatives. At sufficiently high
uncertainty, no route satisfies the clearance requirement.

Current perception uncertainty and control margin values are synthetic.
