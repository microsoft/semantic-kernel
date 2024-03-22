# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class BlockException(KernelException):
    pass


class BlockSyntaxError(BlockException):
    pass


class BlockRenderException(BlockException):
    pass


class VarBlockSyntaxError(BlockSyntaxError):
    def __init__(self, content: str) -> None:
        super().__init__(
            f"A VarBlock starts with a '$' followed by at least one letter, \
number or underscore, anything else is invalid. \
The content provided was: {content}",
        )


class VarBlockRenderError(BlockRenderException):
    pass


class ValBlockSyntaxError(BlockSyntaxError):
    def __init__(self, content: str) -> None:
        super().__init__(
            f"A ValBlock starts with a single or double quote followed by at least one letter, \
finishing with the same type of quote as the first one. \
The content provided was: {content}",
        )


class NamedArgBlockSyntaxError(BlockSyntaxError):
    def __init__(self, content: str) -> None:
        super().__init__(
            f"A NamedArgBlock starts with a name (letters, numbers or underscore) \
followed by a single equal sign, then the value of the argument, \
which can either be a VarBlock (starting with '$') \
or a ValBlock (text surrounded by quotes). \
The content provided was: {content}",
        )


class FunctionIdBlockSyntaxError(BlockSyntaxError):
    def __init__(self, content: str) -> None:
        super().__init__(
            f"A FunctionIdBlock is composed of either a plugin name and \
function name separated by a single dot, or just a function name. \
Both plugin and function names can only contain letters, numbers and underscores. \
The content provided was: {content}",
        )


class CodeBlockSyntaxError(BlockSyntaxError):
    pass


class CodeBlockTokenError(BlockException):
    pass


class CodeBlockRenderException(BlockRenderException):
    pass


class TemplateSyntaxError(BlockSyntaxError):
    pass


class TemplateRenderException(BlockRenderException):
    pass


class HandlebarsTemplateSyntaxError(BlockSyntaxError):
    pass


class HandlebarsTemplateRenderException(BlockRenderException):
    pass


class Jinja2TemplateSyntaxError(BlockSyntaxError):
    pass


class Jinja2TemplateRenderException(BlockRenderException):
    pass


__all__ = [
    "BlockException",
    "BlockSyntaxError",
    "BlockRenderException",
    "VarBlockSyntaxError",
    "VarBlockRenderError",
    "ValBlockSyntaxError",
    "NamedArgBlockSyntaxError",
    "FunctionIdBlockSyntaxError",
    "CodeBlockSyntaxError",
    "CodeBlockTokenError",
    "CodeBlockRenderException",
    "TemplateSyntaxError",
    "TemplateRenderException",
    "HandlebarsTemplateSyntaxError",
    "HandlebarsTemplateRenderException",
    "Jinja2TemplateSyntaxError",
    "Jinja2TemplateRenderException",
]
