import abc
import json
import typing as t

import typing_extensions as te
from pydantic.parse import Protocol
from pydantic.types import StrBytes


class PydanticField(abc.ABC):
    """Subclass this class to make your class a valid pydantic field type.

    This class is a no-op, but it's necessary to make pydantic recognize your class as
    a valid field type. See https://pydantic-docs.helpmanual.io/usage/types/#custom-data-types
    for more information.

    - If you want to add validation to your class, you can do so by implementing the
    `__get_validators__` class method. See
    https://pydantic-docs.helpmanual.io/usage/validators/ for more information.
    - If you want to add serialization to your class, you can do so by implementing the
    `json` and `parse_raw` methods. See
    https://pydantic-docs.helpmanual.io/usage/exporting_models/#json for more information.
    """

    @classmethod
    def __get_validators__(cls) -> t.Generator[t.Callable[..., t.Any], None, None]:
        """Gets the validators for the class."""
        yield cls.no_op_validate

    @classmethod
    def no_op_validate(cls, v: t.Any) -> t.Any:
        """Does no validation, just returns the value."""
        if v is None:
            v = cls()
        if isinstance(v, str):
            v = cls(**json.loads(v))
        return v

    def json(self) -> str:
        """Serialize the model to JSON."""
        return "{}"

    @classmethod
    def parse_raw(
        cls: t.Type[te.Self],
        b: StrBytes,
        *,
        content_type: str = None,
        encoding: str = "utf8",
        proto: Protocol = None,
        allow_pickle: bool = False,
    ) -> te.Self:
        """Parse a raw byte string into a model."""
        return cls()

    def __eq__(self, other: t.Any) -> bool:
        """Check if two instances are equal."""
        return isinstance(other, self.__class__)
