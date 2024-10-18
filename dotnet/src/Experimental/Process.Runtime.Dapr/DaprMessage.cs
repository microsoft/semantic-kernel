// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a message used in the Dapr runtime.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="DaprMessage"/> class.
/// </remarks>
public record DaprMessage
{
    /// <summary>
    /// Gets the source identifier of the message.
    /// </summary>
    public required string SourceId { get; init; }

    /// <summary>
    /// Gets the destination identifier of the message.
    /// </summary>
    public required string DestinationId { get; init; }

    /// <summary>
    /// Gets the name of the function associated with the message.
    /// </summary>
    public required string FunctionName { get; init; }

    /// <summary>
    /// Gets the dictionary of values associated with the message.
    /// </summary>
    public required Dictionary<string, object?> Values { get; init; }

    /// <summary>
    /// The Id of the target event. This may be null if the message is not targeting a sub-process.
    /// </summary>
    public string? TargetEventId { get; init; }

    /// <summary>
    /// The data associated with the target event. This may be null if the message is not targeting a sub-process.
    /// </summary>
    public object? TargetEventData { get; init; }
}
