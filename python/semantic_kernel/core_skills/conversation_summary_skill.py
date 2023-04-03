# Copyright (c) Microsoft. All rights reserved.

from python.semantic_kernel.core_skills.semantic_function_constants import SemanticFunctionConstants
from python.semantic_kernel.kernel_base import KernelBase
from python.semantic_kernel.orchestration.sk_function_base import SKFunctionBase

import semantic_kernel as sk

class ConversationSummarySkill:
    MAX_TOKENS = 1024
    
    _conversationActionItemsFunction: SKFunctionBase
    _conversationTopicsFunction: SKFunctionBase
    _summarizeConversationFunction: SKFunctionBase
    
    def __init__(self, kernel: KernelBase) -> None:
        self._conversation_action_items_function = sk.extensions.create_semantic_function(
            kernel=kernel,
            prompt_template=SemanticFunctionConstants.GET_CONVERSATION_ACTION_ITEMS_DEFINITION,
            skill_name=type(self).__name__,
            description="Given a section of a conversation transcript, identify action items.",
            max_tokens=self.MAX_TOKENS,
            temperature=0.1,
            top_p=0.5
        )
        
        self._conversation_topics_function = sk.extensions.create_semantic_function(
            kernel=kernel,
            prompt_template=SemanticFunctionConstants.GET_CONVERSATION_TOPICS_DEFINITION,
            skill_name=type(self).__name__,
            description="Analyze a conversation transcript and extract key topics worth remembering.",
            max_tokens=self.MAX_TOKENS,
            temperature=0.1,
            top_p=0.5
        )

        self._summarize_conversation_function = sk.extensions.create_semantic_function(
            kernel=kernel,
            prompt_template=SemanticFunctionConstants.GET_CONVERSATION_SUMMARY_DEFINITION,
            skill_name=type(self).__name__,
            description="Given a section of a conversation transcript, summarize the part of the conversation.",
            max_tokens=self.MAX_TOKENS,
            temperature=0.1,
            top_p=0.5
        )

    # TODO: GetConversationActionItemsAsync(...)

    # TODO: GetConversationTopicsAsync(...)

    # TODO: SummarizeConversationAsync(...)

    

