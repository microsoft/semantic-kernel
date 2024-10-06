// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// An class representing an event that can be emitted from a <see cref="KernelProcessStep"/>. This type is convertible to and from CloudEvents.
/// </summary>
<<<public class KernelProcessEvent
>>>>>>>+HEAD
====
pubpublic sealed record KernelProcessEvent
>>>>>>>+main
   /// <summary>
    /// The unique identifier for the event.
    /// </summary>
    public string? Id { get; set; }

    /// <summary>
    /// An optional data payload associated with the event.
    /// </summary>
    public object? Data { get; set; }

    /// <summary>
    /// The visibility of the event. Defaults to <see cref="KernelProcessEventVisibility.Internal"/>.
    /// </summary>
    public KernelProcessEventVisibility Visibility { get; set; } = KernelProcessEventVisibility.Internal;
}
