// Copyright (c) Microsoft. All rights reserved.

using Dapr.Actors.Runtime;

namespace SemanticKernel.Process.IntegrationTests;

/// <summary>
/// Implements a health actor.
/// </summary>
public class HealthActor : Actor, IHealthActor
{
    /// <summary>
    /// Initializes a new instance of the <see cref="HealthActor"/> class.
    /// </summary>
    /// <param name="host"></param>
    public HealthActor(ActorHost host) : base(host)
    {
    }

    /// <inheritdoc />
    public Task HealthCheckAsync()
    {
        return Task.CompletedTask;
    }
}
