from pathlib import Path
import spark_dsg as dsg

#Load a Hydra Dynamic Scene Graph from a JSON file.
def load_dsg(path: str | Path) -> dsg.DynamicSceneGraph:
    graph_path = Path(path).expanduser().resolve()
    if not graph_path.is_file():
        raise FileNotFoundError(f"DSG file not found: {graph_path}")

    if graph_path.suffix.lower() != ".json":
        raise ValueError(f"Expected a JSON DSG file, got: {graph_path}")

    print(f"Loading DSG: {graph_path}")
    graph = dsg.DynamicSceneGraph.load(str(graph_path))
    print("DSG loaded successfully.")

    return graph
