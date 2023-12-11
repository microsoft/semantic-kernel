// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents text content return from a <see cref="ITextGenerationService" /> service.
/// </summary>
public sealed class TextContent : KernelContent
{
    /// <summary>
    /// The text content.
    /// </summary>
    public string? Text { get; set; }

    /// <summary>
    /// The encoding of the text content.
    /// </summary>
    [JsonIgnore]
    public Encoding Encoding { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="TextContent"/> class.
    /// </summary>
    /// <param name="text">Text content</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="encoding">Encoding of the text</param>
    /// <param name="metadata">Additional metadata</param>
    public TextContent(string? text, string? modelId = null, object? innerContent = null, Encoding? encoding = null, IDictionary<string, object?>? metadata = null) : base(innerContent, modelId, metadata)
    {
        this.Text = text;
        this.Encoding = encoding ?? Encoding.UTF8;
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Text ?? string.Empty;
    }
}
