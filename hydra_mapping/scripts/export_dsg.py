"""Validate a saved Spark-DSG graph and export it from a completed managed run."""

import hashlib
import json
from pathlib import Path
import sys


def reject_nonfinite(token):
    raise ValueError(f"Non-JSON numeric constant: {token}")


def validate_graph(data):
    graph = json.loads(data, parse_constant=reject_nonfinite)
    if not isinstance(graph, dict) or not isinstance(graph.get("SPARK_DSG_header"), dict):
        raise ValueError("Missing Spark-DSG header")
    nodes, edges = graph.get("nodes"), graph.get("edges")
    layers = graph.get("layer_names")
    if not isinstance(nodes, list) or not nodes or not isinstance(edges, list):
        raise ValueError("Expected a nonempty node list and an edge list")
    if not isinstance(layers, dict) or "PLACES" not in layers:
        raise ValueError("Missing the PLACES layer")
    places = layers["PLACES"]
    if not isinstance(places, dict) or any(type(places.get(key)) is not int for key in ("layer", "partition")):
        raise ValueError("Invalid PLACES layer key")
    node_ids = set()
    place_count = 0
    for node in nodes:
        if not isinstance(node, dict) or type(node.get("id")) is not int \
                or not isinstance(node.get("attributes"), dict):
            raise ValueError("Invalid graph node")
        if node["id"] in node_ids:
            raise ValueError("Duplicate graph node ID")
        node_ids.add(node["id"])
        if (node.get("layer"), node.get("partition")) == (places["layer"], places["partition"]):
            place_count += 1
    if not place_count:
        raise ValueError("No PLACES nodes in the graph")
    for edge in edges:
        if not isinstance(edge, dict) or any(
            type(edge.get(key)) is not int or edge[key] not in node_ids
            for key in ("source", "target")
        ):
            raise ValueError("Invalid graph edge or missing endpoint")
    return {"nodes": len(nodes), "edges": len(edges), "places_nodes": place_count}


def export(run, output):
    status = json.loads((run / "hydra_exit.json").read_text())
    if status.get("returncode") != 0:
        raise ValueError(f"Hydra terminated before a clean save ({status})")
    source = run / "hydra" / "backend" / "dsg.json"
    data = source.read_bytes()
    if not data:
        raise ValueError(f"Empty graph: {source}")
    counts = validate_graph(data)

    def artifact_state(relative_path):
        artifact = source.parent / relative_path
        size = artifact.stat().st_size if artifact.is_file() else None
        return {"bytes": size, "state": "missing" if size is None else "empty" if size == 0 else "present"}

    metadata_path = run / "run_metadata.txt"
    record = {
        "run": str(run.resolve()),
        "output": str(output.resolve()),
        "hydra_exit": status,
        "graph": {**counts, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()},
        "dsg_with_mesh": artifact_state("dsg_with_mesh.json"),
        "mesh_ply": artifact_state("mesh.ply"),
        "hydra_config": artifact_state("../hydra_config.yaml"),
        "run_metadata": metadata_path.read_text().splitlines() if metadata_path.is_file() else [],
    }
    sidecar = output.with_name(output.name + ".export.json")
    # Exclusive creation prevents concurrent exports from clobbering either file.
    with output.open("xb") as stream:
        try:
            stream.write(data)
            stream.flush()
            with sidecar.open("x") as metadata:
                try:
                    json.dump(record, metadata, indent=2)
                    metadata.write("\n")
                    metadata.flush()
                except BaseException:
                    sidecar.unlink()
                    raise
        except BaseException:
            output.unlink()
            raise
    return record


if __name__ == "__main__":
    try:
        print(json.dumps(export(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
    except (OSError, ValueError) as error:
        sys.exit(f"Export failed: {error}")
