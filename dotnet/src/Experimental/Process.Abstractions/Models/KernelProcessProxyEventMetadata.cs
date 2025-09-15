// Copyright (c) Microsoft. All rights reserved.
using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models;

/// <summary>
/// Process state used for State Persistence serialization
/// </summary>
public sealed record class KernelProcessProxyEventMetadata
{
    /// <summary>
    /// Name of the topic to be emitted externally
    /// </summary>
    [DataMember]
    [JsonPropertyName("topicName")]
    public string TopicName { get; set; } = string.Empty;

    /// <summary>
    /// Internal id used to identify the SK event
    /// </summary>
    [DataMember]
    [JsonPropertyName("eventId")]
    public string EventId { get; set; } = string.Empty;
}
