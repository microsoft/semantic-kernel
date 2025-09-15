// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Dapr.Actors;

namespace Microsoft.SemanticKernel;

// estenori-note:
// for some reason dapr doesn't like if instead public interface IExternalMessageBuffer : IActor, IExternalKernelProcessMessageChannelBase
// instead defining the interface component is necessary. To make it compatible with shared components a "casting" to IExternalKernelProcessMessageChannelEmitter
// is added in StepActor logic to make use of FindInputChannels

/// <summary>
/// An interface for <see cref="IExternalKernelProcessMessageChannel"/>
/// </summary>
public interface IExternalMessageBuffer : IActor
{
    /// <summary>
    /// Emits external events outside of the SK process
    /// </summary>
    /// <param name="externalTopicEvent"></param>
    /// <param name="eventData"></param>
    /// <returns></returns>
    abstract Task EmitExternalEventAsync(string externalTopicEvent, KernelProcessProxyMessage eventData);
}
