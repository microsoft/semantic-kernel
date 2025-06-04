// Copyright (c) Microsoft. All rights reserved.

using System;
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
}
