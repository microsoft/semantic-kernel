// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;
/// <summary>
/// A class that can run a process locally or in-process.
/// </summary>
public static class DaprKernelProcessFactory
{
    /// <summary>
    /// Starts the specified process.
    /// </summary>
    /// <param name="process">Required: The <see cref="KernelProcess"/> to start running.</param>
    /// <param name="kernel">Required: An instance of <see cref="Kernel"/></param>
    /// <param name="initialEvent">Required: The initial event to start the process.</param>
    /// <param name="processId">Optional: Used to specify the unique Id of the process. If the process already has an Id, it will not be overwritten and this parameter has no effect.</param>
    /// <returns>An instance of <see cref="KernelProcess"/> that can be used to interrogate or stop the running process.</returns>
    public static async Task<DaprKernelProcessContext> StartAsync(this KernelProcess process, Kernel kernel, KernelProcessEvent initialEvent, string? processId = null)
    {
        Verify.NotNull(process);
        Verify.NotNullOrWhiteSpace(process.State?.Name);
        Verify.NotNull(kernel);
        Verify.NotNull(initialEvent);

        // Assign the process Id if one is provided and the processes does not already have an Id.
        if (!string.IsNullOrWhiteSpace(processId) && string.IsNullOrWhiteSpace(process.State.Id))
        {
            process = process with { State = process.State with { Id = processId } };
        }

        var processContext = new DaprKernelProcessContext(process);
        await processContext.StartWithEventAsync(initialEvent).ConfigureAwait(false);
        return processContext;
    }
}
