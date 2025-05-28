// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models.Storage;

/// <summary>
/// Storage representation of a process state.
/// </summary>
public record StorageProcessState
{
    /// <summary>
    /// Name of the process builder used to create the process instance
    /// </summary>
    [DataMember]
    [JsonPropertyName("processName")]
    public string ProcessName { get; set; } = string.Empty;

    /// <summary>
    /// Id of the process instance
    /// </summary>
    [DataMember]
    [JsonPropertyName("processInstance")]
    public string ProcessInstance { get; set; } = string.Empty;

    /// <summary>
    /// Map containing Step Names and their respective step instance
    /// </summary>
    [DataMember]
    [JsonPropertyName("steps")]
    public Dictionary<string, string> Steps { get; set; } = [];
}

/// <summary>
/// Extension methods for converting between StorageProcessState and KernelProcess.
/// </summary>
public static class StorageProcessExtension
{
    /// <summary>
    /// Converts a <see cref="KernelProcess"/> to a <see cref="StorageProcessState"/>.
    /// </summary>
    /// <param name="kernelProcess">instance of <see cref="KernelProcess"/></param>
    /// <returns></returns>
    public static StorageProcessState ToKernelStorageProcessState(this KernelProcess kernelProcess)
    {
        return new StorageProcessState
        {
            ProcessName = kernelProcess.State?.StepId ?? string.Empty,
            ProcessInstance = kernelProcess.State?.RunId ?? string.Empty,
            Steps = kernelProcess.Steps.ToList().ToDictionary(step => step.State.StepId, step => step.State.RunId ?? string.Empty) ?? []
        };
    }
}
