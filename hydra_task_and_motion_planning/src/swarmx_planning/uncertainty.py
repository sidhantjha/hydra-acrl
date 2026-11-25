from dataclasses import dataclass

from swarmx_planning.places import PlaceNode
from swarmx_planning.planner import astar_with_min_clearance


@dataclass
class PlanningCertificate:
    robot_radius: float
    control_margin: float
    perception_uncertainty: float

    @property
    def required_clearance(self) -> float:
        return (
            self.robot_radius
            + self.control_margin
            + self.perception_uncertainty
        )


def uncertainty_aware_plan(
    nodes: dict[str, PlaceNode],
    edges: list[tuple[str, str]],
    start: str,
    goal: str,
    certificate: PlanningCertificate,
) -> tuple[list[str], float]:
    """
    Plan using a hard clearance requirement derived from
    robot size, control capability, and perception uncertainty.
    """

    return astar_with_min_clearance(
        nodes=nodes,
        edges=edges,
        start=start,
        goal=goal,
        min_clearance=certificate.required_clearance,
    )
