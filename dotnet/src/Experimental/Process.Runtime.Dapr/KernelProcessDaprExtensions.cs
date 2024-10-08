// Copyright (c) Microsoft. All rights reserved.

using Dapr.Actors.Runtime;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for configuring Dapr actors for the process runtime.
/// </summary>
public static class KernelProcessDaprExtensions
{
    /// <summary>
    /// Adds the process runtime actors to the actor runtime options.
    /// </summary>
    /// <param name="actorOptions"></param>
    public static void AddProcessActors(this ActorRuntimeOptions actorOptions)
    {
        // Register actor types and configure actor settings
        actorOptions.Actors.RegisterActor<Microsoft.SemanticKernel.ProcessActor>();
        actorOptions.Actors.RegisterActor<Microsoft.SemanticKernel.StepActor>();
        actorOptions.Actors.RegisterActor<Microsoft.SemanticKernel.EventQueueActor>();
        actorOptions.Actors.RegisterActor<Microsoft.SemanticKernel.MessageQueueActor>();
        actorOptions.Actors.RegisterActor<Microsoft.SemanticKernel.ExternalEventQueueActor>();

        // actorOptions.ReentrancyConfig = new Dapr.Actors.ActorReentrancyConfig()
        // {
        //     Enabled = true,
        //     MaxStackDepth = 32
        // };
    }
}
