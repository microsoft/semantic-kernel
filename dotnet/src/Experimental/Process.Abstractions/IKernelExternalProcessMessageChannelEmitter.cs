// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface that provides a channel for emitting external messages from a step.
/// </summary>
public interface IExternalKernelProcessMessageChannelEmitter
{
    abstract Task EmitExternalEventAsync(string externalTopicEvent, object? eventData);
}
