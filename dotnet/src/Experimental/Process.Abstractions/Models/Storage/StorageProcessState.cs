// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
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
    [JsonPropertyName("processId")]
    public string ProcessId { get; set; } = string.Empty;

    /// <summary>
    /// Map containing Step Names and their respective step instance
    /// </summary>
    [DataMember]
    [JsonPropertyName("steps")]
    public Dictionary<string, string> Steps { get; set; } = [];
}
