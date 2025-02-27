// Copyright (c) Microsoft. All rights reserved.
using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of an internal message used in a process runtime received by proxy steps.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="KernelProcessProxyMessage"/> class.
/// </remarks>
[DataContract]
public record KernelProcessProxyMessage
{
    /// <summary>
    /// Id of the SK process that emits the external event
    /// </summary>
    [DataMember]
    public string? ProcessId { get; init; }

    /// <summary>
    /// Name of the SK process that triggers sending the event externally
    /// </summary>
    [DataMember]
    public string? TriggerEventId { get; init; }

    /// <summary>
    /// Topic name used for publishing process event data externally
    /// </summary>
    [DataMember]
    public string? ExternalTopicName { get; init; }
    /// <summary>
    /// Event name used for publishing process event as another process event with a different event name
    /// </summary>
    [DataMember]
    public string? ProxyEventName { get; init; }
    /// <summary>
    /// Data to be emitted
    /// </summary>
    [DataMember]
    public object? EventData { get; init; }
}
