// Copyright (c) Microsoft. All rights reserved.
using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel.Process.Runtime;

/// <summary>
/// A wrapper around <see cref="KernelProcessEvent"/> that helps to manage the namespace of the event.
/// </summary>
/// <param name="Namespace">The namespace of the event.</param>
/// <param name="InnerEvent">The instance of <see cref="KernelProcessEvent"/> that this <see cref="ProcessEvent"/> came from.</param>
/// <param name="IsError">This event represents a runtime error / exception raised internally by the framework.</param>
[DataContract]
[KnownType(typeof(KernelProcessError))]
public record ProcessEvent(
    [property: DataMember] string? Namespace,
    [property: DataMember] KernelProcessEvent InnerEvent,
    [property: DataMember] bool IsError = false)
{
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
}
