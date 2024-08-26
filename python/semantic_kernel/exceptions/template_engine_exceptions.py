# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class BlockException(KernelException):
    """Base class for all block exceptions."""


class BlockSyntaxError(BlockException):
    """A invalid block syntax was found."""


class BlockRenderException(BlockException):
    """An error occurred while rendering a block."""


class VarBlockSyntaxError(BlockSyntaxError):
    """A invalid VarBlock syntax was found."""

    def __init__(self, content: str) -> None:
        """Adds the context of the error to the generic message."""
        super().__init__(
            f"A VarBlock starts with a '$' followed by at least one letter, \
number or underscore, anything else is invalid. \
The content provided was: {content}",
        )


class VarBlockRenderError(BlockRenderException):
    """An error occurred while rendering a VarBlock."""


class ValBlockSyntaxError(BlockSyntaxError):
    """A invalid ValBlock syntax was found."""

    def __init__(self, content: str) -> None:
        """Adds the context of the error to the generic message."""
        super().__init__(
            f"A ValBlock starts with a single or double quote followed by at least one letter, \
finishing with the same type of quote as the first one. \
The content provided was: {content}",
        )


class NamedArgBlockSyntaxError(BlockSyntaxError):
    """A invalid NamedArgBlock syntax was found."""

    def __init__(self, content: str) -> None:
        """Adds the context of the error to the generic message."""
        super().__init__(
            f"A NamedArgBlock starts with a name (letters, numbers or underscore) \
followed by a single equal sign, then the value of the argument, \
which can either be a VarBlock (starting with '$') \
or a ValBlock (text surrounded by quotes). \
The content provided was: {content}",
        )


class FunctionIdBlockSyntaxError(BlockSyntaxError):
    """A invalid FunctionIdBlock syntax was found."""

    def __init__(self, content: str) -> None:
        """Adds the context of the error to the generic message."""
        super().__init__(
            f"A FunctionIdBlock is composed of either a plugin name and \
function name separated by a single dot, or just a function name. \
Both plugin and function names can only contain letters, numbers and underscores. \
The content provided was: {content}",
        )


class CodeBlockSyntaxError(BlockSyntaxError):
    """A invalid CodeBlock syntax was found."""


class CodeBlockTokenError(BlockException):
    """An error occurred while tokenizing a CodeBlock."""


class CodeBlockRenderException(BlockRenderException):
    """An error occurred while rendering a CodeBlock."""


class TemplateSyntaxError(BlockSyntaxError):
    """A invalid Template syntax was found."""


class TemplateRenderException(BlockRenderException):
    """An error occurred while rendering a Template."""


class HandlebarsTemplateSyntaxError(BlockSyntaxError):
    """A invalid HandlebarsTemplate syntax was found."""


class HandlebarsTemplateRenderException(BlockRenderException):
    """An error occurred while rendering a HandlebarsTemplate."""


class Jinja2TemplateSyntaxError(BlockSyntaxError):
    """A invalid Jinja2Template syntax was found."""


class Jinja2TemplateRenderException(BlockRenderException):
    """An error occurred while rendering a Jinja2Template."""


__all__ = [
    "BlockException",
    "BlockRenderException",
    "BlockSyntaxError",
    "CodeBlockRenderException",
    "CodeBlockSyntaxError",
    "CodeBlockTokenError",
    "FunctionIdBlockSyntaxError",
    "HandlebarsTemplateRenderException",
    "HandlebarsTemplateSyntaxError",
    "Jinja2TemplateRenderException",
    "Jinja2TemplateSyntaxError",
    "NamedArgBlockSyntaxError",
    "TemplateRenderException",
    "TemplateSyntaxError",
    "ValBlockSyntaxError",
    "VarBlockRenderError",
    "VarBlockSyntaxError",
]
