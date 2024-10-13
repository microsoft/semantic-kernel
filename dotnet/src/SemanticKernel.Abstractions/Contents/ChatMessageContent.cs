// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
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
    [EditorBrowsable(EditorBrowsableState.Never)]
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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                    modelId: this.ModelId,
                    innerContent: this.InnerContent,
                    encoding: this.Encoding,
                    metadata: this.Metadata
                )
                { MimeType = this.MimeType });
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
                ////modelId: this.ModelId, // %%% REDUNDANT
                ////innerContent: this.InnerContent, // %%% CARDINALITY MISMATCH / INVALID ASSUMPTION / MUTATION RISK (IGNORED FOR SERIALIZATION)
                    encoding: this.Encoding // %%% WEIRD, BUT WHO CARES (IGNORED FOR SERIALIZATION)
                ////metadata: this.Metadata, // %%% CARDINALITY MISMATCH / MUTATION RISK
                )
                { MimeType = this.MimeType }); // %%% CARDINALITY MISMATCH / INVALID ASSUMPTION
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
    /// The source is corresponds to the entity that generated this message.
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// The property is intended to be used by agents to associate themselves with the messages they generate.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    /// The property is intended to be used by agents to associate themselves with the messages they generate.
=======
    /// The property is intended to be used by agents to associate themselves with the messages they generate or by a user who created it.
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    /// The property is intended to be used by agents to associate themselves with the messages they generate or by a user who created it.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
    /// The property is intended to be used by agents to associate themselves with the messages they generate or by a user who created it.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
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
