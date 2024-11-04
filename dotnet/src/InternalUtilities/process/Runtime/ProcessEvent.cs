// Copyright (c) Microsoft. All rights reserved.
using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel.Process.Runtime;

/// <summary>
/// A wrapper around <see cref="KernelProcessEvent"/> that helps to manage the namespace of the event.
/// </summary>
/// <param name="Namespace">The namespace of the event.</param>
/// <param name="SourceId">The source Id of the event.</param>
/// <remarks>
/// Initializes a new instance of the <see cref="ProcessEvent"/> class.
/// </remarks>
[DataContract]
[KnownType(typeof(KernelProcessError))]
public record ProcessEvent(
    [property: DataMember] string Namespace,
    [property: DataMember] string SourceId)
{
    /// <summary>
    /// An optional data payload associated with the event.
    /// </summary>
    /// <remarks>
    /// Possible to be defined and yet null.
    /// </remarks>
    [DataMember]
    public object? Data { get; init; }

    /// <summary>
    /// The visibility of the event.
    /// </summary>
    [DataMember]
    public KernelProcessEventVisibility Visibility { get; init; }

    /// <summary>
    /// This event represents a runtime error / exception raised internally by the framework.
    /// </summary>
    [DataMember]
    public bool IsError { get; init; }

    /// <summary>
    /// The Qualified Id of the event.
    /// </summary>
    internal string QualifiedId => $"{this.Namespace}.{this.SourceId}";
}
