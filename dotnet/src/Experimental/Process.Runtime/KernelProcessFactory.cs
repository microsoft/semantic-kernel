// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.AutoGen.Contracts;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A class that can run a process locally or in-process.
/// </summary>
public static class KernelProcessFactory
{
    /// <summary>
    /// Starts the specified process.
    /// </summary>
    /// <param name="process">Required: The <see cref="KernelProcess"/> to start running.</param>
    /// <param name="kernel">Required: An instance of <see cref="Kernel"/></param>
    /// <param name="runtime">%%%</param>
    /// <param name="initialEvent">Required: The initial event to start the process.</param>
    /// <param name="externalMessageChannel">Optional: an instance of <see cref="IExternalKernelProcessMessageChannel"/>.</param>
    /// <returns>An instance of <see cref="KernelProcess"/> that can be used to interrogate or stop the running process.</returns>
    public static async Task<KernelProcessContext> StartAsync(
        this KernelProcess process,
        Kernel kernel,
        IAgentRuntime runtime,
        KernelProcessEvent initialEvent,
        IExternalKernelProcessMessageChannel? externalMessageChannel = null)
    {
        Verify.NotNull(initialEvent, nameof(initialEvent));

        KernelProcessContext processContext = new(process, kernel, runtime, null, externalMessageChannel);
        await processContext.StartWithEventAsync(initialEvent).ConfigureAwait(false);
        return processContext;
    }
}
