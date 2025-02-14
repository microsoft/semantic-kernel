# Copyright (c) Microsoft. All rights reserved.

import typing as t

import pytest
import typing_extensions as te
from pydantic import Field, Json

from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins.conversation_summary_plugin import ConversationSummaryPlugin
from semantic_kernel.core_plugins.http_plugin import HttpPlugin
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.text_memory_plugin import TextMemoryPlugin
from semantic_kernel.core_plugins.text_plugin import TextPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.core_plugins.wait_plugin import WaitPlugin
from semantic_kernel.core_plugins.web_search_engine_plugin import WebSearchEnginePlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.code_block import CodeBlock
from semantic_kernel.template_engine.blocks.function_id_block import FunctionIdBlock
from semantic_kernel.template_engine.blocks.named_arg_block import NamedArgBlock
from semantic_kernel.template_engine.blocks.text_block import TextBlock
from semantic_kernel.template_engine.blocks.val_block import ValBlock
from semantic_kernel.template_engine.blocks.var_block import VarBlock

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

    def create_kernel_function() -> KernelFunction:
        """Return an KernelFunction."""

        @kernel_function(name="function")
        def my_function(arguments: KernelArguments) -> str:
            return f"F({arguments['input']})"

        return KernelFunction.from_method(
            plugin_name="plugin",
            method=my_function,
        )

    def create_chat_history() -> ChatHistory:
        return ChatHistory()

    cls_obj_map = {
        Block: Block(content="foo"),
        CodeBlock: CodeBlock(content="foo"),
        FunctionIdBlock: FunctionIdBlock(content="foo.bar"),
        TextBlock: TextBlock(content="baz"),
        ValBlock: ValBlock(content="'qux'"),
        VarBlock: VarBlock(content="$quux"),
        NamedArgBlock: NamedArgBlock(content="foo='bar'"),
        # PromptTemplateEngine: PromptTemplateEngine(),
        KernelParameterMetadata: KernelParameterMetadata(
            name="foo",
            description="bar",
            default_value="baz",
            type_="string",
            is_required=True,
            schema_data=KernelParameterMetadata.infer_schema(None, "str", "baz", "bar"),
        ),
        KernelFunctionMetadata: KernelFunctionMetadata(
            name="foo",
            plugin_name="bar",
            description="baz",
            parameters=[
                KernelParameterMetadata(
                    name="qux",
                    description="bar",
                    default_value="baz",
                    type_="str",
                    schema_data=KernelParameterMetadata.infer_schema(None, "str", "baz", "bar"),
                )
            ],
            is_prompt=True,
            is_asynchronous=False,
        ),
        ChatHistory: create_chat_history(),
        NullMemory: NullMemory(),
        KernelFunction: create_kernel_function(),
    }

    def constructor(cls: t.Type[_Serializable]) -> _Serializable:
        """Return a serializable object."""
        return cls_obj_map[cls]

    return constructor


PROTOCOLS = [
    ConversationSummaryPlugin,
    HttpPlugin,
    MathPlugin,
    TextMemoryPlugin,
    TextPlugin,
    TimePlugin,
    WaitPlugin,
    WebSearchEnginePlugin,
]

BASE_CLASSES = [
    SemanticTextMemoryBase,
]

STATELESS_CLASSES = [
    NullMemory,
]

ENUMS = [
    BlockTypes,
]

PYDANTIC_MODELS = [
    Block,
    CodeBlock,
    FunctionIdBlock,
    TextBlock,
    ValBlock,
    VarBlock,
    NamedArgBlock,
    KernelParameterMetadata,
    KernelFunctionMetadata,
    ChatHistory,
]
KERNEL_FUNCTION_OPTIONAL = [KernelFunction]
KERNEL_FUNCTION_REQUIRED = [
    pytest.param(
        KernelFunction,
        marks=pytest.mark.xfail(reason="Need to implement Pickle serialization."),
    )
]


class TestUsageInPydanticFields:
    @pytest.mark.parametrize(
        "kernel_type",
        BASE_CLASSES + PROTOCOLS + ENUMS + PYDANTIC_MODELS + STATELESS_CLASSES + KERNEL_FUNCTION_OPTIONAL,
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

            field: kernel_type | None = None

        assert_serializable(TestModel(), TestModel)

    @pytest.mark.parametrize("kernel_type", PYDANTIC_MODELS + STATELESS_CLASSES + KERNEL_FUNCTION_REQUIRED)
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
