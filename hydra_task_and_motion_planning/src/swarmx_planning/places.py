from dataclasses import dataclass
import numpy as np
import spark_dsg as dsg
@dataclass
class PlaceNode:
    """Planning-relevant information from one Hydra PLACES node."""

    id: str
    position: np.ndarray
    clearance: float
    num_basis_points: int


def extract_places(
    graph: dsg.DynamicSceneGraph,
) -> tuple[dict[str, PlaceNode], list[tuple[str, str]]]:

    places_layer = graph.get_layer(dsg.DsgLayers.PLACES)
    nodes = {}
    for node in places_layer.nodes:
        node_id = node.id.str()
        attrs = node.attributes

        nodes[node_id] = PlaceNode(
            id=node_id,
            position=np.asarray(attrs.position, dtype=float),
            clearance=float(attrs.distance),
            num_basis_points=int(attrs.num_basis_points),
        )

    edges = []

    for edge in places_layer.edges:
        source = dsg.NodeSymbol(edge.source).str()
        target = dsg.NodeSymbol(edge.target).str()

        edges.append((source, target))

    return nodes, edges
