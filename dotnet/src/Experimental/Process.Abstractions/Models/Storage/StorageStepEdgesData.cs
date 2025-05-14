// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models.Storage;

/// <summary>
/// Storage representation of step edges data.
/// </summary>
public record StorageStepEdgesData
{
    // TODO: potentially also add versioning/snapshot info to allow "going back in time"

    /// <summary>
    /// Data received by step edges
    /// </summary>
    [DataMember]
    [JsonPropertyName("edgesData")]
    public Dictionary<string, Dictionary<string, KernelProcessEventData?>> EdgesData { get; set; } = [];

    /// <summary>
    /// Indicates if the edge is a group edge
    /// </summary>
    [DataMember]
    [JsonPropertyName("isGroupEdge")]
    public bool IsGroupEdge { get; set; } = false;
}
