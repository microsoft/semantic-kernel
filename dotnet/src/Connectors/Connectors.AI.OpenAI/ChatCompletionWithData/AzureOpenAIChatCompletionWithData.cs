// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Prompts;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

/// <summary>
/// Azure OpenAI Chat Completion with data client.
/// More information: <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/use-your-data-quickstart"/>
/// </summary>
public sealed class AzureOpenAIChatCompletionWithData : IChatCompletion, ITextCompletion
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIChatCompletionWithData"/> class.
    /// </summary>
    /// <param name="config">Instance of <see cref="AzureOpenAIChatCompletionWithDataConfig"/> class with completion configuration.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">Instance of <see cref="ILoggerFactory"/> to use for logging.</param>
    public AzureOpenAIChatCompletionWithData(
        AzureOpenAIChatCompletionWithDataConfig config,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        this.ValidateConfig(config);

        this._config = config;

        this._httpClient = HttpClientProvider.GetHttpClient(httpClient);
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(this.GetType()) : NullLogger.Instance;
        this._attributes.Add(AIServiceExtensions.ModelIdKey, config.CompletionModelId);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <inheritdoc/>
    public ChatHistory CreateNewChat(string? instructions = null)
        => InternalCreateNewChat(instructions);

    /// <inheritdoc/>
    public async Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        ChatHistory chat,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chat);

        OpenAIPromptExecutionSettings chatRequestSettings = OpenAIPromptExecutionSettings.FromRequestSettingsWithData(executionSettings);

        ValidateMaxTokens(chatRequestSettings.MaxTokens);

        return await this.ExecuteCompletionRequestAsync(chat, kernel, chatRequestSettings, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        OpenAIPromptExecutionSettings chatExecutionSettings = OpenAIPromptExecutionSettings.FromRequestSettingsWithData(executionSettings);

        var chat = InternalCreateNewChat(prompt, chatExecutionSettings);

        return (await this.GetChatCompletionsAsync(chat, chatExecutionSettings, kernel, cancellationToken).ConfigureAwait(false))
            .ToList();
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        OpenAIPromptExecutionSettings chatExecutionSettings = OpenAIPromptExecutionSettings.FromRequestSettingsWithData(executionSettings);

        var chat = InternalCreateNewChat(prompt, chatExecutionSettings);

        return (await this.GetChatCompletionsAsync(chat, chatExecutionSettings, kernel, cancellationToken).ConfigureAwait(false))
            .OfType<ITextResult>()
            .ToList();
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<T> GetStreamingContentAsync<T>(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        OpenAIPromptExecutionSettings chatExecutionSettings = OpenAIPromptExecutionSettings.FromRequestSettingsWithData(executionSettings);

        var chat = InternalCreateNewChat(prompt, chatExecutionSettings);

        return this.GetStreamingContentAsync<T>(chat, chatExecutionSettings, kernel, cancellationToken);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<T> GetStreamingContentAsync<T>(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        OpenAIPromptExecutionSettings chatRequestSettings = OpenAIPromptExecutionSettings.FromRequestSettingsWithData(executionSettings);

        using var request = this.GetRequest(chatHistory, chatRequestSettings, isStreamEnabled: true);
        using var response = await this.SendRequestAsync(request, cancellationToken).ConfigureAwait(false);

        await foreach (var result in this.GetChatStreamingUpdatesAsync<T>(response))
        {
            yield return result;
        }
    }

    #region private ================================================================================

    private const string DefaultApiVersion = "2023-06-01-preview";

    private readonly AzureOpenAIChatCompletionWithDataConfig _config;

    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;
    private readonly Dictionary<string, object?> _attributes = new();
    private void ValidateConfig(AzureOpenAIChatCompletionWithDataConfig config)
    {
        Verify.NotNull(config);

        Verify.NotNullOrWhiteSpace(config.CompletionModelId);
        Verify.NotNullOrWhiteSpace(config.CompletionEndpoint);
        Verify.NotNullOrWhiteSpace(config.CompletionApiKey);
        Verify.NotNullOrWhiteSpace(config.DataSourceEndpoint);
        Verify.NotNullOrWhiteSpace(config.DataSourceApiKey);
        Verify.NotNullOrWhiteSpace(config.DataSourceIndex);
    }

    private static void ValidateMaxTokens(int? maxTokens)
    {
        if (maxTokens.HasValue && maxTokens < 1)
        {
            throw new KernelException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
        }
    }

    private async Task<IReadOnlyList<IChatResult>> ExecuteCompletionRequestAsync(
        ChatHistory chat,
        Kernel? kernel,
        OpenAIPromptExecutionSettings executionSettings,
        CancellationToken cancellationToken = default)
    {
        using var request = this.GetRequest(chat, executionSettings, isStreamEnabled: false);
        using var response = await this.SendRequestAsync(request, cancellationToken).ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        var chatWithDataResponse = this.DeserializeResponse<ChatWithDataResponse>(body);

        return chatWithDataResponse.Choices.Select(choice => new ChatWithDataResult(chatWithDataResponse, choice)).ToList();
    }

    private async Task<HttpResponseMessage> SendRequestAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken = default)
    {
        request.Headers.Add("User-Agent", HttpHeaderValues.UserAgent);
        request.Headers.Add("Api-Key", this._config.CompletionApiKey);

        try
        {
            return await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException ex)
        {
            this._logger.LogError(
                "Error occurred on chat completion with data request execution: {ExceptionMessage}", ex.Message);

            throw;
        }
    }

    private async IAsyncEnumerable<T> GetChatStreamingUpdatesAsync<T>(HttpResponseMessage response)
    {
        const string ServerEventPayloadPrefix = "data:";

        using var stream = await response.Content.ReadAsStreamAndTranslateExceptionAsync().ConfigureAwait(false);
        using var reader = new StreamReader(stream);

        while (!reader.EndOfStream)
        {
            var body = await reader.ReadLineAsync().ConfigureAwait(false);

            if (string.IsNullOrWhiteSpace(body))
            {
                continue;
            }

            if (body.StartsWith(ServerEventPayloadPrefix, StringComparison.Ordinal))
            {
                body = body.Substring(ServerEventPayloadPrefix.Length);
            }

            var chatWithDataResponse = this.DeserializeResponse<ChatWithDataStreamingResponse>(body);
            var responseMetadata = this.GetResponseMetadata(response);
            foreach (var choice in chatWithDataResponse.Choices)
            {
                // If the provided T is an specialized class of StreamingContent interface
                if (typeof(T) == typeof(StreamingChatContent) ||
                    typeof(T) == typeof(StreamingContent))
                {
                    yield return (T)(object)new StreamingChatWithDataContent(choice, choice.Index, responseMetadata);
                    continue;
                }

                var result = new ChatWithDataStreamingResult(chatWithDataResponse, choice);
                if (typeof(T) == typeof(string))
                {
                    await foreach (SemanticKernel.AI.ChatCompletion.ChatMessage message in result.GetStreamingChatMessageAsync().ConfigureAwait(false))
                    {
                        yield return (T)(object)message.Content;
                    }
                    continue;
                }

                if (typeof(T) == typeof(ChatWithDataStreamingResult))
                {
                    yield return (T)(object)result;
                    continue;
                }

                throw new NotSupportedException($"Type {typeof(T)} is not supported");
            }
        }
    }

    private Dictionary<string, object> GetResponseMetadata(HttpResponseMessage response)
    {
        return new Dictionary<string, object>()
        {
            { nameof(HttpResponseMessage), response },
        };
    }

    private T DeserializeResponse<T>(string body)
    {
        var response = JsonSerializer.Deserialize<T>(body, JsonOptionsCache.ReadPermissive);

        if (response is null)
        {
            const string ErrorMessage = "Error occurred on chat completion with data response deserialization";

            this._logger.LogError(ErrorMessage);

            throw new KernelException(ErrorMessage);
        }

        return response;
    }

    private HttpRequestMessage GetRequest(
        ChatHistory chat,
        OpenAIPromptExecutionSettings executionSettings,
        bool isStreamEnabled)
    {
        var payload = new ChatWithDataRequest
        {
            Temperature = executionSettings.Temperature,
            TopP = executionSettings.TopP,
            IsStreamEnabled = isStreamEnabled,
            StopSequences = executionSettings.StopSequences,
            MaxTokens = executionSettings.MaxTokens,
            PresencePenalty = executionSettings.PresencePenalty,
            FrequencyPenalty = executionSettings.FrequencyPenalty,
            TokenSelectionBiases = executionSettings.TokenSelectionBiases,
            DataSources = this.GetDataSources(),
            Messages = this.GetMessages(chat)
        };

        return HttpRequest.CreatePostRequest(this.GetRequestUri(), payload);
    }

    private List<ChatWithDataSource> GetDataSources()
    {
        return new List<ChatWithDataSource>
        {
            new() {
                Parameters = new ChatWithDataSourceParameters
                {
                    Endpoint = this._config.DataSourceEndpoint,
                    ApiKey = this._config.DataSourceApiKey,
                    IndexName = this._config.DataSourceIndex
                }
            }
        };
    }

    private List<ChatWithDataMessage> GetMessages(ChatHistory chat)
    {
        return chat
            .Select(message => new ChatWithDataMessage
            {
                Role = message.Role.Label,
                Content = message.Content
            })
            .ToList();
    }

    /// <summary>
    /// Create a new empty chat instance
    /// </summary>
    /// <param name="text">Optional chat instructions for the AI service</param>
    /// <param name="executionSettings">Execution settings</param>
    /// <returns>Chat object</returns>
    private static OpenAIChatHistory InternalCreateNewChat(string? text = null, OpenAIPromptExecutionSettings? executionSettings = null)
    {
        // If text is not provided, create an empty chat with the system prompt if provided
        if (string.IsNullOrWhiteSpace(text))
        {
            return new OpenAIChatHistory(executionSettings?.ChatSystemPrompt);
        }

        // Try to parse the text as a chat history
        if (XmlPromptParser.TryParse(text!, out var nodes) && ChatPromptParser.TryParse(nodes, out var chatHistory))
        {
            return new OpenAIChatHistory(chatHistory);
        }

        // If settings is not provided, create a new chat with the text as the system prompt
        var chat = new OpenAIChatHistory(executionSettings?.ChatSystemPrompt ?? text);
        if (executionSettings is not null)
        {
            // If settings is provided, add the prompt as the user message
            chat.AddUserMessage(text!);
        }

        return chat;
    }

    private string GetRequestUri()
    {
        const string EndpointUriFormat = "{0}/openai/deployments/{1}/extensions/chat/completions?api-version={2}";

        var apiVersion = this._config.CompletionApiVersion;

        if (string.IsNullOrWhiteSpace(apiVersion))
        {
            apiVersion = DefaultApiVersion;
        }

        return string.Format(
            CultureInfo.InvariantCulture,
            EndpointUriFormat,
            this._config.CompletionEndpoint.TrimEnd('/'),
            this._config.CompletionModelId,
            apiVersion);
    }

    #endregion
}
