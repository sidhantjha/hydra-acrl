from collections import defaultdict, deque

import numpy as np
import spark_dsg as dsg


from _paths import experiment_args

args = experiment_args()
GRAPH_PATH = args.dsg


def normalize_id(value):
    if hasattr(value, "id"):
        value = value.id

    if hasattr(value, "str"):
        return value.str()

    try:
        return dsg.NodeSymbol(value).str()
    except Exception:
        return str(value)


graph = dsg.DynamicSceneGraph.load(str(GRAPH_PATH))
places = graph.get_layer(3)

nodes = list(places.nodes)
edges = list(places.edges)

print("=" * 70)
print("SMALL HOUSE DSG INSPECTION")
print("=" * 70)

print("\nTotal graph nodes:", graph.num_nodes())
print("Total graph edges:", graph.num_edges())

print("\nPLACES")
print("nodes:", len(nodes))
print("edges:", len(edges))


positions = {}
clearances = {}

for node in nodes:
    nid = normalize_id(node)
    positions[nid] = np.asarray(
        node.attributes.position,
        dtype=float,
    )
    clearances[nid] = float(
        getattr(node.attributes, "distance", np.nan)
    )


print("\nSAMPLE NODE IDS")
for node in nodes[:5]:
    print(normalize_id(node))


print("\nSAMPLE EDGE IDS")
for edge in edges[:5]:
    print(
        normalize_id(edge.source),
        "<->",
        normalize_id(edge.target),
    )


adj = defaultdict(set)
matched = 0

for edge in edges:
    a = normalize_id(edge.source)
    b = normalize_id(edge.target)

    if a in positions and b in positions:
        adj[a].add(b)
        adj[b].add(a)
        matched += 1


print("\nEDGE MATCHING")
print("layer edges:", len(edges))
print("matched edges:", matched)


unvisited = set(positions.keys())
components = []

while unvisited:
    start = next(iter(unvisited))
    q = deque([start])
    component = {start}
    unvisited.remove(start)

    while q:
        current = q.popleft()

        for neighbor in adj[current]:
            if neighbor in unvisited:
                unvisited.remove(neighbor)
                component.add(neighbor)
                q.append(neighbor)

    components.append(component)


components.sort(key=len, reverse=True)

print("\nCONNECTED COMPONENTS")
print("count:", len(components))
print(
    "sizes:",
    [len(c) for c in components[:10]],
)

largest = components[0]

print(
    f"largest: {len(largest)} / {len(nodes)} "
    f"({100 * len(largest) / len(nodes):.2f}%)"
)


xyz = np.stack(
    [positions[n] for n in largest]
)

print("\nLARGEST COMPONENT BOUNDS")

for i, axis in enumerate(["x", "y", "z"]):
    print(
        f"{axis}: "
        f"{xyz[:, i].min():.3f} -> "
        f"{xyz[:, i].max():.3f} m"
    )


valid_clearance = np.array(
    [
        clearances[n]
        for n in largest
        if np.isfinite(clearances[n])
    ]
)

print("\nCLEARANCE")
print(f"min:    {valid_clearance.min():.3f} m")
print(f"mean:   {valid_clearance.mean():.3f} m")
print(f"median: {np.median(valid_clearance):.3f} m")
print(f"max:    {valid_clearance.max():.3f} m")


degrees = np.array(
    [len(adj[n]) for n in largest]
)

print("\nDEGREE")
print("min:", degrees.min())
print("mean:", round(float(degrees.mean()), 2))
print("median:", float(np.median(degrees)))
print("max:", degrees.max())


origin = np.zeros(3)

start = min(
    largest,
    key=lambda n:
        np.linalg.norm(positions[n] - origin),
)

print("\nSTART NODE")
print("id:", start)
print("position:", positions[start])
print(
    "distance from origin:",
    f"{np.linalg.norm(positions[start]):.3f} m",
)
print(
    "clearance:",
    f"{clearances[start]:.3f} m",
)


goal = max(
    largest,
    key=lambda n:
        np.linalg.norm(
            positions[n] - positions[start]
        ),
)

print("\nFAR-SIDE GOAL CANDIDATE")
print("id:", goal)
print("position:", positions[goal])
print(
    "straight-line distance:",
    f"{np.linalg.norm(
        positions[goal] - positions[start]
    ):.3f} m",
)
print(
    "clearance:",
    f"{clearances[goal]:.3f} m",
)

print("\nDONE")
