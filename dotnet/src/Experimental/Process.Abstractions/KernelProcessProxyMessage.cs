// Copyright (c) Microsoft. All rights reserved.
using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of an internal message used in a process runtime received by proxy steps.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="KernelProcessProxyMessage"/> class.
/// </remarks>
[DataContract]
public sealed record KernelProcessProxyMessage
{
    /// <summary>
    /// Id of the SK process that emits the external event
    /// </summary>
    [DataMember]
    [JsonPropertyName("processId")]
    public string? ProcessId { get; init; }

    /// <summary>
    /// Name of the SK process that triggers sending the event externally
    /// </summary>
    [DataMember]
    [JsonPropertyName("triggerEventId")]
    public string? TriggerEventId { get; init; }

    /// <summary>
    /// Topic name used for publishing process event data externally
    /// </summary>
    [DataMember]
    [JsonPropertyName("externalTopicName")]
    public string ExternalTopicName { get; init; } = string.Empty;
    /// <summary>
    /// Event name used for publishing process event as another process event with a different event name
    /// </summary>
    [DataMember]
    [JsonPropertyName("proxyEventName")]
    public string? ProxyEventName { get; init; }
    /// <summary>
    /// Data to be emitted
    /// </summary>
    [DataMember]
    [JsonPropertyName("eventData")]
    public KernelProcessEventData? EventData { get; init; }
}
