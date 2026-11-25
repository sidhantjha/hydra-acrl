# Hydra-ACRL task and motion planning

`swarmx_planning.graph_io` opens Spark-DSG JSON, and `places` extracts PLACES positions, clearances and edges. The reusable A* planner uses XYZ distance. The Small House search and static route visualization use XY distance with a 0.8 m vertical edge-displacement filter. The animations use NetworkX weighted shortest paths.

`PlanningCertificate` adds robot radius, control margin and a synthetic uncertainty allowance to set the required clearance. The constraint applies to interior nodes. Historical endpoint exemptions and goal selection are retained. The experiment evaluates route switching and infeasibility on graph data. Goal `p2473` is at z = 1.5 m, and edge filtering does not validate a traversable floor, swept path clearance or controller execution.

## CPU setup

Use Python 3.12 and `./setup.sh` from this module. Add `--viz` for plots and GIFs. The default builds the vendored Spark-DSG 1.1.3 Python binding with CMake, a C++ compiler, Eigen headers and pybind11. A verified compatible wheel can be supplied with `--spark-wheel /path/to/wheel.whl`. The script uses an isolated `.venv`, with `PLANNING_VENV` available to choose another path. ROS, Gazebo, CUDA and TensorRT are unnecessary for saved graphs.

The audit observed Python 3.12.3, NumPy 1.26.4, NetworkX 3.6.1, Matplotlib 3.6.3 and Pillow 10.2.0. The optional package dependency uses a Python 3.12-compatible Matplotlib range. A fresh Python 3.12 installation and all four regressions passed with the release package.

## Saved graphs and experiments

From this module, set `DSG` to an absolute path. The historical reference is local at `experiments/small_house/run_01/dsg.json`. Its size is 556,994 bytes and SHA256 is `fd98e8f2281006792a7f9ae60f42cdfac2b99c1ec47d4055d45db2ae4ecea392`. Its companion PNG and CSV remain local pending provenance review. Supply an authorized copy to run the regressions. An exported DSG from live mapping works as input for graph inspection and planning.

```bash
DSG="$PWD/experiments/small_house/run_01/dsg.json"
OUT="$PWD/results/reference-01"
.venv/bin/python scripts/inspect_small_house.py --dsg "$DSG"
.venv/bin/python scripts/find_small_house_route_switch.py --dsg "$DSG" --start p13061
MPLBACKEND=Agg .venv/bin/python scripts/visualize_small_house_uncertainty.py --dsg "$DSG" --start p13061 --goal p2473 --output-dir "$OUT"
.venv/bin/python -B -I -m unittest discover -s tests -v
```

| Entry point | Example arguments | Output |
| --- | --- | --- |
| [inspect_small_house.py](scripts/inspect_small_house.py) | `--dsg "$DSG"` | Graph and PLACES statistics, node IDs and connected components |
| [sweep_uncertainty.py](scripts/sweep_uncertainty.py) | `--dsg "$DSG"` | XYZ clearance-constrained A* costs, route changes and feasibility |
| [find_small_house_route_switch.py](scripts/find_small_house_route_switch.py) | `--dsg "$DSG" --start p13061` | XY search for a goal that illustrates route switching |
| [visualize_astar.py](scripts/visualize_astar.py) | `--dsg "$DSG" --output-dir "$OUT"` | XYZ route figure, or an interactive plot when the output option is omitted |
| [visualize_small_house_uncertainty.py](scripts/visualize_small_house_uncertainty.py) | `--dsg "$DSG" --start p13061 --goal p2473 --output-dir "$OUT"` | XY route PNG and sweep CSV |
| [animate_small_house_routes.py](scripts/animate_small_house_routes.py) | `--dsg "$DSG" --start p13061 --goal p2473 --output-dir "$OUT"` | 2D GIF and MP4 when ffmpeg is available |
| [animate_small_house_routes_3d.py](scripts/animate_small_house_routes_3d.py) | `--dsg "$DSG" --start p13061 --goal p2473 --output-dir "$OUT"` | 3D GIF of NetworkX routes |

Run the listed scripts with `.venv/bin/python scripts/SCRIPT.py`. Figure and animation scripts use the `--viz` dependencies and refuse to overwrite an existing output. Use valid PLACES IDs from your selected graph for fixed endpoints. The [uHumans2 notes](experiments/uhumans2/baseline_results.md) preserve the earlier historical baseline.

The reference had 246 PLACES nodes and 971 edges. For p13061 → p2473, increasing required clearance from 0.40 to 1.00 m increased XY route length from 11.493 to 12.428 m and interior clearance from 0.447 to 1.000 m. At 1.10 and 1.20 m the endpoints had no feasible route. See the [implementation report](../docs/IMPLEMENTATION_REPORT.md) for full precision.

## Experimental waypoint controller

The original ROS 2 controller is preserved under `src/swarmx_planning/control/`. It uses hardcoded waypoints and consumes no planned DSG paths. Historical simulation runs reported stalling. Its original launch is preserved as a reference, and the mapping launch does not invoke it. Running it would require separate ROS integration and authorization.
