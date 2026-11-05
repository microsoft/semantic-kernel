# Copyright (c) Microsoft. All rights reserved.

import tomllib
from pathlib import Path


def test_runtime_protobuf_dependency_is_declared() -> None:
    """The agents runtime imports google.protobuf, so it must be a declared dependency."""
    pyproject = tomllib.loads((Path(__file__).parents[2] / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]
    assert any(dependency.lower().startswith("protobuf") for dependency in dependencies)
