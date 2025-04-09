// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.Process.Internal;

namespace Microsoft.SemanticKernel.Process.Runtime;

/// <summary>
/// A wrapper around <see cref="KernelProcessEvent"/> that helps to manage the namespace of the event.
/// </summary>
public record ProcessEvent
{
    /// <summary>
    /// The namespace of the event.
    /// </summary>
    public string Namespace { get; init; } = string.Empty;

    /// <summary>
    /// The source Id of the event.
    /// </summary>
    public string SourceId { get; init; } = string.Empty;

    /// <summary>
    /// An optional data payload associated with the event.
    /// </summary>
    public object? Data { get; init; }

    /// <summary>
    /// The visibility of the event.
    /// </summary>
    public KernelProcessEventVisibility Visibility { get; init; }

    /// <summary>
    /// This event represents a runtime error / exception raised internally by the framework.
    /// </summary>
    public bool IsError { get; init; }

    /// <summary>
    /// The Qualified Id of the event.
    /// </summary>
    internal string QualifiedId => $"{this.Namespace}{ProcessConstants.EventIdSeparator}{this.SourceId}";

    /// <summary>
    /// Creates a new <see cref="ProcessEvent"/> from a <see cref="KernelProcessEvent"/>.
    /// </summary>
    /// <param name="kernelProcessEvent">The <see cref="KernelProcessEvent"/></param>
    /// <param name="eventNamespace">The namespace of the event.</param>
    /// <param name="isError">Indicates if event is from a runtime error.</param>
    internal static ProcessEvent Create(KernelProcessEvent kernelProcessEvent, string eventNamespace, bool isError = false) =>
        new()
        {
            Namespace = eventNamespace,
            SourceId = kernelProcessEvent.Id,
            Data = KernelProcessEventData.FromObject(kernelProcessEvent.Data),
            Visibility = kernelProcessEvent.Visibility,
            IsError = isError,
        };

    /// <summary>
    /// Creates a new <see cref="ProcessEvent"/>.
    /// </summary>
    /// <param name="data">data passed in the event</param>
    /// <param name="eventNamespace">The namespace of the event.</param>
    /// <param name="sourceId">event source id</param>
    /// <param name="eventVisibility">visibility of the event</param>
    /// <param name="isError">Indicates if event is from a runtime error.</param>
    /// <returns></returns>
    internal static ProcessEvent Create(object? data, string eventNamespace, string sourceId, KernelProcessEventVisibility eventVisibility, bool isError = false) =>
        new()
        {
            Namespace = eventNamespace,
            SourceId = sourceId,
            Data = KernelProcessEventData.FromObject(data),
            IsError = isError,
            Visibility = eventVisibility,
        };
}
