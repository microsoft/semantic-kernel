# Copyright (c) Microsoft. All rights reserved.
<<<<<<< Updated upstream
<<<<<<< Updated upstream

from abc import ABC, abstractmethod
from typing import Any, TypeVar
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD

from abc import ABC, abstractmethod
from typing import Any, TypeVar
=======
<<<<<<< HEAD

from abc import ABC, abstractmethod
from typing import Any, TypeVar
=======
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel

<<<<<<< Updated upstream
<<<<<<< Updated upstream
_T = TypeVar("_T", bound="KernelContent")

=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
_T = TypeVar("_T", bound="KernelContent")

=======
<<<<<<< HEAD
_T = TypeVar("_T", bound="KernelContent")

=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

class KernelContent(KernelBaseModel, ABC):
    """Base class for all kernel contents."""

<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    inner_content: Any | None = None
    ai_model_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @abstractmethod
    def __str__(self) -> str:
        """Return the string representation of the content."""

    @abstractmethod
    def to_element(self) -> Any:
        """Convert the instance to an Element."""

    @classmethod
    @abstractmethod
    def from_element(cls: type[_T], element: Any) -> _T:
        """Create an instance from an Element."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
    inner_content: Optional[Any] = None
    ai_model_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @abstractmethod
    def __str__(self) -> str:
        pass
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
