# TODO: replace Exception with KernelException once those are more pythonic
class BlockError(Exception):
    pass


class BlockSyntaxError(BlockError):
    pass


class BlockRenderError(BlockError):
    pass


class VarBlockSyntaxError(BlockSyntaxError):
    def __init__(self, content: str) -> None:
        super().__init__(
            f"A VarBlock starts with a '$' followed by at least one letter, \
number or underscore, anything else is invalid. \
The content provided was: {content}",
        )


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


class CodeBlockTokenError(BlockError):
    pass


class CodeBlockRenderError(BlockRenderError):
    pass


class TemplateSyntaxError(BlockSyntaxError):
    pass
