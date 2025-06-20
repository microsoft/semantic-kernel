// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Dapr.Actors.Client;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A factory for creating and starting Dapr kernel processes.
/// </summary>
public class DaprKernelProcessFactory
{
    private readonly IReadOnlyDictionary<string, KernelProcess> _registeredProcesses;

    /// <summary>
    /// Creates a new instance of the <see cref="DaprKernelProcessFactory"/> class.
    /// </summary>
    /// <param name="registeredProcesses"></param>
    public DaprKernelProcessFactory(IReadOnlyDictionary<string, KernelProcess> registeredProcesses)
    {
        Verify.NotNull(registeredProcesses, nameof(registeredProcesses));

        this._registeredProcesses = registeredProcesses;
    }

    /// <summary>
    /// Starts the specified process.
    /// </summary>
    /// <param name="key">The registration key for the process to be run.</param>
    /// <param name="processId">The Id of the process run.</param>
    /// <param name="initialEvent">The initial event.</param>
    /// <param name="actorProxyFactory">An instance of <see cref="IActorProxyFactory"/></param>
    /// <returns></returns>
    public async Task<DaprKernelProcessContext> StartAsync(string key, string processId, KernelProcessEvent initialEvent, IActorProxyFactory? actorProxyFactory = null)
    {
        Verify.NotNullOrWhiteSpace(key, nameof(key));
        Verify.NotNullOrWhiteSpace(processId, nameof(processId));

        if (!this._registeredProcesses.TryGetValue(key, out KernelProcess? process) || process is null)
        {
            throw new ArgumentException($"The process with key '{key}' is not registered.", nameof(key));
        }

        // Assign the process Id if one is provided and the processes does not already have an Id.
        if (!string.IsNullOrWhiteSpace(processId) && string.IsNullOrWhiteSpace(process.State.RunId))
        {
            process = process with { State = process.State with { RunId = processId } };
        }

        DaprKernelProcessContext processContext = new(process, actorProxyFactory);
        await processContext.KeyedStartWithEventAsync(key, processId, initialEvent).ConfigureAwait(false);
        return processContext;
    }
}
