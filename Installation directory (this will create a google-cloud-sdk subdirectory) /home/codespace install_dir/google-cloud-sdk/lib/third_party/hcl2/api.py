"""The API that will be exposed to users of this package"""
from typing import TextIO

from hcl2.parser import hcl2
from hcl2.transformer import DictTransformer


def load(file: TextIO, with_meta=False) -> dict:
    """Load a HCL2 file.
    :param file: File with hcl2 to be loaded as a dict.
    :param with_meta: If set to true then adds `__start_line__` and `__end_line__`
    parameters to the output dict. Default to false.
    """
    return loads(file.read(), with_meta=with_meta)


def loads(text: str, with_meta=False) -> dict:
    """Load HCL2 from a string.
    :param text: Text with hcl2 to be loaded as a dict.
    :param with_meta: If set to true then adds `__start_line__` and `__end_line__`
    parameters to the output dict. Default to false.
    """
    # append new line as a workaround for https://github.com/lark-parser/lark/issues/237
    # Lark doesn't support a EOF token so our grammar can't look for "new line or end of file"
    # This means that all blocks must end in a new line even if the file ends
    # Append a new line as a temporary fix
    tree = hcl2.parse(text + "\n")
    return DictTransformer(with_meta=with_meta).transform(tree)
