// Copyright (c) Microsoft. All rights reserved.

using Dapr.Actors;

namespace SemanticKernel.Process.IntegrationTests;

/// <summary>
/// An interface for a health actor that is only used for testing the health of the Dapr runtime.
/// </summary>
public interface IHealthActor : IActor
{
    /// <summary>
    /// An empty method used to determine if Dapr runtime is up and reachable.
    /// </summary>
    /// <returns></returns>
    Task HealthCheckAsync();
}
