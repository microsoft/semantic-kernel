// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// A class representing an event that can be emitted from a <see cref="KernelProcessStep"/>. This type is convertible to and from CloudEvents.
/// </summary>
public record KernelProcessEvent
{
    /// <summary>
    /// The unique identifier for the event.
    /// </summary>
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// The visibility of the event. Defaults to <see cref="KernelProcessEventVisibility.Internal"/>.
    /// </summary>
    public KernelProcessEventVisibility Visibility { get; set; } = KernelProcessEventVisibility.Internal;
}

/// <summary>
/// A class representing an event that can be emitted from a <see cref="KernelProcessStep"/>. This type is convertible to and from CloudEvents.
/// </summary>
public sealed record KernelProcessEvent<TData> : KernelProcessEvent
{
    /// <summary>
    /// An optional data payload associated with the event.
    /// </summary>
    public TData? Data { get; set; }
}
