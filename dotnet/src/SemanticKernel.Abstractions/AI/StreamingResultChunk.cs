// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.AI;

/// <summary>
/// Represents a single update to a streaming result.
/// </summary>
public abstract class StreamingResultChunk
{
    /// <summary>
    /// Type of the update.
    /// </summary>
    public abstract string Type { get; }

    /// <summary>
    /// In a scenario of multiple results, this represents zero-based index of the result in the streaming sequence
    /// </summary>
    public abstract int ResultIndex { get; }

    /// <summary>
    /// Converts the update class to string.
    /// </summary>
    /// <returns>String representation of the update</returns>
    public abstract override string ToString();

    /// <summary>
    /// Converts the update class to byte array.
    /// </summary>
    /// <returns>Byte array representation of the update</returns>
    public abstract byte[] ToByteArray();

    /// <summary>
    /// The current context associated the function call.
    /// </summary>
    [JsonIgnore]
    internal SKContext? Context { get; set; }
}
