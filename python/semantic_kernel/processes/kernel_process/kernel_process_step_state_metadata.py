# Copyright (c) Microsoft. All rights reserved.

import logging
from pathlib import Path
from typing import ClassVar, Generic, Literal, TypeVar

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental

TState = TypeVar("TState")

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class KernelProcessStepStateMetadata(KernelBaseModel, Generic[TState]):
    """Process state used for State Persistence serialization."""

    type_: Literal["Step", "Process"] = Field(
        "Step", alias="$type"
    )  # satisfies mypy to have `Steps` and `Process` as type
    id: str | None = Field(None, alias="id")
    name: str | None = Field(None, alias="name")
    version_info: str | None = Field(None, alias="versionInfo")
    state: TState | None = Field(None, alias="state")  # type: ignore[valid-type]


@experimental
class KernelProcessStateMetadata(KernelProcessStepStateMetadata[TState]):
    """Process state used for State Persistence serialization."""

    type_: Literal["Process"] = Field("Process", alias="$type")
    steps_state: dict[str, "KernelProcessStateMetadata | KernelProcessStepStateMetadata"] = Field(
        default_factory=dict, alias="stepsState"
    )

    model_config: ClassVar = {
        "populate_by_name": True,
    }

    @classmethod
    def load_from_file(
        cls,
        json_filename: str,
        directory: str | Path,
        encoding: str = "utf-8",
    ) -> "KernelProcessStateMetadata | None":
        """Loads a KernelProcessStateMetadata instance from a JSON file.

        Args:
            json_filename (str): Name of the JSON file to load.
            directory (str | Path): Base directory where the file resides.
                Can be relative or absolute.
            encoding (str, optional): Encoding to use when reading the file. Defaults to 'utf-8'.

        Returns:
            KernelProcessStateMetadata | None: Loaded process state metadata or None on failure.
        """
        base_dir = Path(directory)
        file_path = base_dir / json_filename

        if not file_path.exists():
            logger.warning(f"File not found: '{file_path.resolve()}'")
            return None

        try:
            with open(file_path, encoding=encoding) as f:
                file_contents = f.read()
                return cls.model_validate_json(file_contents)
        except Exception as ex:
            logger.error(f"Error reading file '{file_path.resolve()}': {ex}")
            return None
