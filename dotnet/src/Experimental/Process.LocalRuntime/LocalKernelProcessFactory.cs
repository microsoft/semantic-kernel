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
    /// <param name="processId">Optional: id to be assigined to the running process, if null it will be assigned during runtime</param>
    /// <param name="externalMessageChannel">Optional: an instance of <see cref="IExternalKernelProcessMessageChannel"/>.</param>
    /// <param name="storageConnector">Optional: an instance of <see cref="IProcessStorageConnector"/>.</param>
    /// <returns>An instance of <see cref="KernelProcess"/> that can be used to interrogate or stop the running process.</returns>
    public static async Task<LocalKernelProcessContext> StartAsync(
        this KernelProcess process,
        Kernel kernel,
        KernelProcessEvent initialEvent,
        string? processId = null,
        IExternalKernelProcessMessageChannel? externalMessageChannel = null,
        IProcessStorageConnector? storageConnector = null)
    {
        Verify.NotNull(initialEvent, nameof(initialEvent));

        LocalKernelProcessContext processContext = new(process, kernel, null, externalMessageChannel, storageConnector, instanceId: processId);
        await processContext.StartWithEventAsync(initialEvent).ConfigureAwait(false);
        return processContext;
    }

    public static async Task<LocalKernelProcessContext> CreateContextAsync(
        this KernelProcess process,
        Kernel kernel,
        //KernelProcessEvent initialEvent,
        string? processId = null,
        IExternalKernelProcessMessageChannel? externalMessageChannel = null,
        IProcessStorageConnector? storageConnector = null)
    {
        //Verify.NotNull(initialEvent, nameof(initialEvent));

        LocalKernelProcessContext processContext = new(process, kernel, null, externalMessageChannel, storageConnector, instanceId: processId);
        //await processContext.StartWithEventKeepRunning(initialEvent).ConfigureAwait(false);

        return processContext;
    }

    /// <summary>
    /// Starts the specified process and runs it to completion.
    /// </summary>
    /// <param name="process"></param>
    /// <param name="kernel"></param>
    /// <param name="initialEvent"></param>
    /// <param name="timeout"></param>
    /// <param name="externalMessageChannel"></param>
    /// <returns></returns>
    public static async Task<LocalKernelProcessContext> RunToEndAsync(this KernelProcess process, Kernel kernel, KernelProcessEvent initialEvent, TimeSpan? timeout = null, IExternalKernelProcessMessageChannel? externalMessageChannel = null)
    {
        Verify.NotNull(initialEvent, nameof(initialEvent));
        TimeSpan timeoutValue = timeout ?? TimeSpan.FromSeconds(60);

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
    /// <param name="processId">Required: id to be assigined to the running process, if null it will be assigned during runtime</param>
    /// <param name="initialEvent">Required: The initial event to start the process.</param>
    /// <param name="externalMessageChannel">Optional: an instance of <see cref="IExternalKernelProcessMessageChannel"/>.</param>
    /// <param name="storageConnector">Optional: an instance of <see cref="IProcessStorageConnector"/>.</param>
    /// <returns></returns>
    /// <exception cref="ArgumentException"></exception>
    public static async Task<LocalKernelProcessContext> StartAsync(
        Kernel kernel,
        IReadOnlyDictionary<string, KernelProcess> registeredProcesses,
        string processKey,
        string? processId,
        KernelProcessEvent initialEvent,
        IExternalKernelProcessMessageChannel? externalMessageChannel = null,
        IProcessStorageConnector? storageConnector = null)
    {
        Verify.NotNullOrWhiteSpace(processKey, nameof(processKey));
        Verify.NotNullOrWhiteSpace(processId, nameof(processId));
        Verify.NotNull(initialEvent, nameof(initialEvent));

        if (!registeredProcesses.TryGetValue(processKey, out KernelProcess? process) || process is null)
        {
            throw new ArgumentException($"The process with key '{processKey}' is not registered.");
        }

        if (string.IsNullOrWhiteSpace(process.State.StepId))
        {
            process = process with { State = process.State with { StepId = processKey } };
        }

        LocalKernelProcessContext processContext = new(process, kernel, null, externalMessageChannel, storageConnector, processId);
        await processContext.StartWithEventAsync(initialEvent).ConfigureAwait(false);
        return processContext;
    }
}
