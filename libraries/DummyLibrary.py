"""RF-importable library written in Python.

Attention! Please rename it and add your own useful keywords and documentation.
"""

from robot.api import logger

# Variables can be accessed from the resources/variables.py Python module here as well.
from variables import TODAY


class DummyLibrary:
    """Set a proper name, add useful methods and document it accordingly."""

    def __init__(self):
        """Add and document optional input data passed during the import. ([kw]args)"""
        # Additionally, add a state available for the entire life of the library.
        self._context = None  # just a dummy example (used later on in the methods)

    def log_today_in_python(self) -> None:
        """Displays today's date in Python."""
        logger.info(f"Today is {TODAY}. (from Python)")
        self._context = "under logging keyword"

    def my_library_keyword(self, var: str = "test") -> str:
        """Describe what this RF exposed keyword does."""
        logger.info("Python code (as RF keyword) executed with value: %s", var)
        self._context = "under my keyword"
        return var
