// Copyright (c) Microsoft. All rights reserved.
using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents an internal message used in a process runtime received by proxy steps.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="KernelProcessProxyMessage"/> class.
/// </remarks>
[KnownType(typeof(KernelProcessError))]
public record KernelProcessProxyMessage(
    string ProcessId,
    string TriggerEventId)
{
    /// <summary>
    /// Topic name used for publishing process event data externally
    /// </summary>
    public string? ExternalTopicName { get; init; }
    /// <summary>
    /// Event name used for publishing process event as another process event with a different event name
    /// </summary>
    public string? ProxyEventName { get; init; }
    /// <summary>
    /// Data to be emitted
    /// </summary>
    public object? EventData { get; init; }
}
