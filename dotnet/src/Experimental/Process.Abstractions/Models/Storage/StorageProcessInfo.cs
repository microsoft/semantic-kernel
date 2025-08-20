// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models.Storage;

/// <summary>
/// Storage representation of a process state.
/// </summary>
public record StorageProcessInfo : StorageEntryBase
{
    /// <summary>
    /// Name of the process builder used to create the process instance
    /// </summary>
    [JsonPropertyName("processName")]
    public string ProcessName { get; set; } = string.Empty;

    /// <summary>
    /// Id of the parent process, if null the process is a root process.
    /// </summary>
    [JsonPropertyName("parentId")]
    public string? ParentId { get; set; } = null;

    /// <summary>
    /// Map containing Step Names and their respective step instance
    /// </summary>
    [JsonPropertyName("steps")]
    public Dictionary<string, string> Steps { get; set; } = [];

    // TODO: Add running state here: RUNNING, COMPLETED (EndStep was reached), IDLE (it ran and no more events are in queue to be processed)
}
