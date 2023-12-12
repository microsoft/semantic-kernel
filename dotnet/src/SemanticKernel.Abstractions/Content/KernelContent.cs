// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Base class for all AI non-streaming results
/// </summary>
public abstract class KernelContent
{
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
    /// Initializes a new instance of the <see cref="KernelContent"/> class.
    /// </summary>
    /// <param name="innerContent">The inner content representation</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Metadata associated with the content</param>
    protected KernelContent(object? innerContent, string? modelId = null, IDictionary<string, object?>? metadata = null)
    {
        this.ModelId = modelId;
        this.InnerContent = innerContent;
        if (metadata is not null)
        {
            this.Metadata = new Dictionary<string, object?>(metadata);
        }
    }
}
