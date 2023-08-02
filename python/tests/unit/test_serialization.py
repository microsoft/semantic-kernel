import typing as t

import pydantic as pdt
import pytest

from semantic_kernel.core_skills.conversation_summary_skill import (
    ConversationSummarySkill,
)
from semantic_kernel.core_skills.file_io_skill import FileIOSkill
from semantic_kernel.core_skills.http_skill import HttpSkill
from semantic_kernel.core_skills.math_skill import MathSkill
from semantic_kernel.core_skills.text_memory_skill import TextMemorySkill
from semantic_kernel.core_skills.text_skill import TextSkill
from semantic_kernel.core_skills.time_skill import TimeSkill
from semantic_kernel.core_skills.wait_skill import WaitSkill
from semantic_kernel.core_skills.web_search_engine_skill import WebSearchEngineSkill
from semantic_kernel.sk_pydantic import PydanticField

PydanticFieldT = t.TypeVar("PydanticFieldT", bound=PydanticField)


@pytest.mark.parametrize(
    "sk_type",
    [
        pytest.param(
            ConversationSummarySkill, marks=pytest.mark.xfail(reason="Contains data")
        ),
        FileIOSkill,
        HttpSkill,
        MathSkill,
        TextMemorySkill,
        TextSkill,
        TimeSkill,
        WaitSkill,
        pytest.param(
            WebSearchEngineSkill, marks=pytest.mark.xfail(reason="Contains data")
        ),
    ],
)
def test_usage_in_pydantic_fields(sk_type: t.Type[PydanticFieldT]) -> None:
    """Semantic Kernel objects should be valid Pydantic fields.

    Otherwise, they cannot be used in Pydantic models.
    """

    class TestModel(pdt.BaseModel):
        """A test model."""

        field: t.Optional[sk_type] = None

    test_model = TestModel()
    assert test_model is not None
    serialized = test_model.json()
    assert isinstance(serialized, str)
    deserialized = TestModel.parse_raw(serialized)
    assert isinstance(deserialized, TestModel)
    assert deserialized == test_model
