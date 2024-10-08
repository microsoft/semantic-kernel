# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from abc import ABC, abstractmethod
from typing import Any

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover

from semantic_kernel.exceptions.content_exceptions import ContentAdditionException
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger: logging.Logger = logging.getLogger(__name__)


class StreamingContentMixin(KernelBaseModel, ABC):
    """Mixin class for all streaming kernel contents."""

    choice_index: int

    @abstractmethod
    def __bytes__(self) -> bytes:
        """Return the content of the response encoded in the encoding."""
        pass

    @abstractmethod
    def __add__(self, other: Any) -> Self:
        """Combine two streaming contents together."""
        pass

    def _merge_items_lists(self, other_items: list[Any]) -> list[Any]:
        """Create a new list with the items of the current instance and the given list."""
        if not hasattr(self, "items"):
            raise ContentAdditionException(f"Cannot merge items for this instance of type: {type(self)}")

        # Create a copy of the items list to avoid modifying the original instance.
        # Note that the items are not copied, only the list is.
        new_items_list = self.items.copy()

        if new_items_list or other_items:
            for other_item in other_items:
                added = False
                for id, item in enumerate(new_items_list):
                    if type(item) is type(other_item) and hasattr(item, "__add__"):
                        try:
                            new_item = item + other_item  # type: ignore
                            new_items_list[id] = new_item
                            added = True
                        except (ValueError, ContentAdditionException) as ex:
                            logger.debug(f"Could not add item {other_item} to {item}.", exc_info=ex)
                            continue
                if not added:
                    logger.debug(f"Could not add item {other_item} to any item in the list. Adding it as a new item.")
                    new_items_list.append(other_item)

        return new_items_list

    def _merge_inner_contents(self, other_inner_content: Any | list[Any]) -> list[Any]:
        """Create a new list with the inner content of the current instance and the given one."""
        if not hasattr(self, "inner_content"):
            raise ContentAdditionException(f"Cannot merge inner content for this instance of type: {type(self)}")

        # Create a copy of the inner content list to avoid modifying the original instance.
        # Note that the inner content is not copied, only the list is.
        # If the inner content is not a list, it is converted to a list.
        if isinstance(self.inner_content, list):
            new_inner_contents_list = self.inner_content.copy()
        else:
            new_inner_contents_list = [self.inner_content]

        other_inner_content = (
            other_inner_content
            if isinstance(other_inner_content, list)
            else [other_inner_content]
            if other_inner_content
            else []
        )

        new_inner_contents_list.extend(other_inner_content)

        return new_inner_contents_list
