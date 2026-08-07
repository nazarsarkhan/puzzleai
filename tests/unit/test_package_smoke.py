import re

import puzzle_pipeline


def test_package_exposes_semantic_version() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", puzzle_pipeline.__version__)
