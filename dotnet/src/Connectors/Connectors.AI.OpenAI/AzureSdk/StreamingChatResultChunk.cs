// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Streaming chat result update.
/// </summary>
public class StreamingChatResultChunk : StreamingResultChunk
{
    /// <inheritdoc/>
    public override string Type => "openai_chat_message_update";

    /// <inheritdoc/>
    public override int ResultIndex { get; }

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
    /// Create a new instance of the <see cref="StreamingChatResultChunk"/> class.
    /// </summary>
    /// <param name="chatMessage">Original Azure SDK Message update representation</param>
    /// <param name="resultIndex">Index of the choice</param>
    public StreamingChatResultChunk(AzureOpenAIChatMessage chatMessage, int resultIndex)
    {
        this.ResultIndex = resultIndex;
        this.FunctionCall = chatMessage.InnerChatMessage?.FunctionCall;
        this.Content = chatMessage.Content;
        this.Role = new AuthorRole(chatMessage.Role.ToString());
        this.Name = chatMessage.InnerChatMessage?.Name;
    }

    /// <summary>
    /// Create a new instance of the <see cref="StreamingChatResultChunk"/> class.
    /// </summary>
    /// <param name="chatMessage">Original Azure SDK Message update representation</param>
    /// <param name="resultIndex">Index of the choice</param>
    public StreamingChatResultChunk(Azure.AI.OpenAI.ChatMessage chatMessage, int resultIndex)
    {
        this.ResultIndex = resultIndex;
        this.FunctionCall = chatMessage.FunctionCall;
        this.Content = chatMessage.Content;
        this.Role = new AuthorRole(chatMessage.Role.ToString());
        this.Name = chatMessage.FunctionCall?.Name;
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray()
    {
        return Encoding.UTF8.GetBytes(this.ToString());
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return JsonSerializer.Serialize(this);
    }
}
