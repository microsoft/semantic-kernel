// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Dapr.Actors.Client;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// A factory for creating and starting Dapr kernel processes.
/// </summary>
public class DaprKernelProcessFactory2
{
    private readonly IReadOnlyDictionary<string, KernelProcess> _registeredProcesses;

    /// <summary>
    /// Creates a new instance of the <see cref="DaprKernelProcessFactory2"/> class.
    /// </summary>
    /// <param name="registeredProcesses"></param>
    public DaprKernelProcessFactory2(IReadOnlyDictionary<string, KernelProcess> registeredProcesses)
    {
        Verify.NotNull(registeredProcesses, nameof(registeredProcesses));

        this._registeredProcesses = registeredProcesses;
    }

    /// <summary>
    /// Starts the specified process.
    /// </summary>
    /// <param name="key"></param>
    /// <param name="processId"></param>
    /// <param name="initialEvent"></param>
    /// <param name="actorProxyFactory"></param>
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
        if (!string.IsNullOrWhiteSpace(processId) && string.IsNullOrWhiteSpace(process.State.Id))
        {
            process = process with { State = process.State with { Id = processId } };
        }

        DaprKernelProcessContext processContext = new(process, actorProxyFactory);
        await processContext.KeyedStartWithEventAsync(key, processId, initialEvent).ConfigureAwait(false);
        return processContext;
    }
}
