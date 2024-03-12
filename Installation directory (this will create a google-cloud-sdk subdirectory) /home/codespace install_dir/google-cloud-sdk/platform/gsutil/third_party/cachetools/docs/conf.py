def get_version():
    import configparser
    import pathlib

    cp = configparser.ConfigParser()
    cp.read(pathlib.Path(__file__).parent.parent / "setup.cfg")
    return cp["metadata"]["version"]


project = "cachetools"
copyright = "2014-2021 Thomas Kemmer"
version = get_version()
release = version

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
]
exclude_patterns = ["_build"]
master_doc = "index"
html_theme = "default"
