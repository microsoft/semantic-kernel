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
    /// Type of the chunk.
    /// </summary>
    public abstract string Type { get; }

    /// <summary>
    /// In a scenario of multiple choices per request, this represents zero-based index of the choice in the streaming sequence
    /// </summary>
    public abstract int ChoiceIndex { get; }

    /// <summary>
    /// Abstract string representation of the chunk in a way it could compose/append with previous chunks.
    /// </summary>
    /// <remarks>
    /// Depending on the nature of the underlying type, this method may be more efficient than <see cref="ToByteArray"/>.
    /// </remarks>
    /// <returns>String representation of the chunk</returns>
    public abstract override string ToString();

    /// <summary>
    /// Abstract byte[] representation of the chunk in a way it could be composed/appended with previous chunks.
    /// </summary>
    /// <remarks>
    /// Depending on the nature of the underlying type, this method may be more efficient than <see cref="ToString"/>.
    /// </remarks>
    /// <returns>Byte array representation of the chunk</returns>
    public abstract byte[] ToByteArray();

    /// <summary>
    /// Internal chunk object reference. (Breaking glass).
    /// Each connector will have its own internal object representing the result chunk.
    /// </summary>
    /// <remarks>
    /// The usage of this property is considered "unsafe". Use it only if strictly necessary.
    /// </remarks>
    public object? InnerResultChunk { get; }

    /// <summary>
    /// The current context associated the function call.
    /// </summary>
    [JsonIgnore]
    internal SKContext? Context { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="StreamingResultChunk"/> class.
    /// </summary>
    /// <param name="innerResultChunk">Inner result chunk object reference</param>
    protected StreamingResultChunk(object? innerResultChunk)
    {
        this.InnerResultChunk = innerResultChunk;
    }
}
