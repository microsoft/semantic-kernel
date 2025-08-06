// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models.Storage;

/// <summary>
/// Base class for storage entries.
/// </summary>
public abstract record StorageEntryBase
{
    /// <summary>
    /// Unique identifier of the storage entry.
    /// </summary>
    [JsonPropertyName("instanceId")]
    public string InstanceId { get; set; } = string.Empty;
}
