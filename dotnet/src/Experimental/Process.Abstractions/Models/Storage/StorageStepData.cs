// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models.Storage;

/// <summary>
/// Data class for the parent of a step.
/// </summary>
public record StorageStepData : StorageEntryBase
{
    /// <summary>
    /// Process runtime details like id, parent id, step id mapping, etc.
    /// </summary>
    [JsonPropertyName("stepInfo")]
    public StorageStepInfo StepInfo { get; set; }

    /// <summary>
    /// Process runtime unprocessed events
    /// </summary>
    [JsonPropertyName("stepEvents")]
    public StorageStepEvents? StepEvents { get; set; } = null;

    /// <summary>
    /// Step state if any.
    /// </summary>
    [JsonPropertyName("stepState")]
    public StorageStepState? StepState { get; set; } = null;
}
