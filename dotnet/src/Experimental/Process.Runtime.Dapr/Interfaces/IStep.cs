// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Dapr.Actors;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface that represents a step in a process.
/// </summary>
public interface IStep : IActor
{
    /// <summary>
    /// Initializes the step with the provided step information.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    /// <exception cref="KernelException"></exception>
    Task InitializeStepAsync(string processId, string stepId, string? parentProcessId, string? eventProxyStepId);

    /// <summary>
    /// Triggers the step to dequeue all pending messages and prepare for processing.
    /// </summary>
    /// <returns>A <see cref="Task{Task}"/> where T is an <see cref="int"/> indicating the number of messages that are prepared for processing.</returns>
    Task<int> PrepareIncomingMessagesAsync();

    /// <summary>
    /// Triggers the step to process all prepared messages.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    Task ProcessIncomingMessagesAsync();

    /// <summary>
    /// Builds the current state of the step into a <see cref="DaprStepInfo"/>.
    /// </summary>
    /// <returns>An instance of <see cref="DaprStepInfo"/></returns>
    Task<IDictionary<string, KernelProcessStepState>> GetStepStateAsync();
}
