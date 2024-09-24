// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process;

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
    /// <returns>An instance of <see cref="KernelProcess"/> that can be used to interogate or stop the running process.</returns>
    public static Task<LocalKernelProcessContext> StartAsync(this KernelProcess process, Kernel kernel, KernelProcessEvent initialEvent)
    {
        var processContext = new LocalKernelProcessContext(process, kernel);
        processContext.Start(initialEvent);
        return Task.FromResult(processContext);
    }
}
