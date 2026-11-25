from heapq import heappop, heappush

import numpy as np

from swarmx_planning.places import PlaceNode


def euclidean_distance(a: PlaceNode, b: PlaceNode) -> float:
    """Straight-line distance between two Hydra places."""
    return float(np.linalg.norm(a.position - b.position))


def build_adjacency(
    nodes: dict[str, PlaceNode],
    edges: list[tuple[str, str]],
) -> dict[str, list[tuple[str, float]]]:
    """
    Build weighted adjacency list.

    Each edge weight is Euclidean distance between connected places.
    """

    adjacency = {node_id: [] for node_id in nodes}

    for source, target in edges:
        cost = euclidean_distance(nodes[source], nodes[target])

        adjacency[source].append((target, cost))
        adjacency[target].append((source, cost))

    return adjacency


def astar(
    nodes: dict[str, PlaceNode],
    edges: list[tuple[str, str]],
    start: str,
    goal: str,
) -> tuple[list[str], float]:
    """
    Find shortest path between two Hydra places using A*.

    Returns:
        path:
            Ordered list of place IDs.

        total_cost:
            Total path length in meters.
    """

    if start not in nodes:
        raise ValueError(f"Unknown start node: {start}")

    if goal not in nodes:
        raise ValueError(f"Unknown goal node: {goal}")

    adjacency = build_adjacency(nodes, edges)

    open_set = []

    heappush(open_set, (0.0, start))

    came_from = {}

    g_score = {node_id: float("inf") for node_id in nodes}
    g_score[start] = 0.0

    while open_set:
        _, current = heappop(open_set)

        if current == goal:
            path = [current]

            while current in came_from:
                current = came_from[current]
                path.append(current)

            path.reverse()

            return path, g_score[goal]

        for neighbor, edge_cost in adjacency[current]:
            tentative_g = g_score[current] + edge_cost

            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g

                heuristic = euclidean_distance(
                    nodes[neighbor],
                    nodes[goal],
                )

                f_score = tentative_g + heuristic

                heappush(
                    open_set,
                    (f_score, neighbor),
                )

    raise ValueError(f"No path exists between {start} and {goal}")

def astar_with_min_clearance(
    nodes: dict[str, PlaceNode],
    edges: list[tuple[str, str]],
    start: str,
    goal: str,
    min_clearance: float,
) -> tuple[list[str], float]:
    """
    A* that rejects intermediate places below a clearance threshold.

    Start and goal are always allowed so endpoint geometry does not
    artificially make the planning problem infeasible.
    """

    adjacency = build_adjacency(nodes, edges)

    open_set = []
    heappush(open_set, (0.0, start))

    came_from = {}

    g_score = {node_id: float("inf") for node_id in nodes}
    g_score[start] = 0.0

    while open_set:
        _, current = heappop(open_set)

        if current == goal:
            path = [current]

            while current in came_from:
                current = came_from[current]
                path.append(current)

            path.reverse()

            return path, g_score[goal]

        for neighbor, edge_cost in adjacency[current]:

            if (
                neighbor not in (start, goal)
                and nodes[neighbor].clearance < min_clearance
            ):
                continue

            tentative_g = g_score[current] + edge_cost

            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g

                heuristic = euclidean_distance(
                    nodes[neighbor],
                    nodes[goal],
                )

                heappush(
                    open_set,
                    (tentative_g + heuristic, neighbor),
                )

    raise ValueError(
        f"No path with minimum clearance {min_clearance:.2f} m"
    )
