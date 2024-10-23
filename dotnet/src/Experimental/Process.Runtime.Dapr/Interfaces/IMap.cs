// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;
using Dapr.Actors;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface that represents a step in a process.
/// </summary>
public interface IMap : IActor
{
    /// <summary>
    /// Initializes the step with the provided step information.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    /// <exception cref="KernelException"></exception>
    Task InitializeMapAsync(DaprMapInfo mapInfo, string? parentProcessId);

    /// <summary>
    /// Builds the current state of the step into a <see cref="DaprMapInfo"/>.
    /// </summary>
    /// <returns>An instance of <see cref="DaprMapInfo"/></returns>
    Task<DaprMapInfo> ToDaprMapInfoAsync();
}
