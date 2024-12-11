// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Process.Interfaces;
public interface IDaprPubsubEventInfo
{
    /// <summary>
    /// Gets the string of the event name that the function is linked to
    /// </summary>
    string EventName { get; }

    /// <summary>
    /// When using Dapr Runtime, pubsub name is required to know where to send the specific Dapr event
    /// </summary>
    string? DaprPubsub { get; }

    /// <summary>
    /// When using Dapr runtime, If daprTopic provided topic will be used instead of eventName, if not provided default will be eventName
    /// </summary>
    public string? DaprTopic { get; }
}
