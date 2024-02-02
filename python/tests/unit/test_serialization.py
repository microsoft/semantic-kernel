import typing as t

import pytest
import typing_extensions as te
from pydantic import Field, Json

from semantic_kernel import KernelFunctionBase
from semantic_kernel.core_plugins.conversation_summary_plugin import (
    ConversationSummaryPlugin,
)
from semantic_kernel.core_plugins.file_io_plugin import FileIOPlugin
from semantic_kernel.core_plugins.http_plugin import HttpPlugin
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.text_memory_plugin import TextMemoryPlugin
from semantic_kernel.core_plugins.text_plugin import TextPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.core_plugins.wait_plugin import WaitPlugin
from semantic_kernel.core_plugins.web_search_engine_plugin import WebSearchEnginePlugin
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.delegate_handlers import DelegateHandlers
from semantic_kernel.orchestration.delegate_inference import DelegateInference
from semantic_kernel.orchestration.kernel_context import KernelContext
from semantic_kernel.orchestration.kernel_function import KernelFunction
from semantic_kernel.plugin_definition.function_view import FunctionView
from semantic_kernel.plugin_definition.functions_view import FunctionsView
from semantic_kernel.plugin_definition.kernel_function_decorator import kernel_function
from semantic_kernel.plugin_definition.kernel_plugin_collection import (
    KernelPluginCollection,
)
from semantic_kernel.plugin_definition.parameter_view import ParameterView
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

KernelBaseModelFieldT = t.TypeVar("KernelBaseModelFieldT", bound=KernelBaseModel)


class _Serializable(t.Protocol):
    """A serializable object."""

    def json(self) -> Json:
        """Return a JSON representation of the object."""
        raise NotImplementedError

    @classmethod
    def parse_raw(cls: t.Type[te.Self], json: Json) -> te.Self:
        """Return the constructed object from a JSON representation."""
        raise NotImplementedError


@pytest.fixture()
def kernel_factory() -> t.Callable[[t.Type[_Serializable]], _Serializable]:
    """Return a factory for various objects in semantic-kernel."""

    def create_functions_view() -> FunctionsView:
        """Return a functions view."""
        result = FunctionsView()
        result.add_function(
            FunctionView(
                name="function1",
                plugin_name="plugin1",
                description="Native function",
                parameters=[],
                is_semantic=False,
                is_asynchronous=True,
            )
        )
        result.add_function(
            FunctionView(
                name="function1",
                plugin_name="plugin1",
                description="Semantic function",
                parameters=[],
                is_semantic=True,
                is_asynchronous=True,
            )
        )
        return result

    def create_kernel_function() -> KernelFunction:
        """Return an KernelFunction."""

        @kernel_function(name="function")
        def my_function(cx: KernelContext) -> str:
            return f"F({cx.variables.input})"

        return KernelFunction.from_native_method(my_function)

    def create_context_variables() -> ContextVariables:
        """Return a context variables object."""
        return ContextVariables(
            content="content",
            variables={"foo": "bar"},
        )

    def create_plugin_collection() -> KernelPluginCollection:
        """Return a plugin collection."""
        # TODO: Add a few plugins to this collection.
        return KernelPluginCollection()

    cls_obj_map = {
        Block: Block(content="foo"),
        CodeBlock: CodeBlock(content="foo"),
        FunctionIdBlock: FunctionIdBlock(content="bar"),
        TextBlock: TextBlock(content="baz"),
        ValBlock: ValBlock(content="qux"),
        VarBlock: VarBlock(content="quux"),
        CodeTokenizer: CodeTokenizer(),
        PromptTemplateEngine: PromptTemplateEngine(),
        TemplateTokenizer: TemplateTokenizer(),
        ParameterView: ParameterView(
            name="foo",
            description="bar",
            default_value="baz",
            type="string",
            required=True,
        ),
        FunctionView: FunctionView(
            "foo",
            "bar",
            "baz",
            [ParameterView(name="qux", description="bar", default_value="baz")],
            True,
            False,
        ),
        FunctionsView: create_functions_view(),
        KernelPluginCollection: create_plugin_collection(),
        DelegateHandlers: DelegateHandlers(),
        DelegateInference: DelegateInference(),
        ContextVariables: create_context_variables(),
        KernelContext[NullMemory]: KernelContext[NullMemory](
            # TODO: Test serialization with different types of memories.
            variables=create_context_variables(),
            memory=NullMemory(),
            plugins=create_plugin_collection(),
        ),
        NullMemory: NullMemory(),
        KernelFunction: create_kernel_function(),
    }

    def constructor(cls: t.Type[_Serializable]) -> _Serializable:
        """Return a serializable object."""
        return cls_obj_map[cls]

    return constructor


PROTOCOLS = [
    pytest.param(ConversationSummaryPlugin, marks=pytest.mark.xfail(reason="Contains data")),
    FileIOPlugin,
    HttpPlugin,
    MathPlugin,
    TextMemoryPlugin,
    TextPlugin,
    TimePlugin,
    WaitPlugin,
    pytest.param(WebSearchEnginePlugin, marks=pytest.mark.xfail(reason="Contains data")),
    CodeRenderer,
    PromptTemplatingEngine,
    TextRenderer,
]

BASE_CLASSES = [
    SemanticTextMemoryBase,
    KernelFunctionBase,
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
    KernelPluginCollection,
    ContextVariables,
    KernelContext[NullMemory],
    pytest.param(
        KernelFunction,
        marks=pytest.mark.xfail(reason="Need to implement Pickle serialization."),
    ),
]


class TestUsageInPydanticFields:
    @pytest.mark.parametrize(
        "kernel_type",
        BASE_CLASSES + PROTOCOLS + ENUMS + PYDANTIC_MODELS + STATELESS_CLASSES,
    )
    def test_usage_as_optional_field(
        self,
        kernel_type: t.Type[KernelBaseModelFieldT],
    ) -> None:
        """Semantic Kernel objects should be valid Pydantic fields.

        Otherwise, they cannot be used in Pydantic models.
        """

        class TestModel(KernelBaseModel):
            """A test model."""

            field: t.Optional[kernel_type] = None

        assert_serializable(TestModel(), TestModel)

    @pytest.mark.parametrize("kernel_type", PYDANTIC_MODELS + STATELESS_CLASSES)
    def test_usage_as_required_field(
        self,
        kernel_factory: t.Callable[[t.Type[KernelBaseModelFieldT]], KernelBaseModelFieldT],
        kernel_type: t.Type[KernelBaseModelFieldT],
    ) -> None:
        """Semantic Kernel objects should be valid Pydantic fields.

        Otherwise, they cannot be used in Pydantic models.
        """

        class TestModel(KernelBaseModel):
            """A test model."""

            field: kernel_type = Field(default_factory=lambda: kernel_factory(kernel_type))

        assert_serializable(TestModel(), TestModel)
        assert_serializable(TestModel(field=kernel_factory(kernel_type)), TestModel)


def assert_serializable(obj: _Serializable, obj_type) -> None:
    """Assert that an object is serializable, uses both dump and dump_json methods."""
    assert obj is not None
    serialized = obj.model_dump_json()
    assert isinstance(serialized, str)
    assert obj_type.model_validate_json(serialized).model_dump() == obj.model_dump()
