// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Process.IntegrationTests;

/// <summary>
/// A test fixture for running shared process tests across multiple runtimes.
/// </summary>
public abstract class ProcessTestFixture
{
    /// <summary>
    /// Starts a process.
    /// </summary>
    /// <param name="process">The process to start.</param>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    /// <param name="initialEvent">An optional initial event.</param>
    /// <param name="externalMessageChannel">channel used for external messages</param>
    /// <param name="runId">An optional run Id.</param>
    /// <returns>A <see cref="Task{KernelProcessContext}"/></returns>
    public abstract Task<KernelProcessContext> StartProcessAsync(KernelProcess process, Kernel kernel, KernelProcessEvent initialEvent, IExternalKernelProcessMessageChannel? externalMessageChannel = null, string? runId = null);

    /// <summary>
    /// Starts the specified process.
    /// </summary>
    /// <param name="key"></param>
    /// <param name="processId"></param>
    /// <param name="initialEvent"></param>
    /// <returns></returns>
    public abstract Task<KernelProcessContext> StartAsync(string key, string processId, KernelProcessEvent initialEvent);
}
