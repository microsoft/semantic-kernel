# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.agents.runtime.core.topic import TopicId
from semantic_kernel.agents.runtime.in_process.message_handler_context import MessageHandlerContext
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class DefaultTopicId(TopicId):
    """DefaultTopicId provides a sensible default for the topic_id and source fields of a TopicId.

    If created in the context of a message handler, the source will be set to the agent_id of the message handler,
    otherwise it will be set to "default".

    Args:
        type (str, optional): Topic type to publish message to. Defaults to "default".
        source (str | None, optional): Topic source to publish message to. If None, the source will be set to the
            agent_id of the message handler if in the context of a message handler, otherwise it will be set to
            "default". Defaults to None.
    """

    def __init__(self, type: str = "default", source: str | None = None) -> None:
        """Initialize the DefaultTopicId."""
        if source is None:
            try:
                source = MessageHandlerContext.agent_id().key
            # If we aren't in the context of a message handler, we use the default source
            except RuntimeError:
                source = "default"

        super().__init__(type, source)
