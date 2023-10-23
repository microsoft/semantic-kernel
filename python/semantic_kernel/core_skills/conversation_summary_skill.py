# Copyright (c) Microsoft. All rights reserved.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.orchestration.sk_context import SKContext


class ConversationSummarySkill:
    """
    Semantic skill that enables conversations summarization.
    """

    from semantic_kernel.skill_definition import sk_function

    # The max tokens to process in a single semantic function call.
    _max_tokens = 1024

    _summarize_conversation_prompt_template = (
        "BEGIN CONTENT TO SUMMARIZE:\n{{"
        + "$INPUT"
        + "}}\nEND CONTENT TO SUMMARIZE.\nSummarize the conversation in 'CONTENT TO"
        " SUMMARIZE',            identifying main points of discussion and any"
        " conclusions that were reached.\nDo not incorporate other general"
        " knowledge.\nSummary is in plain text, in complete sentences, with no markup"
        " or tags.\n\nBEGIN SUMMARY:\n"
    )

    def __init__(self, kernel: "Kernel"):
        self._summarizeConversationFunction = kernel.create_semantic_function(
            ConversationSummarySkill._summarize_conversation_prompt_template,
            skill_name=ConversationSummarySkill.__name__,
            description=(
                "Given a section of a conversation transcript, summarize the part of"
                " the conversation."
            ),
            max_tokens=ConversationSummarySkill._max_tokens,
            temperature=0.1,
            top_p=0.5,
        )

    @sk_function(
        description="Given a long conversation transcript, summarize the conversation.",
        name="SummarizeConversation",
        input_description="A long conversation transcript.",
    )
    async def summarize_conversation_async(
        self, input: str, context: "SKContext"
    ) -> "SKContext":
        """
        Given a long conversation transcript, summarize the conversation.

        :param input: A long conversation transcript.
        :param context: The SKContext for function execution.
        :return: SKContext with the summarized conversation result.
        """
        from semantic_kernel.text import text_chunker
        from semantic_kernel.text.function_extension import (
            aggregate_chunked_results_async,
        )

        lines = text_chunker._split_text_lines(
            input, ConversationSummarySkill._max_tokens, True
        )
        paragraphs = text_chunker._split_text_paragraph(
            lines, ConversationSummarySkill._max_tokens
        )

        return await aggregate_chunked_results_async(
            self._summarizeConversationFunction, paragraphs, context
        )
