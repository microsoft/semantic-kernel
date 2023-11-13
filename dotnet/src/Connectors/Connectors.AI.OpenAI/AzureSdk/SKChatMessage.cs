// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Chat message representation from Semantic Kernel ChatMessageBase Abstraction
/// </summary>
public class SKChatMessage : ChatMessageBase
{
    /// <summary>
    /// Key for the function call arguments in the additional properties dictionary
    /// </summary>
    public const string FunctionCallArgumentsKey = $"{nameof(ChatMessage.FunctionCall)}.{nameof(ChatMessage.FunctionCall.Arguments)}";

    /// <summary>
    /// Key for the function call name in the additional properties dictionary
    /// </summary>
    public const string FunctionCallNameKey = $"{nameof(ChatMessage.FunctionCall)}.{nameof(ChatMessage.FunctionCall.Name)}";

    private readonly ChatMessage? _message;

    /// <summary>
    /// Initializes a new instance of the <see cref="SKChatMessage"/> class.
    /// </summary>
    /// <param name="message">OpenAI SDK chat message representation</param>
    public SKChatMessage(Azure.AI.OpenAI.ChatMessage message)
        : base(new AuthorRole(message.Role.ToString()), message.Content)
    {
        if (message.Name is not null)
        {
            this.AdditionalProperties![nameof(message.Name)] = message.Name;
        }

        if (message.FunctionCall?.Name is not null)
        {
            this.AdditionalProperties![FunctionCallNameKey] = message.FunctionCall.Name;
        }

        if (message.FunctionCall?.Arguments is not null)
        {
            this.AdditionalProperties![FunctionCallArgumentsKey] = message.FunctionCall.Arguments;
        }

        this._message = message;
        this.FunctionCall = message.FunctionCall;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="SKChatMessage"/> class.
    /// </summary>
    /// <param name="role">Role of the author of the message.</param>
    /// <param name="content">Content of the message.</param>
    public SKChatMessage(string role, string content)
        : base(new AuthorRole(role), content)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="SKChatMessage"/> class.
    /// </summary>
    /// <param name="role">Role of the author of the message.</param>
    /// <param name="content">Content of the message.</param>
    /// <param name="arguments">Arguments of the message.</param>
    public SKChatMessage(string role, string content, Dictionary<string, string> arguments)
        : base(new AuthorRole(role), content, arguments)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="SKChatMessage"/> class.
    /// </summary>
    /// <param name="role">Role of the author of the message.</param>
    /// <param name="content">Content of the message.</param>
    /// <param name="functionCall">Function call definition.</param>
    /// <param name="arguments">Arguments of the message.</param>
    public SKChatMessage(string role, string content, FunctionCall? functionCall, Dictionary<string, string> arguments)
        : base(new AuthorRole(role), content, arguments)
    {
        this.FunctionCall = functionCall;
    }

    /// <summary>
    /// Exposes the underlying OpenAI SDK function call chat message representation
    /// </summary>
    public FunctionCall? FunctionCall { get; set; }
}
