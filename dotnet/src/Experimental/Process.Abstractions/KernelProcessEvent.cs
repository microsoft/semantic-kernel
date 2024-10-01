// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// An class representing an event that can be emitted from a <see cref="KernelProcessStep"/>. This type is convertible to and from CloudEvents.
/// </summary>
public sealed record KernelProcessEvent
{
    /// <summary>
    /// The unique identifier for the event.
    /// </summary>
    public string? Id { get; set; }

    /// <summary>
    /// An optional data payload associated with the event.
    /// </summary>
    public object? Data { get; set; }
}
