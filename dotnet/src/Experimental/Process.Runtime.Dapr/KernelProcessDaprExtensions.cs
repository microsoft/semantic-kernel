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
    /// <param name="actorOptions">The instance of <see cref="ActorRuntimeOptions"/></param>
    public static void AddProcessActors(this ActorRuntimeOptions actorOptions)
    {
        // Register actor types and configure actor settings
        actorOptions.Actors.RegisterActor<ProcessActor>();
        actorOptions.Actors.RegisterActor<StepActor>();
        actorOptions.Actors.RegisterActor<MapActor>();
        actorOptions.Actors.RegisterActor<ProxyActor>();
        actorOptions.Actors.RegisterActor<EventBufferActor>();
        actorOptions.Actors.RegisterActor<MessageBufferActor>();
        actorOptions.Actors.RegisterActor<ExternalEventBufferActor>();
        actorOptions.Actors.RegisterActor<ExternalMessageBufferActor>();
    }
}
