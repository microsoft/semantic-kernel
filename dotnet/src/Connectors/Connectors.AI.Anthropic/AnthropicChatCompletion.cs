// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.Anthropic;

/// <summary>
/// A chat completion connector for the Anthropic API.
/// </summary>
public class AnthropicChatCompletion : IChatCompletion, ITextCompletion, IDisposable
{
    private const string BaseUrl = "https://api.anthropic.com/v1/complete";
    private const int BufferSize = 4096;

    private readonly ILogger? _log;
    private readonly HttpClient _httpClient;
    private readonly bool _disposeHttpClient;
    private readonly string _model;
    private readonly string _apiKey;
    private bool _disposed = false;

    /// <summary>
    /// Initializes a new instance of the <see cref="AnthropicChatCompletion"/> class.
    /// </summary>
    /// <param name="modelId">The ID of the Anthropic model to use for chat completion.</param>
    /// <param name="apiKey">The API key to use for authentication with the Anthropic API.</param>
    /// <param name="httpClient">The <see cref="HttpClient"/> instance to use for making HTTP requests to the Anthropic API.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> instance to use for logging.</param>
    public AnthropicChatCompletion(string modelId, string apiKey, HttpClient? httpClient = null, ILoggerFactory? loggerFactory = null)
    {
        this._httpClient = httpClient ?? new HttpClient();
        this._disposeHttpClient = httpClient == null;
        this._model = modelId;
        this._apiKey = apiKey;
        this._log = loggerFactory?.CreateLogger<AnthropicChatCompletion>();
    }

    private HttpRequestMessage CreateHttpRequest(AnthropicRequest request)
    {
        var json = JsonSerializer.Serialize(request);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        var httpRequest = new HttpRequestMessage(HttpMethod.Post, BaseUrl)
        {
            Content = content
        };
        httpRequest.Headers.Add("x-api-key", this._apiKey);
        return httpRequest;
    }

    private async Task<HttpResponseMessage> SendAsync(AnthropicRequest request, CancellationToken cancellationToken)
    {
        using var httpRequest = this.CreateHttpRequest(request);
        try
        {
            return await this._httpClient.SendWithSuccessCheckAsync(httpRequest, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e) when (!string.IsNullOrWhiteSpace(e.ResponseContent))
        {
            this._log?.LogError(e, "Error sending request to Anthropic API: {Error}", e.ResponseContent);
            var error = JsonSerializer.Deserialize<AnthropicError>(e.ResponseContent!);
            if (error == null)
            {
                throw;
            }
            throw new HttpOperationException($"Error sending request to Anthropic API: {error.Error.Type} - {error.Error.Message}", e);
        }
    }

    private static string ToPrompt(ChatHistory chat)
    {
        var promptBuilder = new StringBuilder();
        foreach (var message in chat.Messages.Where(message => message.Role == AuthorRole.User || message.Role == AuthorRole.Assistant))
        {
            promptBuilder.AppendLine();
            promptBuilder.AppendLine();
            promptBuilder.Append(message.Role == AuthorRole.User ? "Human: " : "Assistant: ");
            promptBuilder.AppendLine(message.Content);
        }

        if (chat.Messages.Count > 0 && chat.Messages.Last().Role != AuthorRole.Assistant)
        {
            promptBuilder.AppendLine();
            promptBuilder.AppendLine();
            promptBuilder.Append("Assistant: ");
        }

        return promptBuilder.ToString();
    }

    private static string ToPrompt(string text)
    {
        var promptBuilder = new StringBuilder();
        promptBuilder.AppendLine();
        promptBuilder.AppendLine();
        promptBuilder.Append("Human: ");
        promptBuilder.AppendLine(text);
        promptBuilder.AppendLine();
        promptBuilder.AppendLine();
        promptBuilder.Append("Assistant: ");
        return promptBuilder.ToString();
    }

    private async Task<HttpResponseMessage> SendAsync(string prompt, bool stream, AIRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
    {
        requestSettings ??= new AnthropicRequestSettings();
        if (requestSettings is not AnthropicRequestSettings settings)
        {
            throw new ArgumentException("Request settings must be an instance of AnthropicRequestSettings",
                nameof(requestSettings));
        }

        var request = new AnthropicRequest(settings, this._model, prompt, stream);
        return await this.SendAsync(request, cancellationToken).ConfigureAwait(false);
    }

    private async Task<IEnumerable<ChatResult>> InternalGetCompletionsAsync(string prompt, AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        using var httpResponse = await this.SendAsync(prompt, false, requestSettings, cancellationToken).ConfigureAwait(false);
        var content = await httpResponse.Content.ReadAsStringAsync().ConfigureAwait(false);
        var response = JsonSerializer.Deserialize<AnthropicResponse>(content) ?? throw new HttpOperationException($"Error deserializing response from Anthropic API: {content}");
        if (response.StopReason == "max_tokens")
        {
            this._log?.LogWarning("Claude stopped because it reached the max tokens limit");
        }

        return new[] { new ChatResult(response) };
    }

    private async IAsyncEnumerable<ChatResult> InternalGetStreamingCompletionsAsync(string prompt, AIRequestSettings? requestSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using var httpResponse = await this.SendAsync(prompt, true, requestSettings, cancellationToken).ConfigureAwait(false);
        var stream = await httpResponse.Content.ReadAsStreamAsync().ConfigureAwait(false);
        using var reader = new StreamReader(stream);

        var buffer = new char[BufferSize];

        while (!reader.EndOfStream)
        {
            var readCount = await reader.ReadAsync(buffer, 0, BufferSize).ConfigureAwait(false);
            var content = new string(buffer, 0, readCount);
            var response = JsonSerializer.Deserialize<AnthropicResponse>(content) ?? throw new HttpOperationException($"Error deserializing response from Anthropic API: {content}");
            yield return new ChatResult(response);
        }
    }

    /// <inheritdoc/>
    public ChatHistory CreateNewChat(string? instructions = null)
    {
        // instructions are ignored for Claude
        return new ChatHistory();
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(ChatHistory chat, AIRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
    {
        if (chat == null)
        {
            throw new ArgumentNullException(nameof(chat));
        }

        return (await this.InternalGetCompletionsAsync(ToPrompt(chat), requestSettings, cancellationToken).ConfigureAwait(false))
            .Cast<IChatResult>()
            .ToList();
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(ChatHistory chat, AIRequestSettings? requestSettings = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (chat == null)
        {
            throw new ArgumentNullException(nameof(chat));
        }

        await foreach (var result in this.InternalGetStreamingCompletionsAsync(ToPrompt(chat), requestSettings, cancellationToken).ConfigureAwait(false))
        {
            yield return result;
        }
    }

    /// <summary>
    /// Releases the unmanaged resources used by the AnthropicChatCompletion and optionally releases the managed resources.
    /// </summary>
    /// <param name="disposing">true to release both managed and unmanaged resources; false to release only unmanaged resources.</param>
    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposed)
        {
            if (disposing)
            {
                // Dispose managed resources here
                this._httpClient.Dispose();
            }

            // Dispose unmanaged resources here
        }

        this._disposed = true;
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(string text, AIRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            throw new ArgumentNullException(nameof(text));
        }

        return (await this.InternalGetCompletionsAsync(ToPrompt(text), requestSettings, cancellationToken).ConfigureAwait(false))
            .Cast<ITextResult>()
            .ToList();
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(string text, AIRequestSettings? requestSettings = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            throw new ArgumentNullException(nameof(text));
        }

        await foreach (var result in this.InternalGetStreamingCompletionsAsync(ToPrompt(text), requestSettings, cancellationToken).ConfigureAwait(false))
        {
            yield return result;
        }
    }
}
