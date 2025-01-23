// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface that provides a channel for emitting messages from a step.
/// </summary>
public interface IKernelExternalMessageChannel
{
    public abstract ValueTask EmitExternalEventAsync(string eventTopic, object? eventData = null);
    public abstract ValueTask SubscribeToExternalEventAsync(string eventTopic);
    public abstract ValueTask UnsubscribeToExternalEventAsync(string eventTopic);
}
