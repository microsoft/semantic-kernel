﻿// Copyright (c) Microsoft. All rights reserved.
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
}
