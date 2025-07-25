// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel.Process.Models.Storage;
/// <summary>
/// Extension methods for converting between StorageProcessState and KernelProcess.
/// </summary>
public static class StorageProcessExtension
{
    /// <summary>
    /// Converts a <see cref="KernelProcess"/> to a <see cref="StorageProcessInfo"/>.
    /// </summary>
    /// <param name="kernelProcess">instance of <see cref="KernelProcess"/></param>
    /// <returns></returns>
    public static StorageProcessInfo ToKernelStorageProcessInfo(this KernelProcess kernelProcess)
    {
        return new StorageProcessInfo
        {
            ProcessName = kernelProcess.StepId ?? string.Empty,
            InstanceId = kernelProcess.RunId ?? string.Empty,
            Steps = kernelProcess.Steps.ToList().ToDictionary(step => step.State.StepId, step => step.State.RunId ?? string.Empty) ?? [],
            ParentId = kernelProcess.ParentId,
        };
    }

    /// <summary>
    /// Converts a <see cref="KernelProcess"/> to a <see cref="StorageProcessInfo"/>.
    /// </summary>
    /// <param name="pendingExternalEvents">list of ending external events to be processed</param>
    /// <returns></returns>
    public static StorageProcessEvents ToKernelStorageProcessEvents(List<KernelProcessEvent>? pendingExternalEvents = null)
    {
        return new StorageProcessEvents
        {
            ExternalPendingMessages = pendingExternalEvents ?? new List<KernelProcessEvent>(),
        };
    }

    /// <summary>
    /// Converts a <see cref="StorageProcessState"/> to a dictionary of shared variables for the kernel process.
    /// </summary>
    /// <param name="storageProcessState"></param>
    /// <returns></returns>
    public static Dictionary<string, object?> ToKernelProcessSharedVariables(this StorageProcessState storageProcessState)
    {
        return storageProcessState.SharedVariables.ToDictionary(
            kvp => kvp.Key,
            kvp => kvp.Value?.ToObject());
    }

    /// <summary>
    /// Converts a <see cref="KernelProcess"/> to a <see cref="StorageProcessState"/>.
    /// </summary>
    /// <param name="processSharedVariables"></param>
    /// <returns></returns>
    public static StorageProcessState ToKernelStorageProcessState(Dictionary<string, object>? processSharedVariables = null)
    {
        return new StorageProcessState
        {
            SharedVariables = processSharedVariables?.ToDictionary(
                kvp => kvp.Key,
                kvp => KernelProcessEventData.FromObject(kvp.Value)) ?? []
        };
    }
}
