// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface that provides a channel for emitting external messages from a step.
/// In addition provide common methods like initialization and Uninitialization
/// </summary>
public interface IExternalKernelProcessMessageChannel : IExternalKernelProcessMessageChannelEmitter
{
    /// <summary>
    /// Initialization of the external messaging channel used
    /// </summary>
    /// <returns>A <see cref="ValueTask"/></returns>
    public abstract ValueTask Initialize();

    /// <summary>
    /// Uninitialization of the external messaging channel used
    /// </summary>
    /// <returns>A <see cref="ValueTask"/></returns>
    public abstract ValueTask Uninitialize();
}
