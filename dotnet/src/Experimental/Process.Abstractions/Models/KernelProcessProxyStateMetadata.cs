// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models;

/// <summary>
/// Process state used for State Persistence serialization
/// </summary>
public sealed record class KernelProcessProxyStateMetadata : KernelProcessStepStateMetadata
{
    /// <summary>
    /// List of publish topics that can be used by the SK process
    /// </summary>
    [DataMember]
    [JsonPropertyName("publishTopics")]
    public List<string> PublishTopics { get; set; } = [];

    /// <summary>
    /// Map that stores which process events trigger external topic to be published and internal metadata information
    /// </summary>
    [DataMember]
    [JsonPropertyName("eventMetadata")]
    public Dictionary<string, KernelProcessProxyEventMetadata> EventMetadata { get; set; } = [];
}
