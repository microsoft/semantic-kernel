# Copyright (c) Microsoft. All rights reserved.

from typing import List

import core_skills.constants as constants
from orchestration.sk_context import SKContext
from skill_definition.sk_function_decorator import sk_function

import semantic_kernel as sk
from python.semantic_kernel.kernel_base import KernelBase
from python.semantic_kernel.orchestration.sk_function_base import SKFunctionBase


class ConversationSummarySkill:
    MAX_TOKENS = 1024

    _conversationActionItemsFunction: SKFunctionBase
    _conversationTopicsFunction: SKFunctionBase
    _summarizeConversationFunction: SKFunctionBase

    def __init__(self, kernel: KernelBase) -> None:
        self._conversation_action_items_function = sk.extensions.create_semantic_function(
            kernel=kernel,
            prompt_template=constants.GET_CONVERSATION_ACTION_ITEMS_DEFINITION,
            skill_name=type(self).__name__,
            description="Given a section of a conversation transcript, identify action items.",
            max_tokens=self.MAX_TOKENS,
            temperature=0.1,
            top_p=0.5,
        )

        self._conversation_topics_function = sk.extensions.create_semantic_function(
            kernel=kernel,
            prompt_template=constants.GET_CONVERSATION_TOPICS_DEFINITION,
            skill_name=type(self).__name__,
            description="Analyze a conversation transcript and extract key topics worth remembering.",
            max_tokens=self.MAX_TOKENS,
            temperature=0.1,
            top_p=0.5,
        )

        self._summarize_conversation_function = sk.extensions.create_semantic_function(
            kernel=kernel,
            prompt_template=constants.GET_CONVERSATION_SUMMARY_DEFINITION,
            skill_name=type(self).__name__,
            description="Given a section of a conversation transcript, summarize the part of the conversation.",
            max_tokens=self.MAX_TOKENS,
            temperature=0.1,
            top_p=0.5,
        )

    @sk_function(
        description="Given a long conversation transcript, identify action items.",
        name="getConversationActionItemsAsync",
        input_description="A long conversation transcript.",
    )
    async def get_conversation_action_items_async(
        self, input: str, context: SKContext
    ) -> SKContext:
        """
        Given a long conversation transcript, identify action items.

        Args:
            input -- A long conversation transcript.
            context -- The SKContext for function execution.
        """
        pass
        # TODO: Uncomment the following code when the semantic_text_partitioner is implemented.
        # paragraphs = self._split_paragraphs(input)

        # TODO: Uncomment the following code when aggregate_partitioned_results is implemented.
        # return await self._conversation_action_items_function.aggregate_partitioned_results_async(paragraphs, context)

    @sk_function(
        description="Given a long conversation topic, identify topics worth remembering.",
        name="getConversationTopicsAsync",
        input_description="A long conversation transcript.",
    )
    async def get_conversation_topics_async(
        self, input: str, context: SKContext
    ) -> SKContext:
        """
        Given a long conversation transcript, identify topics worth remembering.

        Args:
            input -- A long conversation transcript.
            context -- The SKContext for function execution.
        """
        pass
        # TODO: Uncomment the following code when the semantic_text_partitioner is implemented.
        # paragraphs = self._split_paragraphs(input)

        # TODO: Uncomment the following code when aggregate_partitioned_results is implemented.
        # return await self._conversation_topics_function.aggregate_partitioned_results_async(paragraphs, context)

    @sk_function(
        description="Given a long conversation transcript, summarize the conversation.",
        name="summarizeConversationAsync",
        input_description="A long conversation transcript.",
    )
    async def summarize_conversation_async(
        self, input: str, context: SKContext
    ) -> SKContext:
        """
        Given a long conversation transcript, summarize the conversation.

        Args:
            input -- A long conversation transcript.
            context -- The SKContext for function execution.
        """
        pass
        # TODO: Uncomment the following code when the semantic_text_partitioner is implemented.
        # paragraphs = self._split_paragraphs(input)

        # TODO: Uncomment the following code when aggregate_partitioned_results is implemented.
        # return await self._summarize_conversation_function.aggregate_partitioned_results(paragraphs, context)

    def _split_paragraphs(self, input: str) -> List[str]:
        pass
        # TODO: Uncomment the following code when the semantic_text_partitioner is implemented.
        # lines = semantic_text_partitioner.split_plain_text_lines(input, self.MAX_TOKENS)
        # return semantic_text_partitioner.split_plain_text_paragraphs(lines, self.MAX_TOKENS)
