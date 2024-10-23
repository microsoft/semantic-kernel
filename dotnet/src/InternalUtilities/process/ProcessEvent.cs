// Copyright (c) Microsoft. All rights reserved.
using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel.Process.Runtime;

/// <summary>
/// A wrapper around <see cref="KernelProcessEvent"/> that helps to manage the namespace of the event.
/// </summary>
/// <param name="Namespace">The namespace of the event.</param>
/// <param name="InnerEvent">The instance of <see cref="KernelProcessEvent"/> that this <see cref="ProcessEvent"/> came from.</param>
[DataContract]
public record ProcessEvent(
    [property: DataMember] string? Namespace,
    [property: DataMember] KernelProcessEvent InnerEvent)
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

    /// <summary>
    /// Creates a new <see cref="ProcessEvent"/> from a <see cref="KernelProcessEvent"/>.
    /// </summary>
    /// <param name="kernelProcessEvent">The <see cref="KernelProcessEvent"/></param>
    /// <param name="Namespace">The namespace of the event.</param>
    /// <returns>An instance of <see cref="ProcessEvent"/></returns>
    internal static ProcessEvent FromKernelProcessEvent(KernelProcessEvent kernelProcessEvent, string Namespace) => new(Namespace, kernelProcessEvent);
}
