// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Streaming chat result update.
/// </summary>
public sealed class OpenAIStreamingChatContent : StreamingChatContent
{
    /// <summary>
    /// Text associated to the message payload
    /// </summary>
    public override string? Content { get; protected set; }

    /// <summary>
    /// Role of the author of the message
    /// </summary>
    public override AuthorRole? Role { get; protected set; }

    /// <summary>
    /// Name of the author of the message. Name is required if the role is 'function'.
    /// </summary>
    public string? Name { get; }

    /// <summary>
    /// Function name to be called
    /// </summary>
    public override string FunctionName { get; protected set; }

    /// <summary>
    /// Function arguments fragment associated with this chunk
    /// </summary>
    public override string FunctionArgument { get; protected set; }

    /// <summary>
    /// Create a new instance of the <see cref="OpenAIStreamingChatContent"/> class.
    /// </summary>
    /// <param name="chatUpdate">Internal Azure SDK Message update representation</param>
    /// <param name="choiceIndex">Index of the choice</param>
    /// <param name="metadata">Additional metadata</param>
    public OpenAIStreamingChatContent(StreamingChatCompletionsUpdate chatUpdate, int choiceIndex, Dictionary<string, object> metadata) : base(chatUpdate, choiceIndex, metadata)
    {
        this.FunctionName = chatUpdate.FunctionName;
        this.FunctionArgument = chatUpdate.FunctionArgumentsUpdate;
        this.Content = chatUpdate.ContentUpdate;
        if (chatUpdate.Role.HasValue)
        {
            this.Role = new AuthorRole(chatUpdate.Role.ToString());
        }
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray() => Encoding.UTF8.GetBytes(this.ToString());

    /// <inheritdoc/>
    public override string ToString() => this.Content ?? string.Empty;

    /// <summary>
    /// Retrieve the resulting function from the chat result.
    /// </summary>
    /// <param name="fullContent"></param>
    /// <returns>The <see cref="OpenAIFunctionResponse"/>, or null if no function was returned by the model.</returns>
    public static OpenAIFunctionResponse? GetOpenAIStreamingFunctionResponse(IEnumerable<OpenAIStreamingChatContent> fullContent)
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
