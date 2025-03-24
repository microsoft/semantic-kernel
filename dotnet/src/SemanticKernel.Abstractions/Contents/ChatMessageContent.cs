// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents chat message content return from a <see cref="IChatCompletionService" /> service.
/// </summary>
public class ChatMessageContent : KernelContent
{
    /// <summary>
    /// Name of the author of the message
    /// </summary>
    [Experimental("SKEXP0001")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? AuthorName
    {
        get => this._authorName;
        set => this._authorName = string.IsNullOrWhiteSpace(value) ? null : value;
    }

    /// <summary>
    /// Role of the author of the message
    /// </summary>
    public AuthorRole Role { get; set; }

    /// <summary>
    /// A convenience property to get or set the text of the first item in the <see cref="Items" /> collection of <see cref="TextContent"/> type.
    /// </summary>
    [JsonIgnore]
    public string? Content
    {
        get
        {
            var textContent = this.Items.OfType<TextContent>().FirstOrDefault();
            return textContent?.Text;
        }
        set
        {
            var textContent = this.Items.OfType<TextContent>().FirstOrDefault();
            if (textContent is not null)
            {
                textContent.Text = value;
            }
            else if (value is not null)
            {
                this.Items.Add(new TextContent(
                    text: value,
                    modelId: this.ModelId,
                    innerContent: this.InnerContent,
                    encoding: this.Encoding,
                    metadata: this.Metadata
                )
                { MimeType = this.MimeType });
            }
        }
    }

    /// <summary>
    /// Chat message content items
    /// </summary>
    public ChatMessageContentItemCollection Items
    {
        get => this._items ??= [];
        set => this._items = value;
    }

    /// <summary>
    /// The encoding of the text content.
    /// </summary>
    [JsonIgnore]
    public Encoding Encoding
    {
        get
        {
            var textContent = this.Items.OfType<TextContent>().FirstOrDefault();
            if (textContent is not null)
            {
                return textContent.Encoding;
            }

            return this._encoding;
        }
        set
        {
            this._encoding = value;

            var textContent = this.Items.OfType<TextContent>().FirstOrDefault();
            if (textContent is not null)
            {
                textContent.Encoding = value;
            }
        }
    }

    /// <summary>
    /// Represents the source of the message.
    /// </summary>
    /// <remarks>
    /// The source corresponds to the entity that generated this message.
    /// The property is intended to be used by agents to associate themselves with the messages they generate.
    /// </remarks>
    [Experimental("SKEXP0101")]
    [JsonIgnore]
    public object? Source { get; set; }

    /// <summary>
    /// Creates a new instance of the <see cref="ChatMessageContent"/> class
    /// </summary>
    [JsonConstructor]
    public ChatMessageContent()
    {
        this._encoding = Encoding.UTF8;
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
        return this.Content ?? string.Empty;
    }

    private ChatMessageContentItemCollection? _items;
    private Encoding _encoding;
    private string? _authorName;
}
