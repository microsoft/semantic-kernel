// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;

namespace SemanticKernel.Process.IntegrationTests;

/// <summary>
/// A test fixture for running shared process tests across multiple runtimes.
/// </summary>
public class ProcessTestFixture
{
    /// <summary>
    /// Starts a process.
    /// </summary>
    /// <param name="process">The process to start.</param>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    /// <param name="initialEvent">An optional initial event.</param>
    /// <param name="externalMessageChannel">channel used for external messages</param>
    /// <returns>A <see cref="Task{KernelProcessContext}"/></returns>
    public async Task<KernelProcessContext> StartProcessAsync(KernelProcess process, Kernel kernel, KernelProcessEvent initialEvent, IExternalKernelProcessMessageChannel? externalMessageChannel = null)
    {
        return await process.StartAsync(kernel, initialEvent, externalMessageChannel);
    }

    /// <summary>
    /// Starts the specified process.
    /// </summary>
    /// <param name="key"></param>
    /// <param name="processId"></param>
    /// <param name="initialEvent"></param>
    /// <returns></returns>
    public Task<KernelProcessContext> StartAsync(string key, string processId, KernelProcessEvent initialEvent)
    {
        throw new NotImplementedException("This method is not implemented in this test fixture.");
    }
}
