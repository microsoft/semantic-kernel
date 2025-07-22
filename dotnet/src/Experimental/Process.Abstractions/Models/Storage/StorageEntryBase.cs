// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models.Storage;

public abstract record StorageEntryBase
{
    [JsonPropertyName("instanceId")]
    public string InstanceId { get; set; } = string.Empty;
}
