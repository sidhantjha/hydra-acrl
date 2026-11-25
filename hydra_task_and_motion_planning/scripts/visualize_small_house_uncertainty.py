from collections import defaultdict
import heapq
import math
import csv

import numpy as np
import matplotlib.pyplot as plt
import spark_dsg as dsg


from _paths import MODULE, experiment_args, output_path

args = experiment_args(outputs=True, start="p13061", goal="p2473")
GRAPH_PATH = args.dsg

OUTPUT_DIR = args.output_dir or MODULE / "results"

START = args.start
GOAL = args.goal

MAX_DZ = 0.8

ROBOT_RADIUS = 0.15
CONTROL_MARGIN = 0.10

UNCERTAINTIES = [
    0.15,
    0.25,
    0.35,
    0.45,
    0.55,
    0.65,
    0.75,
    0.85,
    0.95,
]


def node_id(value):
    if hasattr(value, "str"):
        return value.str()

    return dsg.NodeSymbol(value).str()


def distance(a, b, positions):
    return float(
        np.linalg.norm(
            positions[a][:2] - positions[b][:2]
        )
    )


def astar(
    start,
    goal,
    adjacency,
    positions,
    clearance,
    threshold,
):
    queue = []
    counter = 0

    heapq.heappush(
        queue,
        (
            distance(start, goal, positions),
            counter,
            start,
        ),
    )

    g_score = {start: 0.0}
    parent = {}

    while queue:
        _, _, current = heapq.heappop(queue)

        if current == goal:
            path = [current]

            while current in parent:
                current = parent[current]
                path.append(current)

            return list(reversed(path))

        for neighbor in adjacency[current]:

            if (
                neighbor not in (start, goal)
                and clearance[neighbor] < threshold
            ):
                continue

            new_cost = (
                g_score[current]
                + distance(current, neighbor, positions)
            )

            if new_cost >= g_score.get(neighbor, math.inf):
                continue

            g_score[neighbor] = new_cost
            parent[neighbor] = current

            counter += 1

            heuristic = distance(
                neighbor,
                goal,
                positions,
            )

            heapq.heappush(
                queue,
                (
                    new_cost + heuristic,
                    counter,
                    neighbor,
                ),
            )

    return None


def path_length(path, positions):
    return sum(
        distance(a, b, positions)
        for a, b in zip(path[:-1], path[1:])
    )


def min_clearance(path, clearance):
    nodes = path[1:-1] if len(path) > 2 else path

    return min(
        clearance[n]
        for n in nodes
    )


graph = dsg.DynamicSceneGraph.load(str(GRAPH_PATH))
layer = graph.get_layer(3)

positions = {}
clearance = {}

for node in layer.nodes:
    nid = node.id.str()

    positions[nid] = np.asarray(
        node.attributes.position,
        dtype=float,
    )

    clearance[nid] = float(
        node.attributes.distance
    )


adj = defaultdict(set)
edges = []

for edge in layer.edges:
    a = node_id(edge.source)
    b = node_id(edge.target)

    if abs(
        positions[a][2]
        - positions[b][2]
    ) > MAX_DZ:
        continue

    adj[a].add(b)
    adj[b].add(a)
    edges.append((a, b))


results = []

for uncertainty in UNCERTAINTIES:

    required = (
        ROBOT_RADIUS
        + CONTROL_MARGIN
        + uncertainty
    )

    path = astar(
        START,
        GOAL,
        adj,
        positions,
        clearance,
        required,
    )

    if path is None:
        results.append(
            {
                "uncertainty": uncertainty,
                "required_clearance": required,
                "path": None,
                "length": None,
                "min_clearance": None,
            }
        )
        continue

    results.append(
        {
            "uncertainty": uncertainty,
            "required_clearance": required,
            "path": path,
            "length": path_length(
                path,
                positions,
            ),
            "min_clearance": min_clearance(
                path,
                clearance,
            ),
        }
    )


print("=" * 78)
print("SMALL HOUSE UNCERTAINTY SWEEP")
print("=" * 78)

for r in results:

    if r["path"] is None:
        print(
            f"U={r['uncertainty']:.2f} m | "
            f"required={r['required_clearance']:.2f} m | "
            f"NO CERTIFIED PATH"
        )
    else:
        print(
            f"U={r['uncertainty']:.2f} m | "
            f"required={r['required_clearance']:.2f} m | "
            f"{len(r['path'])} nodes | "
            f"length={r['length']:.3f} m | "
            f"bottleneck={r['min_clearance']:.3f} m"
        )


csv_path = output_path(OUTPUT_DIR, "uncertainty_sweep.csv")
figure_path = output_path(OUTPUT_DIR, "small_house_uncertainty_routes.png")

with open(csv_path, "x", newline="") as f:
    writer = csv.writer(f)

    writer.writerow(
        [
            "perception_uncertainty_m",
            "required_clearance_m",
            "path_nodes",
            "path_length_m",
            "bottleneck_clearance_m",
        ]
    )

    for r in results:
        writer.writerow(
            [
                r["uncertainty"],
                r["required_clearance"],
                (
                    len(r["path"])
                    if r["path"]
                    else 0
                ),
                r["length"],
                r["min_clearance"],
            ]
        )


plt.figure(figsize=(11, 8))

for a, b in edges:
    pa = positions[a]
    pb = positions[b]

    plt.plot(
        [pa[0], pb[0]],
        [pa[1], pb[1]],
        linewidth=0.5,
        alpha=0.15,
    )


unique_routes = {}

for r in results:
    if r["path"] is None:
        continue

    key = tuple(r["path"])

    if key not in unique_routes:
        unique_routes[key] = r


for r in unique_routes.values():

    xy = np.asarray(
        [
            positions[n][:2]
            for n in r["path"]
        ]
    )

    plt.plot(
        xy[:, 0],
        xy[:, 1],
        marker="o",
        linewidth=2.5,
        label=(
            f"required={r['required_clearance']:.2f} m, "
            f"L={r['length']:.2f} m, "
            f"min={r['min_clearance']:.2f} m"
        ),
    )


plt.scatter(
    positions[START][0],
    positions[START][1],
    s=120,
    marker="*",
    label="Start",
)

plt.scatter(
    positions[GOAL][0],
    positions[GOAL][1],
    s=120,
    marker="X",
    label="Goal",
)

plt.xlabel("X [m]")
plt.ylabel("Y [m]")

plt.title(
    "Hydra Small House: "
    "Uncertainty-Aware Route Switching"
)

plt.axis("equal")
plt.grid(alpha=0.2)
plt.legend()
plt.tight_layout()


plt.savefig(
    figure_path,
    dpi=250,
    bbox_inches="tight",
)

print("\nSaved:")
print(figure_path)
print(csv_path)
