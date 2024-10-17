// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;
/// <summary>
/// A representation of an event raised within a process while running in Dapr.
/// </summary>
public record DaprEvent
{
    /// <summary>
    /// The inner <see cref="KernelProcessEvent"/> that this <see cref="DaprEvent"/> wraps.
    /// </summary>
    public required KernelProcessEvent InnerEvent { get; init; }

    /// <summary>
    /// The namespace of the event.
    /// </summary>
    public required string? Namespace { get; init; }

    /// <summary>
    /// The Id of the event.
    /// </summary>
    internal string Id => $"{this.Namespace}.{this.InnerEvent.Id}";

    /// <summary>
    /// The data of the event.
    /// </summary>
    internal object? Data => this.InnerEvent.Data;

    /// <summary>
    /// The visibility of the event.
    /// </summary>
    internal KernelProcessEventVisibility Visibility => this.InnerEvent.Visibility;

    /// <summary>
    /// Creates a new <see cref="DaprEvent"/> from a <see cref="KernelProcessEvent"/>.
    /// </summary>
    /// <param name="kernelProcessEvent">The <see cref="KernelProcessEvent"/></param>
    /// <param name="eventNamespace">The namespace of the event.</param>
    /// <returns>An instance of <see cref="DaprEvent"/></returns>
    internal static DaprEvent FromKernelProcessEvent(KernelProcessEvent kernelProcessEvent, string eventNamespace) => new() { Namespace = eventNamespace, InnerEvent = kernelProcessEvent };
}
