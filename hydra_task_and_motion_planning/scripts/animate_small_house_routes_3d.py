
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import networkx as nx
import numpy as np
import spark_dsg as dsg

from _paths import MODULE, experiment_args, output_path

args = experiment_args(outputs=True, start="p13061", goal="p2473")
GRAPH_PATH = args.dsg

OUT_DIR = args.output_dir or MODULE / "results"

OUT_GIF = output_path(OUT_DIR, "small_house_uncertainty_routes_3d.gif")

START = args.start
GOAL = args.goal
MAX_DZ = 0.8

ROBOT_RADIUS = 0.15
CONTROL_MARGIN = 0.10

REQUIRED = [0.40, 0.50, 0.70, 1.00]
ROUTE_COLORS = ["tab:brown", "tab:pink", "tab:gray", "tab:olive"]


def id_str(value):
    if hasattr(value, "id"):
        value = value.id
    if hasattr(value, "str"):
        return value.str()
    return dsg.NodeSymbol(value).str()


def xy_distance(a, b, positions):
    return float(np.linalg.norm(positions[a][:2] - positions[b][:2]))


def route_length(path, positions):
    total = 0.0
    for a, b in zip(path[:-1], path[1:]):
        total += xy_distance(a, b, positions)
    return total


def bottleneck(path, clearance):
    interior = path[1:-1] if len(path) > 2 else path
    return min(clearance[n] for n in interior)


print("=" * 72)
print("HYDRA SMALL HOUSE 3D ANIMATION")
print("=" * 72)

graph = dsg.DynamicSceneGraph.load(str(GRAPH_PATH))
layer = graph.get_layer(3)

positions = {}
clearance = {}

for node in layer.nodes:
    nid = node.id.str()
    positions[nid] = np.asarray(node.attributes.position, dtype=float)
    clearance[nid] = float(node.attributes.distance)

G = nx.Graph()
for nid in positions:
    G.add_node(nid)

segments = []
for edge in layer.edges:
    a = id_str(edge.source)
    b = id_str(edge.target)

    pa = positions[a]
    pb = positions[b]

    if abs(pa[2] - pb[2]) > MAX_DZ:
        continue

    w = float(np.linalg.norm(pa[:2] - pb[:2]))
    G.add_edge(a, b, weight=w)
    segments.append([pa, pb])

print("Filtered topology:", G.number_of_nodes(), "nodes,", G.number_of_edges(), "edges")

routes = []
for req in REQUIRED:
    valid_nodes = {
        nid for nid in G.nodes
        if (nid in (START, GOAL) or clearance[nid] >= req)
    }

    H = G.subgraph(valid_nodes).copy()

    if START not in H or GOAL not in H or not nx.has_path(H, START, GOAL):
        print(f"required={req:.2f}: NO CERTIFIED PATH")
        continue

    path = nx.shortest_path(H, START, GOAL, weight="weight")
    length = route_length(path, positions)
    min_clearance = bottleneck(path, clearance)
    uncertainty = req - ROBOT_RADIUS - CONTROL_MARGIN

    xyz = np.asarray([positions[n] for n in path])

    routes.append({
        "required": req,
        "uncertainty": uncertainty,
        "path": path,
        "xyz": xyz,
        "length": length,
        "bottleneck": min_clearance,
    })

    print(
        f"required={req:.2f} m | "
        f"U={uncertainty:.2f} m | "
        f"{len(path)} nodes | "
        f"L={length:.3f} m | "
        f"min={min_clearance:.3f} m"
    )

fig = plt.figure(figsize=(14, 9))
ax = fig.add_subplot(111, projection="3d")
plt.subplots_adjust(left=0.22, right=0.86, top=0.90, bottom=0.06)

edge_collection = Line3DCollection(segments, linewidths=0.6, alpha=0.10)
ax.add_collection3d(edge_collection)

node_ids = list(positions)
node_xyz = np.asarray([positions[n] for n in node_ids])
node_clearance = np.asarray([clearance[n] for n in node_ids])

sc = ax.scatter(
    node_xyz[:, 0], node_xyz[:, 1], node_xyz[:, 2],
    c=node_clearance, s=14, alpha=0.55
)

cbar = fig.colorbar(sc, ax=ax, shrink=0.62, pad=0.02)
cbar.set_label("Hydra local clearance [m]")

start_p = positions[START]
goal_p = positions[GOAL]

ax.scatter([start_p[0]], [start_p[1]], [start_p[2]], marker="*", s=220, label="Start")
ax.scatter([goal_p[0]], [goal_p[1]], [goal_p[2]], marker="X", s=180, label="Goal")

route_line, = ax.plot([], [], [], linewidth=4, zorder=20)
route_nodes = ax.scatter([], [], [], s=55, zorder=21)
robot = ax.scatter([], [], [], s=180, marker="o", zorder=30)

info = fig.text(
    0.02, 0.82, "",
    va="top", ha="left", fontsize=11,
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.90)
)

formula = fig.text(
    0.02, 0.68,
    "Certificate\n"
    "required clearance = robot radius + control margin + uncertainty\n"
    "r_req = 0.15 + 0.10 + U",
    va="top", ha="left", fontsize=9,
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.85)
)

summary = fig.text(
    0.02, 0.52,
    "Interpretation\n"
    "As uncertainty increases, the planner requires larger clearance\n"
    "and switches to safer but slightly longer routes.",
    va="top", ha="left", fontsize=9,
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.85)
)

ax.set_xlabel("X [m]")
ax.set_ylabel("Y [m]")
ax.set_zlabel("Z [m]")
ax.set_title("Hydra Small House 3D DSG: Uncertainty-Aware Route Switching", pad=16)
ax.legend(loc="lower left")

mins = node_xyz.min(axis=0) - np.array([1.0, 1.0, 0.5])
maxs = node_xyz.max(axis=0) + np.array([1.0, 1.0, 0.5])

ax.set_xlim(mins[0], maxs[0])
ax.set_ylim(mins[1], maxs[1])
ax.set_zlim(mins[2], maxs[2])

FRAMES_PER_EDGE = 12
START_PAUSE = 12
END_PAUSE = 16

frame_plan = []
for route_idx, rec in enumerate(routes):
    for _ in range(START_PAUSE):
        frame_plan.append((route_idx, "start", 0, 0.0))

    xyz = rec["xyz"]
    for seg_idx in range(len(xyz) - 1):
        for k in range(FRAMES_PER_EDGE):
            alpha = k / FRAMES_PER_EDGE
            frame_plan.append((route_idx, "move", seg_idx, alpha))

    for _ in range(END_PAUSE):
        frame_plan.append((route_idx, "end", len(xyz) - 2, 1.0))


def interpolate(a, b, alpha):
    return (1.0 - alpha) * a + alpha * b


def update(frame_idx):
    route_idx, state, seg_idx, alpha = frame_plan[frame_idx]
    rec = routes[route_idx]
    xyz = rec["xyz"]

    color = ROUTE_COLORS[route_idx % len(ROUTE_COLORS)]
    route_line.set_color(color)
    robot.set_color(color)
    route_nodes.set_color(color)

    route_nodes._offsets3d = (xyz[:, 0], xyz[:, 1], xyz[:, 2])

    if state == "start":
        current = xyz[0]
        route_line.set_data([xyz[0, 0]], [xyz[0, 1]])
        route_line.set_3d_properties([xyz[0, 2]])

    elif state == "end":
        current = xyz[-1]
        route_line.set_data(xyz[:, 0], xyz[:, 1])
        route_line.set_3d_properties(xyz[:, 2])

    else:
        current = interpolate(xyz[seg_idx], xyz[seg_idx + 1], alpha)

        completed = xyz[:seg_idx + 1]
        xs = list(completed[:, 0]) + [current[0]]
        ys = list(completed[:, 1]) + [current[1]]
        zs = list(completed[:, 2]) + [current[2]]

        route_line.set_data(xs, ys)
        route_line.set_3d_properties(zs)

    robot._offsets3d = ([current[0]], [current[1]], [current[2]])

    info.set_text(
        f"Illustrative uncertainty U = {rec['uncertainty']:.2f} m\n"
        f"Required clearance = {rec['required']:.2f} m\n"
        f"Route length = {rec['length']:.2f} m\n"
        f"Bottleneck clearance = {rec['bottleneck']:.2f} m\n"
        f"Route {route_idx + 1}/{len(routes)}"
    )

    total_frames = len(frame_plan)
    orbit = 40.0 * frame_idx / total_frames
    ax.view_init(elev=24, azim=-62 + orbit)

    return route_line, route_nodes, robot


animation = FuncAnimation(
    fig, update, frames=len(frame_plan), interval=100, blit=False, repeat=True
)

print("\nSaving:", OUT_GIF)
animation.save(OUT_GIF, writer=PillowWriter(fps=10))
plt.close(fig)

print("\nDONE")
print("3D GIF:", OUT_GIF)
