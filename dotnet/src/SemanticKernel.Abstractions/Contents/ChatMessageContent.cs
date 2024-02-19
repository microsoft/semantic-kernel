// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Linq;
using System.Text.Json.Serialization;
using System.Threading;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents chat message content return from a <see cref="IChatCompletionService" /> service.
/// </summary>
public class ChatMessageContent : KernelContent
{
    /// <summary>
    /// Role of the author of the message
    /// </summary>
    public AuthorRole Role { get; set; }

    /// <summary>
    /// Content of the message
    /// </summary>
    public string? Content
    {
        get
        {
            if (this.Items.Count == 0)
            {
                return null;
            }

            if (this.Items[0] is TextContent textContent)
            {
                return textContent.Text;
            }

            throw new InvalidOperationException($"Cannot get the text content of the item of type {this.Items[0].GetType()}.");
        }
        set
        {
            if (value == null)
            {
                return;
            }

            if (this.Items.Count == 0)
            {
                this.Items.Add(new TextContent(
                    text: value,
                    modelId: this.ModelId,
                    innerContent: this.InnerContent,
                    encoding: this.Encoding,
                    metadata: this.Metadata
                ));
                return;
            }

            if (this.Items[0] is TextContent textContent)
            {
                textContent.Text = value;
                textContent.Encoding = this.Encoding;
                return;
            }

            throw new InvalidOperationException($"Cannot set text content for the item of type {this.Items[0].GetType()}");
        }
    }

    /// <summary>
    /// Chat message content items
    /// </summary>
    public ChatMessageContentItemCollection Items =>
        this._items ??
        Interlocked.CompareExchange(ref this._items, new ChatMessageContentItemCollection(), null) ??
        this._items;

    /// <summary>
    /// The encoding of the text content.
    /// </summary>
    [JsonIgnore]
    public Encoding Encoding
    {
        get
        {
            if (this.Items.FirstOrDefault() is TextContent textContent)
            {
                return textContent.Encoding;
            }

            return this._encoding;
        }
        set
        {
            this._encoding = value;

            if (this.Items.FirstOrDefault() is TextContent textContent)
            {
                textContent.Encoding = value;
            }
        }
    }

    /// <summary>
    /// Creates a new instance of the <see cref="ChatMessageContent"/> class
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="content">Content of the message</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content object reference</param>
    /// <param name="encoding">Encoding of the text</param>
    /// <param name="metadata">Dictionary for any additional metadata</param>
    [JsonConstructor]
    public ChatMessageContent(
        AuthorRole role,
        string? content,
        string? modelId = null,
        object? innerContent = null,
        Encoding? encoding = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Role = role;
        this._encoding = encoding ?? Encoding.UTF8;
        this.Content = content;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="ChatMessageContent"/> class
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="items">Instance of <see cref="ChatMessageContentItemCollection"/> with content items</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content object reference</param>
    /// <param name="encoding">Encoding of the text</param>
    /// <param name="metadata">Dictionary for any additional metadata</param>
    public ChatMessageContent(
        AuthorRole role,
        ChatMessageContentItemCollection items,
        string? modelId = null,
        object? innerContent = null,
        Encoding? encoding = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Role = role;
        this._encoding = encoding ?? Encoding.UTF8;
        this._items = items;
    }

    /// <inheritdoc/>
    public override string ToString()
    {
#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            return this.Content ?? string.Empty;
        }
        catch
        {
            return string.Empty;
        }
#pragma warning restore CA1031 // Do not catch general exception types
    }

    private ChatMessageContentItemCollection? _items;
    private Encoding _encoding;
}
