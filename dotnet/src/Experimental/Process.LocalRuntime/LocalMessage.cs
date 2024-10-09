// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;
/// <summary>
/// Represents a local message used in the local runtime.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="LocalMessage"/> class.
/// </remarks>
/// <param name="sourceId">The source identifier of the message.</param>
/// <param name="destinationId">The destination identifier of the message.</param>
/// <param name="functionName">The name of the function associated with the message.</param>
/// <param name="values">The dictionary of values associated with the message.</param>
internal record LocalMessage(string sourceId, string destinationId, string functionName, Dictionary<string, object?> values)
{
    /// <summary>
    /// Gets the source identifier of the message.
    /// </summary>
    public string SourceId { get; } = sourceId;

    /// <summary>
    /// Gets the destination identifier of the message.
    /// </summary>
    public string DestinationId { get; } = destinationId;

    /// <summary>
    /// Gets the name of the function associated with the message.
    /// </summary>
    public string FunctionName { get; } = functionName;

    /// <summary>
    /// Gets the dictionary of values associated with the message.
    /// </summary>
    public Dictionary<string, object?> Values { get; } = values;

    /// <summary>
    /// The Id of the target event. This may be null if the message is not targeting a sub-process.
    /// </summary>
    public string? TargetEventId { get; init; }

    /// <summary>
    /// The data associated with the target event. This may be null if the message is not targeting a sub-process.
    /// </summary>
    public object? TargetEventData { get; init; }
}
