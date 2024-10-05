// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// A wrapper around <see cref="KernelProcessEvent"/> that helps to manage the namespace of the event.
/// </summary>
internal record LocalEvent
{
    /// <summary>
    /// The inner <see cref="KernelProcessEvent"/> that this <see cref="LocalEvent"/> wraps.
    /// </summary>
    private KernelProcessEvent InnerEvent { get; init; }

    /// <summary>
    /// The namespace of the event.
    /// </summary>
    internal string? Namespace { get; init; }

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
    /// Initializes a new instance of the <see cref="LocalEvent"/> class.
    /// </summary>
    /// <param name="eventNamespace">The namespace of the event.</param>
    /// <param name="innerEvent">The instance of <see cref="KernelProcessEvent"/> that this <see cref="LocalEvent"/> came from.</param>
    internal LocalEvent(string? eventNamespace, KernelProcessEvent innerEvent)
    {
        this.Namespace = eventNamespace;
        this.InnerEvent = innerEvent;
    }

    /// <summary>
    /// Creates a new <see cref="LocalEvent"/> from a <see cref="KernelProcessEvent"/>.
    /// </summary>
    /// <param name="kernelProcessEvent">The <see cref="KernelProcessEvent"/></param>
    /// <param name="Namespace">The namespace of the event.</param>
    /// <returns>An instance of <see cref="LocalEvent"/></returns>
    internal static LocalEvent FromKernelProcessEvent(KernelProcessEvent kernelProcessEvent, string Namespace) => new(Namespace, kernelProcessEvent);
}
