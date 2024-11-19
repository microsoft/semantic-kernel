// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// State keys utilized by DAPR actor classes.
/// </summary>
internal static class ActorStateKeys
{
    // Shared Actor keys
    public const string StepParentProcessId = "parentProcessId";

    // StepActor keys
    public const string StepInfoState = nameof(DaprStepInfo);
    public const string StepStateJson = "kernelStepStateJson";
    public const string StepStateType = "kernelStepStateType";
    public const string StepIncomingMessagesState = "incomingMessagesState";

    // MapActor keys
    public const string MapInfoState = nameof(DaprMapInfo);

    // ProcessActor keys
    public const string ProcessInfoState = nameof(DaprProcessInfo);
    public const string EventProxyStepId = "processEventProxyId";
    public const string StepActivatedState = "kernelStepActivated";

    // MessageBufferActor keys
    public const string MessageQueueState = "DaprMessageBufferState";

    // ExternalEventBufferActor keys
    public const string ExternalEventQueueState = "DaprExternalEventBufferState";

    // EventBufferActor keys
    public const string EventQueueState = "DaprEventBufferState";
}
