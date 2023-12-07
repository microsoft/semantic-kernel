// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Azure OpenAI and OpenAI Specialized streaming chat message content.
/// </summary>
/// <remarks>
/// Represents a chat message content chunk that was streamed from the remote model.
/// </remarks>
public sealed class OpenAIStreamingChatMessageContent : StreamingChatMessageContent
{
    /// <summary>
    /// Name of the author of the message. Name is required if the role is 'function'.
    /// </summary>
    public string? Name { get; }

    /// <summary>
    /// Function name to be called
    /// </summary>
    public string? FunctionName { get; set; }

    /// <summary>
    /// Function arguments fragment associated with this chunk
    /// </summary>
    public string? FunctionArgument { get; set; }

    /// <summary>
    /// Create a new instance of the <see cref="OpenAIStreamingChatMessageContent"/> class.
    /// </summary>
    /// <param name="chatUpdate">Internal Azure SDK Message update representation</param>
    /// <param name="choiceIndex">Index of the choice</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    internal OpenAIStreamingChatMessageContent(
        StreamingChatCompletionsUpdate chatUpdate,
        int choiceIndex,
        string modelId,
        Dictionary<string, object?>? metadata = null)
        : base(
            chatUpdate.Role.HasValue ? new AuthorRole(chatUpdate.Role.Value.ToString()) : null,
            chatUpdate.ContentUpdate,
            chatUpdate,
            choiceIndex,
            modelId,
            Encoding.UTF8,
            metadata)
    {
        this.FunctionName = chatUpdate.FunctionName;
        this.FunctionArgument = chatUpdate.FunctionArgumentsUpdate;
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray() => this.Encoding.GetBytes(this.ToString());

    /// <inheritdoc/>
    public override string ToString() => this.Content ?? string.Empty;

    /// <summary>
    /// Retrieve the resulting function from the chat result.
    /// </summary>
    /// <param name="fullContent">Full content of the chat</param>
    /// <returns>The <see cref="OpenAIFunctionResponse"/>, or null if no function was returned by the model.</returns>
    public static OpenAIFunctionResponse? GetOpenAIStreamingFunctionResponse(IEnumerable<OpenAIStreamingChatMessageContent> fullContent)
    {
        StringBuilder arguments = new();
        string? functionName = null;
        foreach (var message in fullContent)
        {
            functionName ??= message.FunctionName;

            if (message?.FunctionArgument is not null)
            {
                arguments.Append(message.FunctionArgument);
            }
        }

        if (functionName is null)
        {
            return null;
        }

        return OpenAIFunctionResponse.FromFunctionCall(new FunctionCall(functionName, arguments.ToString()));
    }
}
