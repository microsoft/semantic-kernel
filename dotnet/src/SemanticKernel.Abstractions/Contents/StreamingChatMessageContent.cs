// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Abstraction of chat message content chunks when using streaming from <see cref="IChatCompletionService"/> interface.
/// </summary>
/// <remarks>
/// Represents a chat message content chunk that was streamed from the remote model.
/// </remarks>
public class StreamingChatMessageContent : StreamingKernelContent
{
    /// <summary>
    /// A convenience property to get or set the text of the first item in the <see cref="Items" /> collection of <see cref="StreamingTextContent"/> type.
    /// </summary>
    public string? Content
    {
        get
        {
            var textContent = this.Items.OfType<StreamingTextContent>().FirstOrDefault();
            return textContent?.Text;
        }
        set
        {
            var textContent = this.Items.OfType<StreamingTextContent>().FirstOrDefault();
            if (textContent is not null)
            {
                textContent.Text = value;
            }
            else if (value is not null)
            {
                this.Items.Add(new StreamingTextContent(
                    text: value,
                    choiceIndex: this.ChoiceIndex,
                    modelId: this.ModelId,
                    innerContent: this.InnerContent,
                    encoding: this.Encoding,
                    metadata: this.Metadata
                ));
            }
        }
    }

    /// <summary>
    /// Chat message content items.
    /// </summary>
    [JsonIgnore]
    public StreamingKernelContentItemCollection Items
    {
        get => this._items ??= [];
        set => this._items = value;
    }

    /// <summary>
    /// Name of the author of the message
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [Experimental("SKEXP0001")]
    public string? AuthorName
    {
        get => this._authorName;
        set => this._authorName = string.IsNullOrWhiteSpace(value) ? null : value;
    }

    /// <summary>
    /// Role of the author of the message
    /// </summary>
    public AuthorRole? Role { get; set; }

    /// <summary>
    /// A convenience property to get or set the encoding of the first item in the <see cref="Items" /> collection of <see cref="StreamingTextContent"/> type.
    /// </summary>
    [JsonIgnore]
    public Encoding Encoding
    {
        get
        {
            var textContent = this.Items.OfType<StreamingTextContent>().FirstOrDefault();
            if (textContent is not null)
            {
                return textContent.Encoding;
            }

            return this._encoding;
        }
        set
        {
            this._encoding = value;

            var textContent = this.Items.OfType<StreamingTextContent>().FirstOrDefault();
            if (textContent is not null)
            {
                textContent.Encoding = value;
            }
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="StreamingChatMessageContent"/> class.
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="content">Content of the message</param>
    /// <param name="innerContent">Inner content object reference</param>
    /// <param name="choiceIndex">Choice index</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="encoding">Encoding of the chat</param>
    /// <param name="metadata">Additional metadata</param>
    [JsonConstructor]
    public StreamingChatMessageContent(AuthorRole? role, string? content, object? innerContent = null, int choiceIndex = 0, string? modelId = null, Encoding? encoding = null, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, choiceIndex, modelId, metadata)
    {
        this.Role = role;
        this.Content = content;
        this._encoding = encoding ?? Encoding.UTF8;
    }

    /// <inheritdoc/>
    public override string ToString() => this.Content ?? string.Empty;

    /// <inheritdoc/>
    public override byte[] ToByteArray() => this.Encoding.GetBytes(this.ToString());

    private StreamingKernelContentItemCollection? _items;
    private Encoding _encoding;
    private string? _authorName;
}
