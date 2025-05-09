// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A class that can run a process locally or in-process.
/// </summary>
public static class LocalKernelProcessFactory
{
    /// <summary>
    /// Starts the specified process.
    /// </summary>
    /// <param name="process">Required: The <see cref="KernelProcess"/> to start running.</param>
    /// <param name="kernel">Required: An instance of <see cref="Kernel"/></param>
    /// <param name="initialEvent">Required: The initial event to start the process.</param>
    /// <param name="externalMessageChannel">Optional: an instance of <see cref="IExternalKernelProcessMessageChannel"/>.</param>
    /// <returns>An instance of <see cref="KernelProcess"/> that can be used to interrogate or stop the running process.</returns>
    public static async Task<LocalKernelProcessContext> StartAsync(this KernelProcess process, Kernel kernel, KernelProcessEvent initialEvent, IExternalKernelProcessMessageChannel? externalMessageChannel = null)
    {
        Verify.NotNull(initialEvent, nameof(initialEvent));

        LocalKernelProcessContext processContext = new(process, kernel, null, externalMessageChannel);
        await processContext.StartWithEventAsync(initialEvent).ConfigureAwait(false);
        return processContext;
    }

    /// <summary>
    /// Starts a specific process using registered processes
    /// </summary>
    /// <param name="kernel">Required: An instance of <see cref="Kernel"/></param>
    /// <param name="registeredProcesses">Required: dictionary with registered processes</param>
    /// <param name="processKey">Required: key of the process in registered processes</param>
    /// <param name="processId">Required: id to be assigined to the running process</param>
    /// <param name="initialEvent">Required: The initial event to start the process.</param>
    /// <param name="externalMessageChannel">Optional: an instance of <see cref="IExternalKernelProcessMessageChannel"/>.</param>
    /// <returns></returns>
    /// <exception cref="ArgumentException"></exception>
    public static async Task<LocalKernelProcessContext> StartAsync(
        Kernel kernel,
        IReadOnlyDictionary<string, KernelProcess> registeredProcesses,
        string processKey,
        string processId,
        KernelProcessEvent initialEvent,
        IExternalKernelProcessMessageChannel? externalMessageChannel = null)
    {
        Verify.NotNullOrWhiteSpace(processKey, nameof(processKey));
        Verify.NotNullOrWhiteSpace(processId, nameof(processId));
        Verify.NotNull(initialEvent, nameof(initialEvent));

        if (!registeredProcesses.TryGetValue(processKey, out KernelProcess? process) || process is null)
        {
            throw new ArgumentException($"The process with key '{processKey}' is not registered.");
        }

        // Assign the process Id if one is provided and the processes does not already have an Id.
        if (!string.IsNullOrWhiteSpace(processId) && string.IsNullOrWhiteSpace(process.State.Id))
        {
            process = process with { State = process.State with { Id = processId, Name = processKey } };
        }

        LocalKernelProcessContext processContext = new(process, kernel, null, externalMessageChannel);
        await processContext.StartWithEventAsync(initialEvent).ConfigureAwait(false);
        return processContext;
    }
}
