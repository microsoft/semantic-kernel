// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.AI;

/// <summary>
/// Base class for all AI results
/// </summary>
public abstract class ModelContent
{
    /// <summary>
    /// The metadata associated with the content.
    /// </summary>
    protected Dictionary<string, object?> InternalMetadata { get; set; } = new Dictionary<string, object?>();

    /// <summary>
    /// Raw content object reference. (Breaking glass).
    /// </summary>
    public object? InnerContent { get; }

    /// <summary>
    /// The metadata associated with the content.
    /// </summary>
    [JsonExtensionData]
    public IReadOnlyDictionary<string, object?> Metadata => this.InternalMetadata;

    /// <summary>
    /// Initializes a new instance of the <see cref="ModelContent"/> class.
    /// </summary>
    /// <param name="innerContent">Raw content object reference</param>
    /// <param name="metadata">Metadata associated with the content</param>
    [JsonConstructor]
    protected ModelContent(object? innerContent, IReadOnlyDictionary<string, object?>? metadata = null)
    {
        this.InnerContent = innerContent;
        if (metadata is null)
        {
            return;
        }

        if (metadata is Dictionary<string, object?> writeableMetadata)
        {
            this.InternalMetadata = writeableMetadata;
        }
        else
        {
            foreach (var kv in metadata)
            {
                this.InternalMetadata.Add(kv.Key, kv.Value);
            }
        }
    }

    /// <summary>
    /// Implicit conversion to string
    /// </summary>
    /// <param name="modelContent">model Content</param>
    public static implicit operator string(ModelContent modelContent)
    {
        return modelContent.ToString();
    }
}
