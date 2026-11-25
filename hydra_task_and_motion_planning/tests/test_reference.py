import hashlib
import io
import os
from pathlib import Path
import runpy
import sys
import sysconfig
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from swarmx_planning import graph_io
from swarmx_planning.metrics import build_adjacency, connected_components
from swarmx_planning.places import extract_places


MODULE = Path(__file__).resolve().parents[1]
REFERENCE = MODULE / "experiments/small_house/run_01/dsg.json"
SHA256 = "fd98e8f2281006792a7f9ae60f42cdfac2b99c1ec47d4055d45db2ae4ecea392"


class ReferenceGraphTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not REFERENCE.is_file():
            raise unittest.SkipTest("The local-only Small House fixture is required")
        script = MODULE / "scripts/find_small_house_route_switch.py"
        with patch.object(sys, "argv", [str(script), "--dsg", str(REFERENCE)]), patch.object(
            sys, "path", [str(script.parent), *sys.path]
        ), redirect_stdout(io.StringIO()):
            cls.experiment = runpy.run_path(str(script))

    def test_reference_identity_and_unfiltered_topology(self):
        self.assertEqual(REFERENCE.stat().st_size, 556994)
        self.assertEqual(hashlib.sha256(REFERENCE.read_bytes()).hexdigest(), SHA256)
        source = MODULE / "src/swarmx_planning/graph_io.py"
        origin = Path(graph_io.__file__).resolve()
        if origin != source:
            release_venv = MODULE / ".venv"
            site_packages = Path(sysconfig.get_path("purelib")).resolve()
            self.assertEqual(
                Path(sys.prefix).resolve(), release_venv, f"Unexpected import: {origin}"
            )
            self.assertTrue(
                site_packages.is_relative_to(release_venv),
                f"Unexpected site-packages: {site_packages}",
            )
            self.assertEqual(origin, site_packages / "swarmx_planning/graph_io.py")
            self.assertEqual(
                hashlib.sha256(origin.read_bytes()).digest(),
                hashlib.sha256(source.read_bytes()).digest(),
                f"Installed graph_io.py differs from the release source: {origin}",
            )
        graph = graph_io.load_dsg(REFERENCE)
        nodes, edges = extract_places(graph)
        self.assertEqual((len(nodes), len(edges)), (246, 971))
        self.assertEqual(
            [len(group) for group in connected_components(build_adjacency(nodes, edges))],
            [242, 4],
        )

    def test_filtered_topology_and_endpoint_selection(self):
        e = self.experiment
        self.assertEqual(e["GRAPH_PATH"], REFERENCE)
        self.assertEqual(e["MAX_DZ"], 0.8)
        self.assertEqual(e["kept_edges"], 555)
        self.assertEqual(len(e["start_component"]), 213)
        self.assertEqual((e["START_ID"], e["goal"]), ("p13061", "p2473"))
        self.assertEqual(e["positions"]["p2473"][2], 1.5)

    def test_fixed_endpoint_routes(self):
        e = self.experiment
        start, goal = "p13061", "p2473"
        expected = [
            (0.40, 11.492680218053675, 0.44721361994743347, 6),
            (0.50, 11.848104306169116, 0.6324554681777954, 7),
            (0.70, 12.098943976678365, 0.9165151715278625, 8),
            (1.00, 12.42833077724467, 1.0, 6),
        ]
        args = (start, goal, e["adj"], e["positions"], e["clearance"])
        for threshold, length, interior, count in expected:
            with self.subTest(threshold=threshold):
                route = e["astar"](*args, min_clearance=threshold)
                measured_length = e["path_length"](route, e["positions"])
                measured_interior = e["interior_min_clearance"](route, e["clearance"])
                self.assertEqual((route[0], route[-1], len(route)), (start, goal, count))
                self.assertAlmostEqual(measured_length, length, delta=1e-6)
                self.assertAlmostEqual(measured_interior, interior, delta=1e-6)
                print(f"{threshold:.2f} {measured_length:.17g} {measured_interior:.17g}")
        self.assertLess(e["clearance"][start], 1.0)
        self.assertLess(e["clearance"][goal], 1.0)
        for threshold in (1.10, 1.20):
            self.assertIsNone(e["astar"](*args, min_clearance=threshold))


class ExportTest(unittest.TestCase):
    def test_saved_graph_and_failure_cases(self):
        if not REFERENCE.is_file():
            self.skipTest("The local-only Small House fixture is required")
        import json
        import shutil
        import subprocess
        import tempfile

        script = MODULE.parent / "hydra_mapping/scripts/export_dsg.sh"
        with tempfile.TemporaryDirectory(dir=os.environ.get("SWARMX_TEST_TMP")) as folder:
            run = Path(folder)
            backend = run / "hydra/backend"
            backend.mkdir(parents=True)
            source = backend / "dsg.json"
            shutil.copyfile(REFERENCE, source)
            (run / ".mapping.lock").touch()
            status = run / "hydra_exit.json"
            status.write_text('{"returncode": 0}')
            (backend / "dsg_with_mesh.json").touch()
            output = run / "output.json"
            command = ["bash", str(script), str(run), str(output)]
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual(output.read_bytes(), REFERENCE.read_bytes())
            record = json.loads((run / "output.json.export.json").read_text())
            self.assertEqual(record["graph"]["sha256"], SHA256)
            self.assertEqual(record["dsg_with_mesh"]["state"], "empty")
            self.assertEqual(record["mesh_ply"]["state"], "missing")
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(output.read_bytes(), REFERENCE.read_bytes())

            other = command[:-1] + [str(run / "other.json")]
            status.write_text('{"returncode": -15}')
            self.assertIn(b"before a clean save", subprocess.run(other, capture_output=True).stderr)
            status.write_text('{"returncode": 0}')
            source.write_bytes(b"")
            self.assertIn(b"Empty graph", subprocess.run(other, capture_output=True).stderr)
            source.write_text('{"truncated":')
            failed = subprocess.run(other, capture_output=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse((run / "other.json").exists())
