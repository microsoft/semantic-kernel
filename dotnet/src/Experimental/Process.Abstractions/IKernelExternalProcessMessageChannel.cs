// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface that provides a channel for emitting external messages from a step.
/// In addition provide common methods like initialization and Uninitialization
/// </summary>
public interface IExternalKernelProcessMessageChannel
{
    /// <summary>
    /// Initialization of the external messaging channel used
    /// </summary>
    /// <returns>A <see cref="ValueTask"/></returns>
    abstract ValueTask Initialize();

    /// <summary>
    /// Uninitialization of the external messaging channel used
    /// </summary>
    /// <returns>A <see cref="ValueTask"/></returns>
    abstract ValueTask Uninitialize();

    /// <summary>
    /// Emits the specified event from the step outside the SK process
    /// </summary>
    /// <param name="externalTopicEvent">name of the topic to be used externally as the event name</param>
    /// <param name="message">data to be transmitted externally</param>
    /// <returns></returns>
    abstract Task EmitExternalEventAsync(string externalTopicEvent, KernelProcessProxyMessage message);
}
