import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

from swarmx_planning.graph_io import load_dsg
from swarmx_planning.places import extract_places
from swarmx_planning.metrics import build_adjacency, connected_components
from swarmx_planning.planner import astar


from _paths import experiment_args, output_path


def main():
    args = experiment_args(outputs=True)
    graph = load_dsg(args.dsg)
    nodes, edges = extract_places(graph)

    adjacency = build_adjacency(nodes, edges)
    components = connected_components(adjacency)

    largest = components[0]

    # Same start/goal selection as our first A* test
    start = min(
        largest,
        key=lambda node_id: nodes[node_id].position[0],
    )

    goal = max(
        largest,
        key=lambda node_id: nodes[node_id].position[0],
    )

    path, distance = astar(
        nodes,
        edges,
        start,
        goal,
    )

    print(f"Start: {start}")
    print(f"Goal: {goal}")
    print(f"Path nodes: {len(path)}")
    print(f"Path distance: {distance:.2f} m")

    # -------------------------
    # Draw complete Places graph
    # -------------------------

    graph_segments = []

    for source, target in edges:
        p1 = nodes[source].position
        p2 = nodes[target].position

        graph_segments.append(
            [
                (p1[0], p1[1]),
                (p2[0], p2[1]),
            ]
        )

    fig, ax = plt.subplots(figsize=(12, 9))

    graph_lines = LineCollection(
        graph_segments,
        linewidths=0.3,
        alpha=0.25,
    )

    ax.add_collection(graph_lines)

    # -------------------------
    # Draw all place nodes
    # -------------------------

    xs = [node.position[0] for node in nodes.values()]
    ys = [node.position[1] for node in nodes.values()]

    ax.scatter(
        xs,
        ys,
        s=4,
        alpha=0.4,
    )

    # -------------------------
    # Draw A* path
    # -------------------------

    path_x = [
        nodes[node_id].position[0]
        for node_id in path
    ]

    path_y = [
        nodes[node_id].position[1]
        for node_id in path
    ]

    ax.plot(
        path_x,
        path_y,
        linewidth=3,
        label=f"A* path ({distance:.2f} m)",
    )

    # Start + goal
    ax.scatter(
        nodes[start].position[0],
        nodes[start].position[1],
        s=100,
        marker="o",
        label=f"Start {start}",
    )

    ax.scatter(
        nodes[goal].position[0],
        nodes[goal].position[1],
        s=100,
        marker="X",
        label=f"Goal {goal}",
    )

    ax.set_title("Hydra PLACES Graph + A* Route")
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")

    ax.axis("equal")
    ax.grid(True, alpha=0.2)
    ax.legend()

    plt.tight_layout()
    if args.output_dir is None:
        plt.show()
    else:
        plt.savefig(output_path(args.output_dir, "visualize_astar.png"))


if __name__ == "__main__":
    main()
