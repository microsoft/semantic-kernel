﻿// Copyright (c) Microsoft. All rights reserved.

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
    /// <returns>A <see cref="Task{KernelProcessContext}"/></returns>
    public async Task<KernelProcessContext> StartProcessAsync(KernelProcess process, Kernel kernel, KernelProcessEvent initialEvent)
    {
        return await process.StartAsync(kernel, initialEvent);
    }
}
