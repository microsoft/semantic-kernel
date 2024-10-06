# Copyright (c) Microsoft. All rights reserved.
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< main
>>>>>>> main
>>>>>>> Stashed changes

import logging
from typing import TYPE_CHECKING, Annotated, Any

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_from_prompt import (
    KernelFunctionFromPrompt,
)
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
import sys
from typing import TYPE_CHECKING
>>>>>>> ms/small_fixes

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
    from semantic_kernel.prompt_template.prompt_template_config import (
        PromptTemplateConfig,
    )
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    from semantic_kernel.prompt_template.prompt_template_config import (
        PromptTemplateConfig,
    )
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
<<<<<<< main
    from semantic_kernel.prompt_template.prompt_template_config import (
        PromptTemplateConfig,
    )
=======
    from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

logger = logging.getLogger(__name__)


<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
class ConversationSummaryPlugin:
    """Semantic plugin that enables conversations summarization."""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
class ConversationSummaryPlugin:
    """Semantic plugin that enables conversations summarization."""
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
class ConversationSummaryPlugin:
    """Semantic plugin that enables conversations summarization."""
=======
>>>>>>> Stashed changes
<<<<<<< main
class ConversationSummaryPlugin:
    """Semantic plugin that enables conversations summarization."""
=======
    from semantic_kernel.functions.kernel_function_decorator import kernel_function
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

    # The max tokens to process in a single semantic function call.
    _max_tokens = 1024

    _summarize_conversation_prompt_template = (
        "BEGIN CONTENT TO SUMMARIZE:\n{{"
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        "$input"
        "}}\nEND CONTENT TO SUMMARIZE.\nSummarize the conversation in 'CONTENT TO"
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        "$input"
        "}}\nEND CONTENT TO SUMMARIZE.\nSummarize the conversation in 'CONTENT TO"
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
        "$input"
        "}}\nEND CONTENT TO SUMMARIZE.\nSummarize the conversation in 'CONTENT TO"
=======
>>>>>>> Stashed changes
<<<<<<< main
        "$input"
        "}}\nEND CONTENT TO SUMMARIZE.\nSummarize the conversation in 'CONTENT TO"
=======
        + "$input"
        + "}}\nEND CONTENT TO SUMMARIZE.\nSummarize the conversation in 'CONTENT TO"
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        " SUMMARIZE',            identifying main points of discussion and any"
        " conclusions that were reached.\nDo not incorporate other general"
        " knowledge.\nSummary is in plain text, in complete sentences, with no markup"
        " or tags.\n\nBEGIN SUMMARY:\n"
    )

    def __init__(
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< main
>>>>>>> main
>>>>>>> Stashed changes
        self,
        prompt_template_config: "PromptTemplateConfig",
        return_key: str = "summary",
        **kwargs: Any
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
        prompt_template_config.template = (
            ConversationSummaryPlugin._summarize_conversation_prompt_template
        )
        prompt_template_config.template_format = "semantic-kernel"
        self._summarizeConversationFunction = KernelFunctionFromPrompt(
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
        self, kernel: "Kernel", prompt_template_config: "PromptTemplateConfig", return_key: str = "summary"
    ) -> None:
        """
        Initializes a new instance of the ConversationSummaryPlugin class.

        :param kernel: The kernel instance.
        :param prompt_template_config: The prompt template configuration.
        :param return_key: The key to use for the return value.
        """
        self.return_key = return_key
        self._summarizeConversationFunction = kernel.create_function_from_prompt(
            ConversationSummaryPlugin._summarize_conversation_prompt_template,
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< main
>>>>>>> main
>>>>>>> Stashed changes
        "KernelArguments",
        "KernelArguments with the summarized conversation result in key self.return_key.",
    ]:
        """Given a long conversation transcript, summarize the conversation.

        Args:
            input (str): A long conversation transcript.
            kernel (Kernel): The kernel for function execution.
            arguments (KernelArguments): Arguments used by the kernel.

        Returns:
            KernelArguments with the summarized conversation result in key self.return_key.
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
        "KernelArguments", "KernelArguments with the summarized conversation result in key self.return_key."
    ]:
        """
        Given a long conversation transcript, summarize the conversation.

        :param input: A long conversation transcript.
        :param kernel: The kernel for function execution.
        :param arguments: Arguments used by the kernel.
        :return: KernelArguments with the summarized conversation result in key self.return_key.
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        """
        from semantic_kernel.text import text_chunker
        from semantic_kernel.text.function_extension import aggregate_chunked_results

        lines = text_chunker._split_text_lines(
            input, ConversationSummaryPlugin._max_tokens, True
        )
        paragraphs = text_chunker._split_text_paragraph(
            lines, ConversationSummaryPlugin._max_tokens
        )

        arguments[self.return_key] = await aggregate_chunked_results(
            self._summarizeConversationFunction, paragraphs, kernel, arguments
        )
        return arguments
