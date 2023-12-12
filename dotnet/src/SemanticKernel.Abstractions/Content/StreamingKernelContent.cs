// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a single update to a streaming content.
/// </summary>
public abstract class StreamingKernelContent
{
    /// <summary>
    /// In a scenario of multiple choices per request, this represents zero-based index of the choice in the streaming sequence
    /// </summary>
    public int ChoiceIndex { get; }

    /// <summary>
    /// The inner content representation. Use this to bypass the current abstraction.
    /// </summary>
    /// <remarks>
    /// The usage of this property is considered "unsafe". Use it only if strictly necessary.
    /// </remarks>
    [JsonIgnore]
    public object? InnerContent { get; }

    /// <summary>
    /// The model ID used to generate the content.
    /// </summary>
    public string? ModelId { get; }

    /// <summary>
    /// The metadata associated with the content.
    /// </summary>
    public IDictionary<string, object?>? Metadata { get; }

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
    /// Initializes a new instance of the <see cref="StreamingKernelContent"/> class.
    /// </summary>
    /// <param name="innerContent">Inner content object reference</param>
    /// <param name="choiceIndex">Choice index</param>
    /// <param name="modelId">The model ID used to generate the content.</param>
    /// <param name="metadata">Additional metadata associated with the content.</param>
    protected StreamingKernelContent(object? innerContent, int choiceIndex = 0, string? modelId = null, IDictionary<string, object?>? metadata = null)
    {
        this.ModelId = modelId;
        this.InnerContent = innerContent;
        this.ChoiceIndex = choiceIndex;
        if (metadata is not null)
        {
            this.Metadata = new Dictionary<string, object?>(metadata);
        }
    }
}
