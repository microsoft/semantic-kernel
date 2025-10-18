// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models.Storage;

/// <summary>
/// Storage representation of a process state.
/// </summary>
public record StorageStepInfo : StorageEntryBase
{
    /// <summary>
    /// Name of the process builder used to create the process instance
    /// </summary>
    [JsonPropertyName("stepName")]
    public string StepName { get; set; } = string.Empty;

    /// <summary>
    /// Id of the step parent process
    /// </summary>
    [JsonPropertyName("parentId")]
    public string ParentId { get; set; } = string.Empty;

    /// <summary>
    /// version of step
    /// </summary>
    [JsonPropertyName("version")]
    public string Version { get; set; } = string.Empty;
}
