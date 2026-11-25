from collections import deque

import numpy as np

from swarmx_planning.places import PlaceNode


def build_adjacency(
    nodes: dict[str, PlaceNode],
    edges: list[tuple[str, str]],
) -> dict[str, set[str]]:
    """
    Build an unweighted undirected adjacency list.

    Used for connectivity analysis rather than path planning.
    """

    adjacency = {
        node_id: set()
        for node_id in nodes
    }

    for source, target in edges:
        adjacency[source].add(target)
        adjacency[target].add(source)

    return adjacency


def connected_components(
    adjacency: dict[str, set[str]],
) -> list[set[str]]:
    """
    Find all connected components using breadth-first search.

    Components are returned largest-first.
    """

    unvisited = set(adjacency.keys())
    components = []

    while unvisited:
        start = unvisited.pop()

        queue = deque([start])
        component = {start}

        while queue:
            current = queue.popleft()

            for neighbor in adjacency[current]:
                if neighbor in unvisited:
                    unvisited.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)

        components.append(component)

    return sorted(
        components,
        key=len,
        reverse=True,
    )


def print_graph_metrics(
    nodes: dict[str, PlaceNode],
    edges: list[tuple[str, str]],
) -> None:
    """
    Print basic planning-relevant statistics for the Hydra PLACES graph.
    """

    if not nodes:
        print("Graph contains no Place nodes.")
        return

    adjacency = build_adjacency(nodes, edges)
    components = connected_components(adjacency)

    degrees = np.array(
        [
            len(neighbors)
            for neighbors in adjacency.values()
        ],
        dtype=float,
    )

    clearances = np.array(
        [
            node.clearance
            for node in nodes.values()
        ],
        dtype=float,
    )

    largest_component_size = (
        len(components[0])
        if components
        else 0
    )

    largest_component_coverage = (
        100.0
        * largest_component_size
        / len(nodes)
    )

    print("\n=== CONNECTIVITY ===")
    print(
        "Connected components:",
        len(components),
    )
    print(
        "Largest component:",
        largest_component_size,
    )
    print(
        "Largest component coverage:",
        f"{largest_component_coverage:.2f}%",
    )

    print("\n=== DEGREE ===")
    print(
        f"Min degree:    {degrees.min():.0f}"
    )
    print(
        f"Mean degree:   {degrees.mean():.2f}"
    )
    print(
        f"Median degree: {np.median(degrees):.0f}"
    )
    print(
        f"Max degree:    {degrees.max():.0f}"
    )

    print("\n=== CLEARANCE ===")
    print(
        f"Min:    {clearances.min():.3f} m"
    )
    print(
        f"Mean:   {clearances.mean():.3f} m"
    )
    print(
        f"Median: {np.median(clearances):.3f} m"
    )
    print(
        f"Max:    {clearances.max():.3f} m"
    )


def path_metrics(
    nodes: dict[str, PlaceNode],
    path: list[str],
) -> dict[str, float | str | int]:
    """
    Compute geometry and clearance statistics for a planned path.

    Start and goal clearance are also reported, but interior clearance
    is calculated separately so endpoint geometry does not falsely
    appear to be the path bottleneck.
    """

    if len(path) < 2:
        raise ValueError(
            "Path must contain at least two nodes."
        )

    segment_lengths = []

    for source, target in zip(
        path[:-1],
        path[1:],
    ):
        p1 = nodes[source].position
        p2 = nodes[target].position

        distance = float(
            np.linalg.norm(p2 - p1)
        )

        segment_lengths.append(distance)

    path_length = float(
        sum(segment_lengths)
    )

    direct_distance = float(
        np.linalg.norm(
            nodes[path[-1]].position
            - nodes[path[0]].position
        )
    )

    if direct_distance > 0.0:
        stretch_ratio = (
            path_length / direct_distance
        )
    else:
        stretch_ratio = 1.0

    clearances = np.array(
        [
            nodes[node_id].clearance
            for node_id in path
        ],
        dtype=float,
    )

    bottleneck_index = int(
        np.argmin(clearances)
    )

    bottleneck_node = path[
        bottleneck_index
    ]

    # Exclude start and goal when measuring
    # actual route bottleneck.
    interior_path = path[1:-1]

    if interior_path:
        interior_clearances = np.array(
            [
                nodes[node_id].clearance
                for node_id in interior_path
            ],
            dtype=float,
        )

        interior_bottleneck_index = int(
            np.argmin(interior_clearances)
        )

        interior_bottleneck_node = (
            interior_path[
                interior_bottleneck_index
            ]
        )

        interior_min_clearance = float(
            interior_clearances.min()
        )

        interior_mean_clearance = float(
            interior_clearances.mean()
        )

    else:
        interior_bottleneck_node = (
            bottleneck_node
        )

        interior_min_clearance = float(
            clearances.min()
        )

        interior_mean_clearance = float(
            clearances.mean()
        )

    return {
        "path_nodes": len(path),

        "path_length": path_length,
        "direct_distance": direct_distance,
        "stretch_ratio": stretch_ratio,

        "min_clearance": float(
            clearances.min()
        ),
        "mean_clearance": float(
            clearances.mean()
        ),
        "median_clearance": float(
            np.median(clearances)
        ),
        "max_clearance": float(
            clearances.max()
        ),
        "clearance_p10": float(
            np.percentile(
                clearances,
                10,
            )
        ),

        "bottleneck_node":
            bottleneck_node,

        "interior_min_clearance":
            interior_min_clearance,

        "interior_mean_clearance":
            interior_mean_clearance,

        "interior_bottleneck_node":
            interior_bottleneck_node,
    }
