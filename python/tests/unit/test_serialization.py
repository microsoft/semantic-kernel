import logging
import typing as t

import pydantic as pdt
import pytest
import typing_extensions as te

from semantic_kernel import SKFunctionBase
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
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.delegate_handlers import DelegateHandlers
from semantic_kernel.orchestration.delegate_inference import DelegateInference
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function import SKFunction
from semantic_kernel.sk_pydantic import PydanticField, SKBaseModel
from semantic_kernel.skill_definition.function_view import FunctionView
from semantic_kernel.skill_definition.functions_view import FunctionsView
from semantic_kernel.skill_definition.parameter_view import ParameterView
from semantic_kernel.skill_definition.read_only_skill_collection import (
    ReadOnlySkillCollection,
)
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)
from semantic_kernel.skill_definition.sk_function_decorator import sk_function
from semantic_kernel.skill_definition.skill_collection import SkillCollection
from semantic_kernel.skill_definition.skill_collection_base import SkillCollectionBase
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.code_block import CodeBlock
from semantic_kernel.template_engine.blocks.function_id_block import FunctionIdBlock
from semantic_kernel.template_engine.blocks.text_block import TextBlock
from semantic_kernel.template_engine.blocks.val_block import ValBlock
from semantic_kernel.template_engine.blocks.var_block import VarBlock
from semantic_kernel.template_engine.code_tokenizer import CodeTokenizer
from semantic_kernel.template_engine.prompt_template_engine import PromptTemplateEngine
from semantic_kernel.template_engine.protocols.code_renderer import CodeRenderer
from semantic_kernel.template_engine.protocols.prompt_templating_engine import (
    PromptTemplatingEngine,
)
from semantic_kernel.template_engine.protocols.text_renderer import TextRenderer
from semantic_kernel.template_engine.template_tokenizer import TemplateTokenizer

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

    def create_functions_view() -> FunctionsView:
        """Return a functions view."""
        result = FunctionsView()
        result.add_function(
            FunctionView(
                name="function1",
                skill_name="skill1",
                description="Native function",
                parameters=[],
                is_semantic=False,
                is_asynchronous=True,
            )
        )
        result.add_function(
            FunctionView(
                name="function1",
                skill_name="skill1",
                description="Semantic function",
                parameters=[],
                is_semantic=True,
                is_asynchronous=True,
            )
        )
        return result

    def create_sk_function() -> SKFunction:
        """Return an SKFunction."""

        @sk_function(name="function")
        def my_function_async(cx: SKContext) -> str:
            return f"F({cx.variables.input})"

        return SKFunction.from_native_method(my_function_async)

    def create_context_variables() -> ContextVariables:
        """Return a context variables object."""
        return ContextVariables(
            content="content",
            variables={"foo": "bar"},
        )

    def create_skill_collection() -> SkillCollection:
        """Return a skill collection."""
        # TODO: Add a few skills to this collection.
        return SkillCollection()

    cls_obj_map = {
        Block: Block("foo"),
        CodeBlock: CodeBlock("foo"),
        FunctionIdBlock: FunctionIdBlock("bar"),
        TextBlock: TextBlock("baz"),
        ValBlock: ValBlock("qux"),
        VarBlock: VarBlock("quux"),
        CodeTokenizer: CodeTokenizer(log=logging.getLogger("test")),
        PromptTemplateEngine: PromptTemplateEngine(logger=logging.getLogger("test")),
        TemplateTokenizer: TemplateTokenizer(log=logging.getLogger("test")),
        ParameterView: ParameterView("foo", "bar", default_value="baz"),
        FunctionView: FunctionView(
            "foo",
            "bar",
            "baz",
            [ParameterView("qux", "bar", "baz")],
            True,
            False,
        ),
        FunctionsView: create_functions_view(),
        ReadOnlySkillCollection: create_skill_collection().read_only_skill_collection,
        DelegateHandlers: DelegateHandlers(),
        DelegateInference: DelegateInference(),
        ContextVariables: create_context_variables(),
        SkillCollection: create_skill_collection(),
        SKContext[NullMemory]: SKContext(
            # TODO: Test serialization with different types of memories.
            memory=NullMemory(),
            variables=create_context_variables(),
            skill_collection=create_skill_collection().read_only_skill_collection,
        ),
        NullMemory: NullMemory(),
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

BASE_CLASSES = [
    ReadOnlySkillCollectionBase,
    SkillCollectionBase,
    SemanticTextMemoryBase,
    SKFunctionBase,
]

# Classes that don't need serialization
UNSERIALIZED_CLASSES = [
    ReadOnlySkillCollection,
]

STATELESS_CLASSES = [
    CodeTokenizer,
    PromptTemplateEngine,
    TemplateTokenizer,
    DelegateHandlers,
    DelegateInference,
    NullMemory,
]

ENUMS = [
    BlockTypes,
    DelegateInference,
]

PYDANTIC_MODELS = [
    Block,
    CodeBlock,
    FunctionIdBlock,
    TextBlock,
    ValBlock,
    VarBlock,
    ParameterView,
    FunctionView,
    FunctionsView,
    ReadOnlySkillCollection,
    SkillCollection,
    ContextVariables,
    SKContext[NullMemory],
    pytest.param(
        SKFunction,
        marks=pytest.mark.xfail(reason="Need to implement Pickle serialization."),
    ),
]


class TestUsageInPydanticFields:
    @pytest.mark.parametrize(
        "sk_type",
        BASE_CLASSES
        + PROTOCOLS
        + ENUMS
        + PYDANTIC_MODELS
        + STATELESS_CLASSES
        + UNSERIALIZED_CLASSES,
    )
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

    @pytest.mark.parametrize("sk_type", PYDANTIC_MODELS + STATELESS_CLASSES)
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
