import typing as t

import pydantic as pdt
import pytest
import typing_extensions as te

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
from semantic_kernel.sk_pydantic import PydanticField, SKBaseModel
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.code_block import CodeBlock
from semantic_kernel.template_engine.blocks.function_id_block import FunctionIdBlock
from semantic_kernel.template_engine.blocks.text_block import TextBlock
from semantic_kernel.template_engine.blocks.val_block import ValBlock
from semantic_kernel.template_engine.blocks.var_block import VarBlock
from semantic_kernel.template_engine.protocols.code_renderer import CodeRenderer
from semantic_kernel.template_engine.protocols.prompt_templating_engine import (
    PromptTemplatingEngine,
)
from semantic_kernel.template_engine.protocols.text_renderer import TextRenderer

PydanticFieldT = t.TypeVar("PydanticFieldT", bound=PydanticField)


class _Serializable(t.Protocol):
    """A serializable object."""

    def json(self) -> pdt.Json:
        """Return a JSON representation of the object."""
        raise NotImplementedError

    @classmethod
    def parse_raw(cls: t.Type[te.Self], json: pdt.Json) -> te.Self:
        """Return the constructed object from a JSON representation."""
        raise NotImplementedError


@pytest.fixture()
def sk_factory() -> t.Callable[[t.Type[_Serializable]], _Serializable]:
    """Return a factory for various objects in semantic-kernel."""
    cls_obj_map = {
        Block: Block("foo"),
        CodeBlock: CodeBlock("foo"),
        FunctionIdBlock: FunctionIdBlock("bar"),
        TextBlock: TextBlock("baz"),
        ValBlock: ValBlock("qux"),
        VarBlock: VarBlock("quux"),
    }

    def constructor(cls: t.Type[_Serializable]) -> _Serializable:
        """Return a serializable object."""
        return cls_obj_map[cls]

    return constructor


PROTOCOLS = [
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
    pytest.param(WebSearchEngineSkill, marks=pytest.mark.xfail(reason="Contains data")),
    CodeRenderer,
    PromptTemplatingEngine,
    TextRenderer,
]

ENUMS = [BlockTypes]

PYDANTIC_MODELS = [
    Block,
    CodeBlock,
    FunctionIdBlock,
    TextBlock,
    ValBlock,
    VarBlock,
]


class TestUsageInPydanticFields:
    @pytest.mark.parametrize("sk_type", PROTOCOLS + ENUMS + PYDANTIC_MODELS)
    def test_usage_as_optional_field(
        self,
        sk_type: t.Type[PydanticFieldT],
    ) -> None:
        """Semantic Kernel objects should be valid Pydantic fields.

        Otherwise, they cannot be used in Pydantic models.
        """

        class TestModel(SKBaseModel):
            """A test model."""

            field: t.Optional[sk_type] = None

        assert_serializable(TestModel(), TestModel)

    @pytest.mark.parametrize("sk_type", PYDANTIC_MODELS)
    def test_usage_as_required_field(
        self,
        sk_factory: t.Callable[[t.Type[PydanticFieldT]], PydanticFieldT],
        sk_type: t.Type[PydanticFieldT],
    ) -> None:
        """Semantic Kernel objects should be valid Pydantic fields.

        Otherwise, they cannot be used in Pydantic models.
        """

        class TestModel(SKBaseModel):
            """A test model."""

            field: sk_type = pdt.Field(default_factory=lambda: sk_factory(sk_type))

        assert_serializable(TestModel(), TestModel)
        assert_serializable(TestModel(field=sk_factory(sk_type)), TestModel)


def assert_serializable(obj: _Serializable, obj_type) -> None:
    """Assert that an object is serializable."""
    assert obj is not None
    serialized = obj.json()
    assert isinstance(serialized, str)
    deserialized = obj_type.parse_raw(serialized)
    assert deserialized == obj
