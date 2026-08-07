import json
from pathlib import Path

from puzzle_pipeline.reference import inspect_reference

ROOT = Path(__file__).resolve().parents[2]


def test_puzzle_019_reference_contract_matches_observed_fixture() -> None:
    archive = ROOT / "puzzle_019.zip"
    contract_path = ROOT / "tests" / "fixtures" / "reference" / "puzzle_019_contract.json"
    expected = json.loads(contract_path.read_text(encoding="utf-8"))

    observed = inspect_reference(archive)

    assert observed["grid"] == expected["grid"]
    assert observed["seed"] == expected["seed"]
    assert observed["piece_count"] == expected["piece_count"]
    assert observed["atlas_size"] == expected["atlas_size"]
    assert observed["thickness"] == expected["thickness"]
    assert observed["material_names"] == expected["material_names"]
    assert observed["front_axis"] == expected["front_axis"]
    assert observed["pivot_policy"] == expected["pivot_policy"]
    assert observed["files"] == expected["files"]
