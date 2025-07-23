// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models.Storage;

/// <summary>
/// Storage representation of step edges data.
/// </summary>
public record StorageStepEvents
{
    /// <summary>
    /// Data received by step edges, used when step function has multiple parameters
    /// </summary>
    [JsonPropertyName("edgeGroupEvents")]
    public Dictionary<string, Dictionary<string, KernelProcessEventData?>>? EdgesData { get; set; } = null;

    //[JsonPropertyName("lastEventReceived")]
}
