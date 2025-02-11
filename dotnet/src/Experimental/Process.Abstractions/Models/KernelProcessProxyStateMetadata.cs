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
    /// Map that stores which process events trigger external topic to be published
    /// </summary>
    [DataMember]
    [JsonPropertyName("eventTopicMap")]
    public Dictionary<string, string> EventPublishTopicMap { get; set; } = [];

    /// <summary>
    /// Map that stores the SK process event name with the running full event id
    /// </summary>
    [DataMember]
    [JsonPropertyName("eventDataMap")]
    public Dictionary<string, string> EventDataMap { get; set; } = [];
}
