// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
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
    /// Text associated to the message payload
    /// </summary>
    public string? Content { get; set; }

    /// <summary>
    /// Role of the author of the message
    /// </summary>
    public AuthorRole? Role { get; set; }

    /// <summary>
    /// The encoding of the text content.
    /// </summary>
    [JsonIgnore]
    public Encoding Encoding { get; set; }

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
    public StreamingChatMessageContent(AuthorRole? role, string? content, object? innerContent = null, int choiceIndex = 0, string? modelId = null, Encoding? encoding = null, IDictionary<string, object?>? metadata = null) : base(innerContent, choiceIndex, modelId, metadata)
    {
        this.Role = role;
        this.Content = content;
        this.Encoding = encoding ?? Encoding.UTF8;
    }

    /// <inheritdoc/>
    public override string ToString() => this.Content ?? string.Empty;

    /// <inheritdoc/>
    public override byte[] ToByteArray() => this.Encoding.GetBytes(this.ToString());
}
