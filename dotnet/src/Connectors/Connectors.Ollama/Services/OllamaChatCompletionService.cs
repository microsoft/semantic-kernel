// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Ollama.Core;
using OllamaSharp;
using OllamaSharp.Models.Chat;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

/// <summary>
/// Represents a chat completion service using Ollama Original API.
/// </summary>
public sealed class OllamaChatCompletionService : ServiceBase, IChatCompletionService
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaChatCompletionService"/> class.
    /// </summary>
    /// <param name="model">The hosted model.</param>
    /// <param name="endpoint">The endpoint including the port where Ollama server is hosted</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the Ollama API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaChatCompletionService(
        string model,
        Uri endpoint,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
        : base(model, endpoint, httpClient, loggerFactory)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaChatCompletionService"/> class.
    /// </summary>
    /// <param name="model">The hosted model.</param>
    /// <param name="client">The Ollama API client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaChatCompletionService(
        string model,
        OllamaApiClient client,
        ILoggerFactory? loggerFactory = null)
        : base(model, client, loggerFactory)
    {
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <inheritdoc />
    public async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var settings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);
        var request = CreateChatRequest(chatHistory, settings, this._client.SelectedModel);

        var answer = await this._client.SendChat(request, _ => { }, cancellationToken).ConfigureAwait(false);

        // Ollama Client gives back the same requested history with added message at the end
        // To be compatible with this API behavior, we only return the added message (last).
        var message = answer.Last();

        return [new ChatMessageContent(
            role: GetAuthorRole(message.Role) ?? AuthorRole.Assistant,
            content: message.Content,
            modelId: this._client.SelectedModel,
            innerContent: message)]; // Currently the Ollama Message does not provide any metadata
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var settings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);
        var request = CreateChatRequest(chatHistory, settings, this._client.SelectedModel);

        await foreach (var message in this._client.StreamChat(request, cancellationToken).ConfigureAwait(false))
        {
            yield return new StreamingChatMessageContent(
                GetAuthorRole(message?.Message.Role),
                message?.Message.Content,
                modelId: message?.Model,
                innerContent: message,
                metadata: new OllamaMetadata(message));
        }
    }

    private static AuthorRole? GetAuthorRole(ChatRole? role) => role.ToString().ToUpperInvariant() switch
    {
        "USER" => AuthorRole.User,
        "ASSISTANT" => AuthorRole.Assistant,
        "SYSTEM" => AuthorRole.System,
        _ => null
    };

    private static ChatRequest CreateChatRequest(ChatHistory chatHistory, OllamaPromptExecutionSettings settings, string selectedModel)
    {
        var messages = new List<Message>();
        foreach (var chatHistoryMessage in chatHistory)
        {
            ChatRole role = ChatRole.User;
            if (chatHistoryMessage.Role == AuthorRole.System)
            {
                role = ChatRole.System;
            }
            else if (chatHistoryMessage.Role == AuthorRole.Assistant)
            {
                role = ChatRole.Assistant;
            }

            messages.Add(new Message(role, chatHistoryMessage.Content!));
        }

        var request = new ChatRequest
        {
            Options = new()
            {
                Temperature = settings.Temperature,
                TopP = settings.TopP,
                TopK = settings.TopK,
                Stop = settings.Stop
            },
            Messages = messages.ToList(),
            Model = selectedModel,
            Stream = true
        };
        return request;
    }
}
