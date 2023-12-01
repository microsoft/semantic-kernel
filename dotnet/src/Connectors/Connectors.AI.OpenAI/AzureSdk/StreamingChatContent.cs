// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI;

/// <summary>
/// Streaming chat result update.
/// </summary>
public class StreamingChatContent : StreamingContent
{
    /// <inheritdoc/>
    public override int ChoiceIndex { get; }

    /// <summary>
    /// Gets the name of the function to be called
    /// </summary>
    public string FunctionName { get; }

    /// <summary>
    /// Gets a function arguments fragment associated with this chunk
    /// </summary>
    public string FunctionArgumentUpdate { get; }

    /// <summary>
    /// Text associated to the message payload
    /// </summary>
    public string? ContentUpdate { get; }

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
    /// <param name="chatUpdate">Internal Azure SDK Message update representation</param>
    /// <param name="resultIndex">Index of the choice</param>
    /// <param name="metadata">Additional metadata</param>
    public StreamingChatContent(StreamingChatCompletionsUpdate chatUpdate, int resultIndex, Dictionary<string, object> metadata) : base(chatUpdate, metadata)
    {
        this.ChoiceIndex = resultIndex;
        this.FunctionName = chatUpdate.FunctionName;
        this.FunctionArgumentUpdate = chatUpdate.FunctionArgumentsUpdate;
        this.ContentUpdate = chatUpdate.ContentUpdate;
        if (chatUpdate.Role.HasValue)
        {
            this.Role = new AuthorRole(chatUpdate.Role.ToString());
        }
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray() => Encoding.UTF8.GetBytes(this.ToString());

    /// <inheritdoc/>
    public override string ToString() => this.ContentUpdate ?? string.Empty;

    /// <summary>
    /// Retrieve the resulting function from the chat result.
    /// </summary>
    /// <param name="fullContent"></param>
    /// <returns>The <see cref="OpenAIFunctionResponse"/>, or null if no function was returned by the model.</returns>
    public static OpenAIFunctionResponse? GetOpenAIStreamingFunctionResponse(IEnumerable<StreamingChatContent> fullContent)
    {
        StringBuilder arguments = new();
        string? functionName = null;
        foreach (var message in fullContent)
        {
            functionName ??= message.FunctionName;

            if (message?.FunctionArgumentUpdate is not null)
            {
                arguments.Append(message.FunctionArgumentUpdate);
            }
        }

        if (functionName is null)
        {
            return null;
        }

        return OpenAIFunctionResponse.FromFunctionCall(new FunctionCall(functionName, arguments.ToString()));
    }
}
