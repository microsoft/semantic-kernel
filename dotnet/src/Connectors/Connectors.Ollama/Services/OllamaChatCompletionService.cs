// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;
using OllamaSharp;
using OllamaSharp.Models.Chat;
using Microsoft.SemanticKernel.Connectors.Ollama.Core;
using System.Runtime.CompilerServices;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

/// <summary>
/// Represents a chat completion service using Ollama Original API.
/// </summary>
public sealed class OllamaChatCompletionService : IChatCompletionService
{
    private Dictionary<string, object?> AttributesInternal { get; } = new();
    private readonly OllamaApiClient _client;

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaChatCompletionService"/> class.
    /// </summary>
    /// <param name="model">The hosted model.</param>
    /// <param name="baseUri">The base uri including the port where Ollama server is hosted</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the Ollama API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaChatCompletionService(
        string model,
        Uri baseUri,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);

        this._client = (httpClient is null) ? new(baseUri, model) : new(httpClient, model);
        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
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
    {
        Verify.NotNullOrWhiteSpace(model);
        this._client = client;
        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
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

        var last = answer.Last();

        return [new(GetAuthorRole(last.Role) ?? AuthorRole.Assistant, content: last.Content)];
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
            yield return new StreamingChatMessageContent(GetAuthorRole(message?.Message.Role), message?.Message.Content);
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
            Options = new() {
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
