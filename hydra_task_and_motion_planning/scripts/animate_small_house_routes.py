import math

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import networkx as nx
import numpy as np
import spark_dsg as dsg


from _paths import MODULE, experiment_args, output_path

args = experiment_args(outputs=True, start="p13061", goal="p2473")
GRAPH_PATH = args.dsg

OUT_DIR = args.output_dir or MODULE / "results"

OUT_GIF = output_path(OUT_DIR, "small_house_uncertainty_routes.gif")
OUT_MP4 = output_path(OUT_DIR, "small_house_uncertainty_routes.mp4")

PLACE_LAYER_ID = 3

START_ID = args.start
GOAL_ID = args.goal

MAX_EDGE_DZ = 0.8
REQUIRED_CLEARANCES = [0.40, 0.50, 0.70, 1.00]

ROBOT_RADIUS = 0.15
CONTROL_MARGIN = 0.10


def id_str(value):
    if hasattr(value, "id"):
        value = value.id

    if hasattr(value, "str"):
        return value.str()

    try:
        return dsg.NodeSymbol(value).str()
    except Exception:
        return str(value)


def node_id_str(node):
    return id_str(node)


def node_pos(node):
    p = np.array(node.attributes.position, dtype=float).reshape(-1)
    return p[:3]


def node_clearance(node):
    # For Hydra places this is the GVD distance / local clearance.
    if hasattr(node.attributes, "distance"):
        return float(node.attributes.distance)
    if hasattr(node.attributes, "clearance"):
        return float(node.attributes.clearance)
    raise AttributeError(f"No clearance field found for node {node_id_str(node)}")


def edge_uv(edge):
    return id_str(edge.source), id_str(edge.target)


def path_length(path_ids, positions):
    total = 0.0
    for a, b in zip(path_ids[:-1], path_ids[1:]):
        total += float(
            np.linalg.norm(
                positions[b][:2] - positions[a][:2]
            )
        )
    return total


def interior_min_clearance(path_ids, clearances):
    if len(path_ids) <= 2:
        return min(clearances[path_ids[0]], clearances[path_ids[-1]])
    vals = [clearances[nid] for nid in path_ids[1:-1]]
    return min(vals) if vals else min(clearances[path_ids[0]], clearances[path_ids[-1]])


print("=" * 72)
print("LOADING DSG")
print("=" * 72)
print("Graph:", GRAPH_PATH)

graph = dsg.DynamicSceneGraph.load(str(GRAPH_PATH))
places = graph.get_layer(PLACE_LAYER_ID)

nodes = list(places.nodes)
edges = list(places.edges)

print(f"places: {len(nodes)} nodes, {len(edges)} edges")

positions = {}
clearances = {}

for node in nodes:
    nid = node_id_str(node)
    positions[nid] = node_pos(node)
    clearances[nid] = node_clearance(node)

G = nx.Graph()

for nid in positions:
    G.add_node(
        nid,
        pos=positions[nid],
        clearance=clearances[nid],
    )

for edge in edges:
    u, v = edge_uv(edge)
    pu = positions[u]
    pv = positions[v]

    dz = abs(float(pu[2] - pv[2]))
    if dz > MAX_EDGE_DZ:
        continue

    w = float(np.linalg.norm(pu[:2] - pv[:2]))
    G.add_edge(u, v, weight=w, dz=dz)

print(f"filtered graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
print(f"start: {START_ID} @ {positions[START_ID]}")
print(f"goal:  {GOAL_ID} @ {positions[GOAL_ID]}")

if START_ID not in G.nodes:
    raise RuntimeError(f"Start node {START_ID} not found in filtered graph.")
if GOAL_ID not in G.nodes:
    raise RuntimeError(f"Goal node {GOAL_ID} not found in filtered graph.")

route_records = []

for req in REQUIRED_CLEARANCES:
    G_req = nx.Graph()

    for nid in G.nodes:
        keep = (nid == START_ID) or (nid == GOAL_ID) or (clearances[nid] >= req)
        if keep:
            G_req.add_node(nid, **G.nodes[nid])

    for u, v, data in G.edges(data=True):
        if u in G_req.nodes and v in G_req.nodes:
            G_req.add_edge(u, v, **data)

    if not nx.has_path(G_req, START_ID, GOAL_ID):
        print(f"[WARN] No path for required clearance {req:.2f} m")
        continue

    path_ids = nx.shortest_path(G_req, START_ID, GOAL_ID, weight="weight")
    L = path_length(path_ids, positions)
    min_clr = interior_min_clearance(path_ids, clearances)

    route_records.append(
        {
            "required": req,
            "uncertainty": req - (ROBOT_RADIUS + CONTROL_MARGIN),
            "path_ids": path_ids,
            "xy": np.array([[positions[n][0], positions[n][1]] for n in path_ids], dtype=float),
            "length": L,
            "min_clearance": min_clr,
        }
    )

    print(
        f"req={req:.2f} m  "
        f"nodes={len(path_ids):2d}  "
        f"L={L:.3f} m  "
        f"min_clr={min_clr:.3f} m"
    )

if not route_records:
    raise RuntimeError("No valid routes found. Nothing to animate.")

# Plot bounds
all_xy = np.array([[p[0], p[1]] for p in positions.values()], dtype=float)
xmin, ymin = all_xy.min(axis=0)
xmax, ymax = all_xy.max(axis=0)

pad_x = 0.08 * (xmax - xmin)
pad_y = 0.08 * (ymax - ymin)

fig, ax = plt.subplots(figsize=(11, 8))

# background graph
for u, v in G.edges():
    pu = positions[u]
    pv = positions[v]
    ax.plot(
        [pu[0], pv[0]],
        [pu[1], pv[1]],
        linewidth=0.8,
        alpha=0.18,
        zorder=1,
    )

# faint nodes
bg_xy = np.array([[positions[n][0], positions[n][1]] for n in G.nodes], dtype=float)
ax.scatter(bg_xy[:, 0], bg_xy[:, 1], s=8, alpha=0.18, zorder=2)

# start / goal
start_xy = positions[START_ID][:2]
goal_xy = positions[GOAL_ID][:2]

ax.scatter([start_xy[0]], [start_xy[1]], marker="*", s=180, zorder=10, label="Start")
ax.scatter([goal_xy[0]], [goal_xy[1]], marker="X", s=160, zorder=10, label="Goal")

colors = ["tab:brown", "tab:pink", "tab:gray", "tab:olive"]

route_lines = []
route_dots = []

for i, rec in enumerate(route_records):
    line, = ax.plot([], [], linewidth=3, alpha=0.95, zorder=6)
    line.set_color(colors[i % len(colors)])
    dot, = ax.plot([], [], "o", markersize=8, zorder=7)
    dot.set_color(colors[i % len(colors)])
    route_lines.append(line)
    route_dots.append(dot)

title = ax.set_title("Hydra Small House: Uncertainty-Aware Route Switching", fontsize=16)
info_text = ax.text(
    0.02, 0.98, "", transform=ax.transAxes,
    va="top", ha="left", fontsize=11,
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.85)
)

ax.set_xlabel("X [m]")
ax.set_ylabel("Y [m]")
ax.set_xlim(xmin - pad_x, xmax + pad_x)
ax.set_ylim(ymin - pad_y, ymax + pad_y)
ax.set_aspect("equal")
ax.grid(True, alpha=0.25)
ax.legend(loc="lower left")

# Build animation frame plan
FRAMES_PER_SEGMENT = 10
PAUSE_FRAMES = 12

frame_plan = []
for ridx, rec in enumerate(route_records):
    nseg = len(rec["xy"]) - 1
    frame_plan += [(ridx, "pause_start", 0.0)] * PAUSE_FRAMES
    for seg in range(nseg):
        for k in range(FRAMES_PER_SEGMENT):
            alpha = k / FRAMES_PER_SEGMENT
            frame_plan.append((ridx, seg, alpha))
    frame_plan += [(ridx, "pause_end", 1.0)] * PAUSE_FRAMES


def interpolate_point(a, b, t):
    return (1.0 - t) * a + t * b


def update(frame_idx):
    ridx, seg_info, alpha = frame_plan[frame_idx]

    # Clear future routes, fade previous routes
    for j, rec in enumerate(route_records):
        xy = rec["xy"]
        color = colors[j % len(colors)]

        if j < ridx:
            route_lines[j].set_data(xy[:, 0], xy[:, 1])
            route_lines[j].set_alpha(0.25)
            route_lines[j].set_color(color)
            route_dots[j].set_data([xy[-1, 0]], [xy[-1, 1]])
            route_dots[j].set_alpha(0.0)
        elif j > ridx:
            route_lines[j].set_data([], [])
            route_dots[j].set_data([], [])
        else:
            route_lines[j].set_alpha(0.95)
            route_lines[j].set_color(color)

            if seg_info == "pause_start":
                route_lines[j].set_data([xy[0, 0]], [xy[0, 1]])
                route_dots[j].set_data([xy[0, 0]], [xy[0, 1]])
            elif seg_info == "pause_end":
                route_lines[j].set_data(xy[:, 0], xy[:, 1])
                route_dots[j].set_data([xy[-1, 0]], [xy[-1, 1]])
            else:
                seg = int(seg_info)
                pts = xy[: seg + 1].copy()
                p = interpolate_point(xy[seg], xy[seg + 1], alpha)

                if len(pts) == 0:
                    xs = [p[0]]
                    ys = [p[1]]
                else:
                    xs = list(pts[:, 0]) + [p[0]]
                    ys = list(pts[:, 1]) + [p[1]]

                route_lines[j].set_data(xs, ys)
                route_dots[j].set_data([p[0]], [p[1]])

    rec = route_records[ridx]
    req = rec["required"]
    U = rec["uncertainty"]
    L = rec["length"]
    mc = rec["min_clearance"]

    info_text.set_text(
        f"Required clearance = {req:.2f} m\n"
        f"Illustrative uncertainty U = {U:.2f} m\n"
        f"Route length = {L:.2f} m\n"
        f"Interior bottleneck clearance = {mc:.2f} m"
    )

    return route_lines + route_dots + [info_text]


anim = FuncAnimation(
    fig,
    update,
    frames=len(frame_plan),
    interval=120,
    blit=False,
    repeat=True,
)

print("\nSaving GIF to:", OUT_GIF)
anim.save(OUT_GIF, writer=PillowWriter(fps=8))

try:
    print("Saving MP4 to:", OUT_MP4)
    anim.save(OUT_MP4, fps=8)
except Exception as e:
    print(f"[WARN] MP4 export failed ({e}). GIF was still saved successfully.")

plt.close(fig)

print("\nDONE")
print("GIF:", OUT_GIF)
print("MP4:", OUT_MP4)
