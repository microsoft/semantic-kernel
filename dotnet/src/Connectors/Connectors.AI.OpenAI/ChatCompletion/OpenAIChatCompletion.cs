// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Reliability;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;

/// <summary>
/// OpenAI chat completion client.
/// TODO: forward ETW logging to ILogger, see https://learn.microsoft.com/en-us/dotnet/azure/sdk/logging
/// </summary>
public sealed class OpenAIChatCompletion : OpenAIClientBase, IChatCompletion, ITextCompletion
{
    /// <summary>
    /// Create an instance of the OpenAI chat completion connector
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="handlerFactory">Retry handler factory for HTTP requests.</param>
    /// <param name="log">Application logger</param>
    public OpenAIChatCompletion(
        string modelId,
        string apiKey,
        string? organization = null,
        IDelegatingHandlerFactory? handlerFactory = null,
        ILogger? log = null
    ) : base(modelId, apiKey, organization, handlerFactory, log)
    {
    }

    /// <inheritdoc/>
    public Task<string> GenerateMessageAsync(
        ChatHistory chat,
        ChatRequestSettings requestSettings,
        CancellationToken cancellationToken = default)
    {
        return this.InternalGenerateChatMessageAsync(chat, requestSettings, cancellationToken);
    }

    /// <inheritdoc/>
    public ChatHistory CreateNewChat(string instructions = "")
    {
        return this.InternalCreateNewChat(instructions);
    }

    /// <inheritdoc/>
    public Task<string> CompleteAsync(
        string text,
        CompleteRequestSettings requestSettings,
        CancellationToken cancellationToken = default)
    {
        return this.InternalCompleteTextUsingChatAsync(text, requestSettings, cancellationToken);
    }
}
