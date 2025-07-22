// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models.Storage;

// it seems all properties needed are already in KernelProcessStepStateMetadata
// using new class for now in case there some extra props needed while
// plumbing
/// <summary>
/// Data class for the parent of a step.
/// </summary>
public record StorageProcessData : StorageEntryBase
{
    /// <summary>
    /// Process runtime details like id, parent id, step id mapping, etc.
    /// </summary>
    [JsonPropertyName("processInfo")]
    public StorageProcessInfo ProcessInfo { get; set; } = new();

    /// <summary>
    /// Process runtime unprocessed events
    /// </summary>
    [JsonPropertyName("processEvents")]
    public StorageProcessEvents ProcessEvents { get; set; } = new();

    /* TODO: Plumb properly when proper support for ProcessState is added
    /// <summary>
    /// Process state/variables related data
    /// </summary>
    [JsonPropertyName("processState")]
    public StorageProcessState? ProcessState { get; set; } = null;
    */
}
