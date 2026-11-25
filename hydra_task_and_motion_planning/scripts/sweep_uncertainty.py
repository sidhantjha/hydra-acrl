from swarmx_planning.graph_io import load_dsg
from swarmx_planning.places import extract_places
from swarmx_planning.metrics import (
    build_adjacency,
    connected_components,
    path_metrics,
)
from swarmx_planning.uncertainty import (
    PlanningCertificate,
    uncertainty_aware_plan,
)


from _paths import experiment_args


def main():
    graph = load_dsg(experiment_args().dsg)
    nodes, edges = extract_places(graph)

    adjacency = build_adjacency(nodes, edges)
    largest = connected_components(adjacency)[0]

    start = min(
        largest,
        key=lambda n: (
            nodes[n].position[0],
            n,
        ),
    )

    goal = max(
        largest,
        key=lambda n: (
            nodes[n].position[0],
            n,
        ),
    )

    # Initial illustrative values.
    # We will replace these with measured robot values later.
    robot_radius = 0.15
    control_margin = 0.10

    perception_values = [
        0.15,
        0.35,
        0.55,
        0.75,
        0.95,
    ]

    print("Start:", start)
    print("Goal:", goal)

    print("\n=== UNCERTAINTY SWEEP ===")

    previous_path = None

    for perception_uncertainty in perception_values:

        certificate = PlanningCertificate(
            robot_radius=robot_radius,
            control_margin=control_margin,
            perception_uncertainty=perception_uncertainty,
        )

        required = certificate.required_clearance

        try:
            path, distance = uncertainty_aware_plan(
                nodes,
                edges,
                start,
                goal,
                certificate,
            )

            metrics = path_metrics(
                nodes,
                path,
            )

            route_changed = (
                previous_path is not None
                and path != previous_path
            )

            print(
                f"perception={perception_uncertainty:.2f} m | "
                f"required={required:.2f} m | "
                f"length={distance:.2f} m | "
                f"min={metrics['interior_min_clearance']:.3f} m | "
                f"changed={route_changed}"
            )

            previous_path = path

        except ValueError:
            print(
                f"perception={perception_uncertainty:.2f} m | "
                f"required={required:.2f} m | "
                f"NO CERTIFIED PATH"
            )


if __name__ == "__main__":
    main()
