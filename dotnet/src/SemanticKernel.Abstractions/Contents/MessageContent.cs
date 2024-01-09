#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents chat message content return from a <see cref="ITextGenerationService" /> service.
/// </summary>
public class MessageContent : KernelContent
{
    /// <summary>
    /// Creates a new instance of the <see cref="MessageContent"/> class
    /// </summary>
    /// <param name="content">Content of the message</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content object reference</param>
    /// <param name="encoding">Encoding of the text</param>
    /// <param name="metadata">Dictionary for any additional metadata</param>
    [JsonConstructor]
    public MessageContent(
        string? content,
        string? modelId = null,
        object? innerContent = null,
        Encoding? encoding = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Content = content;
        this.Encoding = encoding ?? Encoding.UTF8;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="MessageContent"/> class
    /// </summary>
    /// <param name="items">Instance of <see cref="MessageContentItemCollection"/> with content items</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content object reference</param>
    /// <param name="encoding">Encoding of the text</param>
    /// <param name="metadata">Dictionary for any additional metadata</param>
    public MessageContent(
        MessageContentItemCollection items,
        string? modelId = null,
        object? innerContent = null,
        Encoding? encoding = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Encoding = encoding ?? Encoding.UTF8;
        this.Items = items;
    }

    /// <summary>
    /// Content of the message
    /// </summary>
    public string? Content { get; set; }

    /// <summary>
    /// Chat message content items
    /// </summary>
    public MessageContentItemCollection? Items { get; set; }

    /// <summary>
    /// The encoding of the text content.
    /// </summary>
    [JsonIgnore]
    public Encoding Encoding { get; set; }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Content ?? string.Empty;
    }
}
