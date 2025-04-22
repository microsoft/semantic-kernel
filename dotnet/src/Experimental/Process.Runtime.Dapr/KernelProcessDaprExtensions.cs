// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Dapr.Actors.Runtime;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Process;

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

    /// <summary>
    /// Adds the Dapr process runtime to the service collection.
    /// </summary>
    /// <param name="sc"></param>
    public static void AddDaprKernelProcesses(this IServiceCollection sc)
    {
        RegisterKeyedProcesses(sc);
    }

    /// <summary>
    /// Registers the keyed processes in the service collection.
    /// </summary>
    /// <param name="sc"></param>
    private static void RegisterKeyedProcesses(this IServiceCollection sc)
    {
        // KeyedServiceCache caches all the keys of a given type for a
        // specific service type. By making it a singleton we only have
        // determine the keys once, which makes resolving the dict very fast.
        sc.AddSingleton<KeyedProcesses>();

        // KeyedServiceCache depends on the IServiceCollection to get
        // the list of keys. That's why we register that here as well, as it
        // is not registered by default in MS.DI.
        sc.AddSingleton(sc);

        // For completeness, let's also allow IReadOnlyDictionary to be resolved.
        sc.AddTransient<IReadOnlyDictionary<string, KernelProcess>, KeyedServiceDictionary>();
    }
}
