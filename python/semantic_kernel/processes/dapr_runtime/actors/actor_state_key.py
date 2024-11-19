# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class ActorStateKeys(Enum):
    """Keys used to store actor state in Dapr."""

    # StepActor Keys
    StepParentProcessId = "parentProcessId"
    StepInfoState = "DaprStepInfo"
    StepStateJson = "kernelStepStateJson"
    StepStateType = "kernelStepStateType"
    StepIncomingMessagesState = "incomingMessagesState"

    # ProcessActor Keys
    ProcessInfoState = "DaprProcessInfo"
    StepActivatedState = "kernelStepActivated"

    # MessageBufferActor Keys
    MessageQueueState = "DaprMessageBufferState"

    # ExternalEventBufferActor Keys
    ExternalEventQueueState = "DaprExternalEventBufferState"

    # EventBufferActor Keys
    EventQueueState = "DaprEventBufferState"
