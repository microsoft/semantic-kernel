// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Process.TestsShared.CloudEvents;

/// <summary>
/// Mock cloud event data used for testing purposes only
/// </summary>
public class MockCloudEventData
{
    /// <summary>
    /// Name of the mock topic
    /// </summary>
    [DataMember]
    [JsonPropertyName("topicName")]
    public required string TopicName { get; set; }

    /// <summary>
    /// Data emitted in the mock cloud event
    /// </summary>
    [DataMember]
    [JsonPropertyName("data")]
    public KernelProcessProxyMessage? Data { get; set; }
}
