// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Streaming chat result update.
/// </summary>
public class StreamingChatContent : StreamingContent
{
    /// <inheritdoc/>
    public override int ChoiceIndex { get; }

    /// <summary>
    /// Function call associated to the message payload
    /// </summary>
    public FunctionCall? FunctionCall { get; }

    /// <summary>
    /// Text associated to the message payload
    /// </summary>
    public string? Content { get; }

    /// <summary>
    /// Role of the author of the message
    /// </summary>
    public AuthorRole? Role { get; }

    /// <summary>
    /// Name of the author of the message. Name is required if the role is 'function'.
    /// </summary>
    public string? Name { get; }

    /// <summary>
    /// Create a new instance of the <see cref="StreamingChatContent"/> class.
    /// </summary>
    /// <param name="chatMessage">Internal Azure SDK Message update representation</param>
    /// <param name="resultIndex">Index of the choice</param>
    /// <param name="metadata">Additional metadata</param>
    public StreamingChatContent(Azure.AI.OpenAI.ChatMessage chatMessage, int resultIndex, Dictionary<string, object> metadata) : base(chatMessage, metadata)
    {
        this.ChoiceIndex = resultIndex;
        this.FunctionCall = chatMessage.FunctionCall;
        this.Content = chatMessage.Content;
        this.Role = new AuthorRole(chatMessage.Role.ToString());
        this.Name = chatMessage.FunctionCall?.Name;
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray() => Encoding.UTF8.GetBytes(this.ToString());

    /// <inheritdoc/>
    public override string ToString() => this.Content ?? string.Empty;
}
