# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING

from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import Agent
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


@experimental_class
class AgentChannel(ABC):
    """Defines the communication protocol for a particular Agent type.

    An agent provides it own AgentChannel via CreateChannel.
    """

    # My Experiments

    This is a markdown file where I document my experiments.

    ## Experiment 1: Example Experiment

    ### Objective
    Describe the objective of the experiment.

    ### Method
    Outline the steps taken to perform the experiment.

    ### Results
    Document the results of the experiment.

    ### Conclusion
    Summarize the findings and conclusions drawn from the experiment.

    @abstractmethod
    async def receive(
        self,
        history: list["ChatMessageContent"],
    ) -> None:
        """Receive the conversation messages.

        Used when joining a conversation and also during each agent interaction.

        Args:
            history: The history of messages in the conversation.
        """
        ...

    @abstractmethod
    def invoke(
        self,
        agent: "Agent",
    ) -> AsyncIterable[tuple[bool, "ChatMessageContent"]]:
        """Perform a discrete incremental interaction between a single Agent and AgentChat.

        Args:
            agent: The agent to interact with.

        Returns:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            A async iterable of a bool, ChatMessageContent.
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
            A async iterable of a bool, ChatMessageContent.
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
            A async iterable of a bool, ChatMessageContent.
=======
>>>>>>> Stashed changes
            An async iterable of a bool, ChatMessageContent.
        """
        ...

    @abstractmethod
    def invoke_stream(
        self,
        agent: "Agent",
        history: "list[ChatMessageContent]",
    ) -> AsyncIterable["ChatMessageContent"]:
        """Perform a discrete incremental stream interaction between a single Agent and AgentChat.

        Args:
            agent: The agent to interact with.
            history: The history of messages in the conversation.

        Returns:
            An async iterable ChatMessageContent.
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
        ...

    @abstractmethod
    def get_history(
        self,
    ) -> AsyncIterable["ChatMessageContent"]:
        """Retrieve the message history specific to this channel.

        Returns:
            An async iterable of ChatMessageContent.
        """
        ...

    @abstractmethod
    async def reset(self) -> None:
        """Reset any persistent state associated with the channel."""
        ...


