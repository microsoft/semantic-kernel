// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;
using Dapr.Actors;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface that represents an agent step in a process.
/// </summary>
public interface IAgentStep : IActor
{
    /// <summary>
    /// Initializes the step with the provided step information.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    /// <exception cref="KernelException"></exception>
    Task InitializeAgentStepAsync(DaprAgentStepInfo stepInfo, string? parentProcessId);
}
