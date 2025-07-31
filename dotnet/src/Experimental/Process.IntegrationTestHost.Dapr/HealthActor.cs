// Copyright (c) Microsoft. All rights reserved.

using Dapr.Actors.Runtime;

namespace Microsoft.SemanticKernel.Process.IntegrationTests;

/// <summary>
/// An implementation of the health actor that is only used for testing the health of the Dapr runtime.
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
