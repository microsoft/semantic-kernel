// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel.Process.Runtime;

/// <summary>
/// Represents a message used in a process runtime.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="ProcessMessage"/> class.
/// </remarks>
/// <param name="EventName">Original name of the name of the event triggered</param>
/// <param name="EventId">Original name of the name of the event triggered</param>
/// <param name="SourceId">The source identifier of the message.</param>
/// <param name="DestinationId">The destination identifier of the message.</param>
/// <param name="FunctionName">The name of the function associated with the message.</param>
/// <param name="Values">The dictionary of values associated with the message.</param>
[KnownType(typeof(KernelProcessError))]
public record ProcessMessage(
    string EventName,
    string EventId,
    string SourceId,
    string DestinationId,
    string FunctionName,
    Dictionary<string, object?> Values)
{
    /// <summary>
    /// The Id of the target event. This may be null if the message is not targeting a sub-process.
    /// </summary>
    public string? TargetEventId { get; init; }

    /// <summary>
    /// The data associated with the target event. This may be null if the message is not targeting a sub-process.
    /// </summary>
    public object? TargetEventData { get; init; }
}
