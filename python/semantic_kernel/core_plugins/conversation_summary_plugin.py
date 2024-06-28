# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Annotated, Any

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

logger = logging.getLogger(__name__)


class ConversationSummaryPlugin:
    """Semantic plugin that enables conversations summarization."""

    # The max tokens to process in a single semantic function call.
    _max_tokens = 1024

    _summarize_conversation_prompt_template = (
        "BEGIN CONTENT TO SUMMARIZE:\n{{"
        "$input"
        "}}\nEND CONTENT TO SUMMARIZE.\nSummarize the conversation in 'CONTENT TO"
        " SUMMARIZE',            identifying main points of discussion and any"
        " conclusions that were reached.\nDo not incorporate other general"
        " knowledge.\nSummary is in plain text, in complete sentences, with no markup"
        " or tags.\n\nBEGIN SUMMARY:\n"
    )

    def __init__(
        self, prompt_template_config: "PromptTemplateConfig", return_key: str = "summary", **kwargs: Any
    ) -> None:
        """Initializes a new instance of the ConversationSummaryPlugin.

        The template for this plugin is built-in, and will overwrite any template passed in the prompt_template_config.

        Args:
            prompt_template_config (PromptTemplateConfig): The prompt template configuration.
            return_key (str): The key to use for the return value.
            **kwargs: Additional keyword arguments, not used only for compatibility.

        """
        if "kernel" in kwargs:
            logger.warning(
                "The kernel parameter is not used in the ConversationSummaryPlugin constructor anymore."
                "Please make sure to remove and to add the created plugin to the kernel, by using:"
                "kernel.add_plugin(conversation_plugin, 'summarizer')"
            )

        self.return_key = return_key
        prompt_template_config.template = ConversationSummaryPlugin._summarize_conversation_prompt_template
        prompt_template_config.template_format = "semantic-kernel"
        self._summarizeConversationFunction = KernelFunctionFromPrompt(
            plugin_name=ConversationSummaryPlugin.__name__,
            function_name="SummarizeConversation",
            prompt_template_config=prompt_template_config,
        )

    @kernel_function(
        description="Given a long conversation transcript, summarize the conversation.",
        name="SummarizeConversation",
    )
    async def summarize_conversation(
        self,
        input: Annotated[str, "A long conversation transcript."],
        kernel: Annotated["Kernel", "The kernel instance."],
        arguments: Annotated["KernelArguments", "Arguments used by the kernel."],
    ) -> Annotated[
        "KernelArguments", "KernelArguments with the summarized conversation result in key self.return_key."
    ]:
        """Given a long conversation transcript, summarize the conversation.

        Args:
            input (str): A long conversation transcript.
            kernel (Kernel): The kernel for function execution.
            arguments (KernelArguments): Arguments used by the kernel.

        Returns:
            KernelArguments with the summarized conversation result in key self.return_key.
        """
        from semantic_kernel.text import text_chunker
        from semantic_kernel.text.function_extension import aggregate_chunked_results

        lines = text_chunker._split_text_lines(input, ConversationSummaryPlugin._max_tokens, True)
        paragraphs = text_chunker._split_text_paragraph(lines, ConversationSummaryPlugin._max_tokens)

        arguments[self.return_key] = await aggregate_chunked_results(
            self._summarizeConversationFunction, paragraphs, kernel, arguments
        )
        return arguments
