"""A parser for HCL2 implemented using the Lark parser"""
from pathlib import Path

from lark import Lark


PARSER_FILE = Path(__file__).absolute().resolve().parent / ".lark_cache.bin"


hcl2 = Lark.open(
    "hcl2.lark",
    parser="lalr",
    cache=str(PARSER_FILE),  # Disable/Delete file to effect changes to the grammar
    rel_to=__file__,
    propagate_positions=True,
)
