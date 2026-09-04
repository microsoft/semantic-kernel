# Copyright (c) Microsoft. All rights reserved.

"""Keeps docs/CONNECTOR_EXTRAS.md checkable against the package metadata in pyproject.toml.

The doc lists, for every public connector, the install extra it needs and the upstream
packages that extra declares. This test parses both files and fails when they drift:

* an extra named in the doc that does not exist in pyproject.toml,
* a connector extra in pyproject.toml that no doc row mentions,
* upstream package names for an extra that differ between the two files,
* a version specifier in the doc that no longer matches pyproject.toml,
* an import path in the doc that does not exist on disk,
* a row claiming a package that its own connector never imports.

Stdlib only, no network, no project extras required.
"""

import re
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - Python 3.10 only, tomli ships with pytest there
    import tomli as tomllib

PYTHON_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = PYTHON_ROOT / "pyproject.toml"
DOC = PYTHON_ROOT / "docs" / "CONNECTOR_EXTRAS.md"

# Table header that marks a connector table in the doc. Other tables in the doc are ignored.
TABLE_HEADER = ("Connector", "Import path", "Install extra", "Upstream package(s) & constraint")

# Extras that exist in pyproject.toml but are deliberately not connector extras, so they have
# no row in the doc. Listed explicitly so that intent is stated instead of silently ignored.
NON_CONNECTOR_EXTRAS = {
    "autogen",  # agent integration, semantic_kernel/agents/autogen
    "copilotstudio",  # agent integration, semantic_kernel/agents/copilot_studio
    "notebooks",  # ipykernel, for the sample notebooks
    "pandas",  # sample and test helper
    "realtime",  # websockets/aiortc, both already base dependencies
}

BACKTICKED = re.compile(r"`([^`]+)`")
DIST_NAME = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")
HAS_SPECIFIER = re.compile(r"[<>=!~]")
EXTRA_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
IMPORTED = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][\w.]*)", re.MULTILINE)


def _canonical_name(requirement: str) -> str:
    """Return the PEP 503 normalized distribution name of a requirement string."""
    match = DIST_NAME.match(requirement.strip())
    if not match:
        return ""
    return re.sub(r"[-_.]+", "-", match.group(1)).lower()


def _normalize(requirement: str) -> str:
    """Drop the environment marker and all whitespace so two spellings compare equal."""
    return re.sub(r"\s+", "", requirement.split(";", 1)[0])


def _load_pyproject() -> tuple[list[str], dict[str, list[str]]]:
    with PYPROJECT.open("rb") as handle:
        data = tomllib.load(handle)
    project = data["project"]
    return project["dependencies"], project["optional-dependencies"]


def _parse_rows() -> list[dict]:
    """Parse every connector table in the doc into rows."""
    rows: list[dict] = []
    lines = DOC.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        cells = _split_row(lines[index])
        if tuple(cells) != TABLE_HEADER:
            index += 1
            continue
        index += 2  # skip the header and the `| --- |` separator
        while index < len(lines) and lines[index].startswith("|"):
            cells = _split_row(lines[index])
            assert len(cells) == 4, f"{DOC.name} line {index + 1}: expected 4 columns, got {len(cells)}"
            rows.append({
                "line": index + 1,
                "connector": cells[0],
                "import_path": _single_backticked(cells[1], index + 1),
                "extras": _extras_of(cells[2], index + 1),
                "upstream": BACKTICKED.findall(cells[3]),
            })
            index += 1
    return rows


def _split_row(line: str) -> list[str]:
    if not line.startswith("|"):
        return []
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _single_backticked(cell: str, line_no: int) -> str:
    found = BACKTICKED.findall(cell)
    assert len(found) == 1, f"{DOC.name} line {line_no}: expected exactly one `import path`, got {found}"
    return found[0]


def _extras_of(cell: str, line_no: int) -> set[str]:
    found = {token for token in BACKTICKED.findall(cell) if EXTRA_NAME.match(token)}
    assert found, f"{DOC.name} line {line_no}: install extra column must name an extra or `none`"
    return found


def test_doc_and_pyproject_exist():
    assert DOC.is_file(), f"{DOC} is missing"
    assert PYPROJECT.is_file(), f"{PYPROJECT} is missing"
    assert _parse_rows(), "no connector table rows were parsed from the doc"


def test_non_connector_allow_list_is_real():
    """The allow-list must only name extras that actually exist, so it cannot go stale."""
    _, optional = _load_pyproject()
    unknown = NON_CONNECTOR_EXTRAS - set(optional)
    assert not unknown, f"NON_CONNECTOR_EXTRAS names extras that no longer exist in pyproject.toml: {sorted(unknown)}"


def test_every_documented_extra_exists_in_pyproject():
    _, optional = _load_pyproject()
    for row in _parse_rows():
        for extra in sorted(row["extras"]):
            if extra == "none":
                continue
            assert extra in optional, (
                f"{DOC.name} line {row['line']} ({row['connector']}): extra '{extra}' is not declared in "
                f"[project.optional-dependencies]"
            )


def test_every_connector_extra_is_documented():
    _, optional = _load_pyproject()
    documented = {extra for row in _parse_rows() for extra in row["extras"]} - {"none"}
    missing = set(optional) - NON_CONNECTOR_EXTRAS - documented
    assert not missing, (
        f"these extras are declared in pyproject.toml but have no row in {DOC.name}: {sorted(missing)}. "
        f"Add a row, or add the extra to NON_CONNECTOR_EXTRAS with a reason."
    )


def test_upstream_package_names_match_pyproject():
    """The packages listed per extra in the doc must be exactly what that extra declares."""
    _, optional = _load_pyproject()
    documented: dict[str, set[str]] = {}
    for row in _parse_rows():
        extras = row["extras"] - {"none"}
        if not extras:
            continue
        for requirement in row["upstream"]:
            name = _canonical_name(requirement)
            owners = [extra for extra in extras if name in {_canonical_name(r) for r in optional[extra]}]
            assert owners, (
                f"{DOC.name} line {row['line']} ({row['connector']}): '{requirement}' is not declared by any of "
                f"{sorted(extras)} in pyproject.toml"
            )
            for owner in owners:
                documented.setdefault(owner, set()).add(name)

    for extra, names in sorted(documented.items()):
        expected = {_canonical_name(requirement) for requirement in optional[extra]}
        assert names == expected, (
            f"extra '{extra}': {DOC.name} documents {sorted(names)} but pyproject.toml declares {sorted(expected)}"
        )


def test_version_constraints_match_pyproject():
    """Every version specifier printed in the doc must still be the one pyproject.toml declares."""
    dependencies, optional = _load_pyproject()
    base = {_normalize(requirement) for requirement in dependencies}
    for row in _parse_rows():
        extras = row["extras"] - {"none"}
        allowed = base if not extras else {_normalize(r) for extra in extras for r in optional[extra]}
        for requirement in row["upstream"]:
            if not HAS_SPECIFIER.search(requirement):
                continue  # documentation-only entry, e.g. a transitive dependency
            assert _normalize(requirement) in allowed, (
                f"{DOC.name} line {row['line']} ({row['connector']}): '{requirement}' does not match the "
                f"constraint declared in pyproject.toml for {sorted(extras) or '[project] dependencies'}"
            )


def test_documented_import_paths_exist():
    for row in _parse_rows():
        parts = row["import_path"].split(".")
        package = PYTHON_ROOT.joinpath(*parts)
        module = package.with_suffix(".py")
        assert (package / "__init__.py").is_file() or module.is_file(), (
            f"{DOC.name} line {row['line']} ({row['connector']}): import path '{row['import_path']}' "
            f"does not exist under {PYTHON_ROOT}"
        )


def _import_names(import_path: str) -> set[str]:
    """Every module name imported by the connector module or package at `import_path`."""
    parts = import_path.split(".")
    package = PYTHON_ROOT.joinpath(*parts)
    sources = sorted(package.rglob("*.py")) if package.is_dir() else [package.with_suffix(".py")]
    names: set[str] = set()
    for source in sources:
        for match in IMPORTED.finditer(source.read_text(encoding="utf-8")):
            names.add(match.group(1))
    return names


def _import_candidates(requirement: str) -> set[str]:
    """Plausible import names for a distribution name, widest last."""
    name = _canonical_name(requirement)
    return {name.replace("-", "_"), name.replace("-", "."), name.split("-", 1)[0]}


def test_documented_packages_are_actually_imported_by_the_connector():
    """A row must not claim a package its own connector never imports.

    This is what stops a self-consistent wrong pairing: without it a row can name a real
    extra whose real packages simply belong to a different connector, and every other
    check in this file still passes.
    """
    for row in _parse_rows():
        if not row["extras"] - {"none"}:
            continue  # base-install connectors, nothing extra to attribute
        imported = _import_names(row["import_path"])
        hit = any(
            candidate == name or name.startswith(f"{candidate}.")
            for requirement in row["upstream"]
            for candidate in _import_candidates(requirement)
            for name in imported
        )
        assert hit, (
            f"{DOC.name} line {row['line']} ({row['connector']}): none of {row['upstream']} is imported "
            f"anywhere under '{row['import_path']}' -- the row attributes a package to the wrong connector"
        )
