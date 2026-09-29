# Copyright (c) Microsoft. All rights reserved.

import re
from pathlib import Path


PYTHON_ROOT = Path(__file__).parents[2]
PYPROJECT = PYTHON_ROOT / "pyproject.toml"
CONNECTOR_DOC = PYTHON_ROOT / "CONNECTOR_DEPENDENCIES.md"


def _optional_extra_names(pyproject_text: str) -> set[str]:
    marker = "[project.optional-dependencies]"
    assert marker in pyproject_text

    optional_block = pyproject_text.split(marker, 1)[1].split("\n[", 1)[0]
    return set(re.findall(r"^([a-z][a-z0-9_]*)\s*=\s*\[", optional_block, flags=re.MULTILINE))


def test_connector_dependency_doc_lists_every_optional_extra():
    extras = _optional_extra_names(PYPROJECT.read_text(encoding="utf-8"))
    doc = CONNECTOR_DOC.read_text(encoding="utf-8")
    documented = set(re.findall(r"\| `([a-z][a-z0-9_]*)` \|", doc))

    assert extras <= documented, f"Undocumented optional extras: {sorted(extras - documented)}"
