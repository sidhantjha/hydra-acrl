from collections import defaultdict
import heapq
import math

import numpy as np
import spark_dsg as dsg


from _paths import experiment_args

args = experiment_args(start="p13061")
GRAPH_PATH = args.dsg

START_ID = args.start

MAX_DZ = 0.8

CLEARANCE_THRESHOLDS = [
    0.40,
    0.50,
    0.60,
    0.70,
    0.80,
    0.90,
    1.00,
]


def nid(x):
    if hasattr(x, "str"):
        return x.str()
    return dsg.NodeSymbol(x).str()


def xy_distance(a, b, positions):
    return float(
        np.linalg.norm(
            positions[a][:2] - positions[b][:2]
        )
    )


def path_length(path, positions):
    return sum(
        xy_distance(a, b, positions)
        for a, b in zip(path[:-1], path[1:])
    )


def interior_min_clearance(path, clearance):
    if len(path) <= 2:
        values = path
    else:
        values = path[1:-1]

    return min(clearance[n] for n in values)


def astar(
    start,
    goal,
    adjacency,
    positions,
    clearance,
    min_clearance=None,
):
    queue = []
    counter = 0

    heapq.heappush(
        queue,
        (
            xy_distance(start, goal, positions),
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

            # Start/goal are always allowed.
            if (
                min_clearance is not None
                and neighbor != goal
                and neighbor != start
                and clearance[neighbor] < min_clearance
            ):
                continue

            tentative = (
                g_score[current]
                + xy_distance(current, neighbor, positions)
            )

            if tentative >= g_score.get(neighbor, math.inf):
                continue

            parent[neighbor] = current
            g_score[neighbor] = tentative

            counter += 1

            f = (
                tentative
                + xy_distance(neighbor, goal, positions)
            )

            heapq.heappush(
                queue,
                (f, counter, neighbor),
            )

    return None


# ------------------------------------------------------------
# Load graph
# ------------------------------------------------------------

graph = dsg.DynamicSceneGraph.load(str(GRAPH_PATH))
layer = graph.get_layer(3)

positions = {}
clearance = {}

for node in layer.nodes:
    node_id = node.id.str()

    positions[node_id] = np.asarray(
        node.attributes.position,
        dtype=float,
    )

    clearance[node_id] = float(
        getattr(node.attributes, "distance", np.nan)
    )


# ------------------------------------------------------------
# Ground-compatible topology filter
# ------------------------------------------------------------

adj = defaultdict(set)
kept_edges = 0

for edge in layer.edges:
    a = nid(edge.source)
    b = nid(edge.target)

    pa = positions[a]
    pb = positions[b]

    dz = abs(pa[2] - pb[2])

    if dz > MAX_DZ:
        continue

    adj[a].add(b)
    adj[b].add(a)

    kept_edges += 1


# ------------------------------------------------------------
# Find component containing canonical start
# ------------------------------------------------------------

if START_ID not in positions:
    raise SystemExit(f"Start node {START_ID} is missing. Select a node from this graph with --start.")

stack = [START_ID]
start_component = {START_ID}

while stack:
    u = stack.pop()

    for v in adj[u]:
        if v not in start_component:
            start_component.add(v)
            stack.append(v)


print("=" * 72)
print("SMALL HOUSE ROUTE-SWITCH SEARCH")
print("=" * 72)

print("\nTopology filter")
print("max |dz|:", MAX_DZ, "m")
print("edges kept:", kept_edges)

print("\nCanonical start")
print("id:", START_ID)
print("position:", positions[START_ID])
print("clearance:", clearance[START_ID])

print(
    "\nStart connected component:",
    len(start_component),
    "/",
    len(positions),
)


# ------------------------------------------------------------
# Search goals
# ------------------------------------------------------------

candidates = []

for goal in start_component:

    if goal == START_ID:
        continue

    direct_distance = xy_distance(
        START_ID,
        goal,
        positions,
    )

    # Ignore tiny local paths.
    if direct_distance < 4.0:
        continue

    baseline = astar(
        START_ID,
        goal,
        adj,
        positions,
        clearance,
        min_clearance=None,
    )

    if baseline is None:
        continue

    baseline_len = path_length(
        baseline,
        positions,
    )

    baseline_clearance = interior_min_clearance(
        baseline,
        clearance,
    )

    routes = []

    for threshold in CLEARANCE_THRESHOLDS:

        path = astar(
            START_ID,
            goal,
            adj,
            positions,
            clearance,
            min_clearance=threshold,
        )

        if path is None:
            routes.append(
                (threshold, None, None, None)
            )
            continue

        routes.append(
            (
                threshold,
                path,
                path_length(path, positions),
                interior_min_clearance(
                    path,
                    clearance,
                ),
            )
        )

    feasible = [
        r
        for r in routes
        if r[1] is not None
    ]

    if len(feasible) < 2:
        continue

    # Find a genuinely different route.
    alternatives = []

    for threshold, path, length, min_c in feasible:

        if path == baseline:
            continue

        clearance_gain = (
            min_c - baseline_clearance
        )

        length_penalty = (
            length - baseline_len
        )

        if (
            clearance_gain >= 0.10
            and length_penalty >= 0.05
        ):
            alternatives.append(
                (
                    threshold,
                    path,
                    length,
                    min_c,
                    clearance_gain,
                    length_penalty,
                )
            )

    if not alternatives:
        continue

    best_alt = max(
        alternatives,
        key=lambda x:
            (x[4], -x[5]),
    )

    score = (
        best_alt[4] * 10.0
        - best_alt[5] * 0.1
        + direct_distance * 0.02
    )

    candidates.append(
        (
            score,
            goal,
            direct_distance,
            baseline,
            baseline_len,
            baseline_clearance,
            routes,
            best_alt,
        )
    )


if not candidates:
    print("\nNO ROUTE-SWITCH CANDIDATE FOUND.")
    raise SystemExit(1)


candidates.sort(
    key=lambda x: x[0],
    reverse=True,
)

(
    score,
    goal,
    direct_distance,
    baseline,
    baseline_len,
    baseline_clearance,
    routes,
    best_alt,
) = candidates[0]


print("\n" + "=" * 72)
print("BEST ROUTE-SWITCH PAIR")
print("=" * 72)

print("\nSTART")
print("id:", START_ID)
print("position:", positions[START_ID])

print("\nGOAL")
print("id:", goal)
print("position:", positions[goal])

print(
    "\nXY straight-line distance:",
    f"{direct_distance:.3f} m",
)

print("\nBASELINE SHORTEST PATH")
print("nodes:", len(baseline))
print("length:", f"{baseline_len:.3f} m")
print(
    "interior min clearance:",
    f"{baseline_clearance:.3f} m",
)

print("\nCLEARANCE SWEEP")

for threshold, path, length, min_c in routes:

    if path is None:
        print(
            f"{threshold:.2f} m -> NO PATH"
        )
        continue

    changed = (
        "SAME"
        if path == baseline
        else "DIFFERENT"
    )

    print(
        f"{threshold:.2f} m -> "
        f"{changed:9s} | "
        f"{len(path):3d} nodes | "
        f"{length:7.3f} m | "
        f"min clr {min_c:.3f} m"
    )


print("\nBEST ALTERNATIVE")

(
    threshold,
    alt_path,
    alt_length,
    alt_clearance,
    clearance_gain,
    length_penalty,
) = best_alt

print(
    "threshold:",
    f"{threshold:.2f} m",
)
print(
    "length:",
    f"{alt_length:.3f} m",
)
print(
    "interior min clearance:",
    f"{alt_clearance:.3f} m",
)
print(
    "clearance gain:",
    f"{clearance_gain:.3f} m",
)
print(
    "extra path length:",
    f"{length_penalty:.3f} m",
)

print("\nSTART_ID =", repr(START_ID))
print("GOAL_ID  =", repr(goal))

print("\nDONE")
