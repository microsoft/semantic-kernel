// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using Anthropic;
using Anthropic.Core;
using Anthropic.Exceptions;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic.Core.Extensions;
using Microsoft.SemanticKernel.Connectors.FunctionCalling;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// Core implementation for Anthropic API interactions.
/// Uses the official Anthropic C# SDK with custom header handling for Azure-hosted endpoints.
/// Follows Semantic Kernel's ClientCore pattern for consistency.
/// </summary>
#pragma warning disable SKEXP0001 // ModelDiagnostics is experimental in SK
internal partial class AnthropicClientCore
{
    #region Private Constants and Fields

    /// <summary>
    /// Default max tokens if not specified.
    /// </summary>
    /// <remarks>
    /// Anthropic requires explicit MaxTokens. This high default ensures we don't unnecessarily limit responses.
    /// The Anthropic SDK will automatically clamp this to the model's actual maximum output token limit.
    /// </remarks>
    private const int DefaultMaxTokens = 32000;

    /// <summary>
    /// Instance of <see cref="Meter"/> for metrics.
    /// </summary>
    private static readonly Meter s_meter = new("Microsoft.SemanticKernel.Connectors.Anthropic");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of prompt tokens used.
    /// </summary>
    internal static readonly Counter<int> s_promptTokensCounter = s_meter.CreateCounter<int>(
        name: "semantic_kernel.connectors.anthropic.tokens.prompt",
        unit: "{token}",
        description: "Number of prompt tokens used");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of completion tokens used.
    /// </summary>
    internal static readonly Counter<int> s_completionTokensCounter = s_meter.CreateCounter<int>(
        name: "semantic_kernel.connectors.anthropic.tokens.completion",
        unit: "{token}",
        description: "Number of completion tokens used");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the total number of tokens used.
    /// </summary>
    internal static readonly Counter<int> s_totalTokensCounter = s_meter.CreateCounter<int>(
        name: "semantic_kernel.connectors.anthropic.tokens.total",
        unit: "{token}",
        description: "Number of tokens used");

    #endregion

    #region Properties

    /// <summary>
    /// Identifier of the model to use.
    /// </summary>
    protected internal string ModelId { get; init; } = string.Empty;

    /// <summary>
    /// Logger instance.
    /// </summary>
    protected internal ILogger? Logger { get; init; }

    /// <summary>
    /// Anthropic SDK client.
    /// </summary>
    protected internal AnthropicClient Client { get; init; } = null!;

    /// <summary>
    /// Optional endpoint identifier for telemetry.
    /// </summary>
    protected internal string? EndpointId { get; init; }

    /// <summary>
    /// Base URL for the API endpoint.
    /// </summary>
    protected internal Uri BaseUrl { get; init; } = null!;

    /// <summary>
    /// Storage for AI service attributes.
    /// </summary>
    internal Dictionary<string, object?> Attributes { get; } = [];

    /// <summary>
    /// The function calls processor for auto-invocation with SK filters and concurrent execution.
    /// Initialized by partial method InitializeFunctionCallsProcessor() in ChatCompletion partial class.
    /// </summary>
    protected FunctionCallsProcessor FunctionCallsProcessor { get; private set; } = null!;

    #endregion

    #region Constructors

    /// <summary>
    /// Initializes a new instance of the <see cref="AnthropicClientCore"/> class.
    /// </summary>
    /// <param name="modelId">Model name (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="apiKey">API Key for authentication.</param>
    /// <param name="baseUrl">Base URL for the API endpoint.</param>
    /// <param name="endpointId">Optional endpoint identifier for telemetry.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILogger"/> to use for logging. If null, no logging will be performed.</param>
    internal AnthropicClientCore(
        string modelId,
        string apiKey,
        Uri baseUrl,
        string? endpointId = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);
        Verify.NotNull(baseUrl);

        this.Logger = logger ?? NullLogger.Instance;
        this.ModelId = modelId;
        this.EndpointId = endpointId;
        this.BaseUrl = baseUrl;

        this.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
        this.AddAttribute(AIServiceExtensions.EndpointKey, baseUrl.ToString());

        // Create Anthropic client with custom configuration
        this.Client = CreateAnthropicClient(apiKey, baseUrl, httpClient);

        // Initialize function calls processor for parallel tool execution
        this.InitializeFunctionCallsProcessor();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AnthropicClientCore"/> class using an existing AnthropicClient.
    /// </summary>
    /// <param name="modelId">Model name (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="anthropicClient">Pre-configured <see cref="AnthropicClient"/>.</param>
    /// <param name="logger">The <see cref="ILogger"/> to use for logging. If null, no logging will be performed.</param>
    /// <remarks>
    /// Note: Instances created this way might not have the default diagnostics settings.
    /// It's up to the caller to configure the client appropriately.
    /// </remarks>
    internal AnthropicClientCore(
        string modelId,
        AnthropicClient anthropicClient,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(anthropicClient);

        this.Logger = logger ?? NullLogger.Instance;
        this.ModelId = modelId;
        this.Client = anthropicClient;
        this.BaseUrl = new Uri("https://api.anthropic.com");

        this.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
        this.AddAttribute(AIServiceExtensions.EndpointKey, this.BaseUrl.ToString());

        // Initialize function calls processor for parallel tool execution
        this.InitializeFunctionCallsProcessor();
    }

    #endregion

    #region Private Methods

    /// <summary>
    /// Creates an Anthropic client with custom header handling for Azure-hosted endpoints.
    /// Azure uses 'api-key' header instead of SDK's default 'X-Api-Key'.
    /// Also adds Semantic Kernel identification headers for diagnostics.
    /// </summary>
    /// <remarks>
    /// <para><b>HttpClient Lifecycle:</b></para>
    /// <para>
    /// When <paramref name="httpClient"/> is null, a new HttpClient is created internally.
    /// The Anthropic SDK's <see cref="AnthropicClient"/> takes ownership of the HttpClient
    /// passed via ClientOptions and manages its lifecycle. The HttpClient is NOT disposed
    /// when this class is garbage collected - this is intentional as HttpClient is designed
    /// to be long-lived and reused.
    /// </para>
    /// <para>
    /// For production scenarios with proper resource management, inject an HttpClient via
    /// IHttpClientFactory or DI container. The injected client will then be managed by the
    /// container's lifecycle management.
    /// </para>
    /// </remarks>
    private static AnthropicClient CreateAnthropicClient(string apiKey, Uri baseUrl, HttpClient? httpClient)
    {
        // Create HttpClient if not provided. Note: The Anthropic SDK takes ownership of this client.
        // In production, prefer injecting HttpClient via IHttpClientFactory for proper lifecycle management.
        var client = httpClient ?? new HttpClient();

        // Add Azure-compatible 'api-key' header for Azure-hosted Anthropic endpoints
        // The SDK also sends 'X-Api-Key' via APIKey property, but Azure requires 'api-key'
        if (!client.DefaultRequestHeaders.Contains("api-key"))
        {
            client.DefaultRequestHeaders.Add("api-key", apiKey);
        }

        // Add Semantic Kernel identification headers (following SK connector pattern)
        if (!client.DefaultRequestHeaders.Contains(HttpHeaderConstant.Names.UserAgent))
        {
            client.DefaultRequestHeaders.Add(
                HttpHeaderConstant.Names.UserAgent,
                HttpHeaderConstant.Values.UserAgent);
        }
        if (!client.DefaultRequestHeaders.Contains(HttpHeaderConstant.Names.SemanticKernelVersion))
        {
            client.DefaultRequestHeaders.Add(
                HttpHeaderConstant.Names.SemanticKernelVersion,
                HttpHeaderConstant.Values.GetAssemblyVersion(typeof(AnthropicClientCore)));
        }

        var options = new ClientOptions
        {
            BaseUrl = baseUrl,
            APIKey = apiKey,
            HttpClient = client
        };

        return new AnthropicClient(options);
    }

    #endregion

    #region Internal Methods

    /// <summary>
    /// Logs Anthropic action details.
    /// </summary>
    /// <param name="callerMemberName">Caller member name. Populated automatically by runtime.</param>
    internal void LogActionDetails([CallerMemberName] string? callerMemberName = default)
    {
        if (this.Logger!.IsEnabled(LogLevel.Debug))
        {
            this.Logger.LogDebug("Action: {Action}. Anthropic Model ID: {ModelId}.", callerMemberName, this.ModelId);
        }
    }

    /// <summary>
    /// Allows adding attributes to the client.
    /// </summary>
    /// <param name="key">Attribute key.</param>
    /// <param name="value">Attribute value.</param>
    internal void AddAttribute(string key, string? value)
    {
        if (!string.IsNullOrEmpty(value))
        {
            this.Attributes.Add(key, value);
        }
    }

    #endregion

    #region Protected Methods

    /// <summary>
    /// Gets the model identifier to use for the client.
    /// </summary>
    protected virtual string GetClientModelId()
        => this.ModelId;

    /// <summary>
    /// Starts a chat completion activity for telemetry tracking using SK's ModelDiagnostics.
    /// </summary>
    /// <param name="chatHistory">Chat history.</param>
    /// <param name="executionSettings">Execution settings.</param>
    /// <returns>Activity instance or null if telemetry is disabled.</returns>
    protected virtual Activity? StartChatCompletionActivity(ChatHistory chatHistory, PromptExecutionSettings? executionSettings)
    {
        // Use SK's ModelDiagnostics for OTel semantic conventions compliance
        return ModelDiagnostics.StartCompletionActivity(
            this.BaseUrl,
            this.ModelId,
            "anthropic",
            chatHistory,
            executionSettings as AnthropicPromptExecutionSettings);
    }

    /// <summary>
    /// Sets completion response information on the activity using SK's ModelDiagnostics.
    /// </summary>
    /// <param name="activity">Activity to update.</param>
    /// <param name="chatMessages">Chat message responses.</param>
    /// <param name="promptTokens">Number of prompt tokens.</param>
    /// <param name="completionTokens">Number of completion tokens.</param>
    /// <remarks>
    /// ModelDiagnostics extracts finish reason from ChatMessageContent.Metadata["FinishReason"].
    /// Token counts are cast from long to int - SK's ModelDiagnostics API uses int which covers
    /// most practical cases (up to 2.1B tokens per request).
    /// </remarks>
    protected virtual void SetCompletionResponse(Activity? activity, IReadOnlyList<ChatMessageContent> chatMessages,
        long? promptTokens = null, long? completionTokens = null)
    {
        if (activity == null)
        {
            return;
        }

        // Use SK's ModelDiagnostics extension method for OTel semantic conventions compliance
        activity.SetCompletionResponse(
            chatMessages,
            promptTokens: (int?)promptTokens,
            completionTokens: (int?)completionTokens);
    }

    /// <summary>
    /// Records token usage metrics.
    /// </summary>
    /// <param name="inputTokens">Number of input tokens.</param>
    /// <param name="outputTokens">Number of output tokens.</param>
    protected void RecordTokenUsageMetrics(int inputTokens, int outputTokens)
    {
        var tags = new TagList { { "model_id", this.ModelId } };

        if (!string.IsNullOrEmpty(this.EndpointId))
        {
            tags.Add("endpoint_id", this.EndpointId);
        }

        if (inputTokens > 0)
        {
            s_promptTokensCounter.Add(inputTokens, tags);
        }

        if (outputTokens > 0)
        {
            s_completionTokensCounter.Add(outputTokens, tags);
        }

        var totalTokens = inputTokens + outputTokens;
        if (totalTokens > 0)
        {
            s_totalTokensCounter.Add(totalTokens, tags);
        }
    }

    /// <summary>
    /// Invokes the specified request and handles exceptions.
    /// Converts Anthropic SDK exceptions to SK's HttpOperationException for consistency.
    /// </summary>
    /// <typeparam name="T">Type of the response.</typeparam>
    /// <param name="request">Request to invoke.</param>
    /// <returns>Returns the response.</returns>
    /// <remarks>
    /// Exception handling follows SK's pattern:
    /// - AnthropicApiException → HttpOperationException (with StatusCode and ResponseContent)
    /// - AnthropicIOException → HttpOperationException (I/O errors, no status code)
    /// - TaskCanceledException with TimeoutException → TimeoutException
    /// </remarks>
    protected static async Task<T> RunRequestAsync<T>(Func<Task<T>> request)
    {
        try
        {
            return await request.Invoke().ConfigureAwait(false);
        }
        catch (AnthropicApiException e)
        {
            // Convert Anthropic API exceptions to SK's HttpOperationException
            // This includes all HTTP error responses (400, 401, 403, 404, 422, 429, 5xx)
            throw e.ToHttpOperationException();
        }
        catch (AnthropicIOException e)
        {
            // I/O errors (network connectivity issues) - no status code available
            throw new HttpOperationException(
                statusCode: null,
                responseContent: null,
                message: e.Message,
                innerException: e);
        }
        catch (TaskCanceledException e) when (e.InnerException is TimeoutException)
        {
            throw new TimeoutException("Anthropic API request timed out.", e);
        }
    }

    #endregion

    /// <summary>
    /// Initializes the function calls processor (implemented in ChatCompletion partial class).
    /// </summary>
    partial void InitializeFunctionCallsProcessor();
}
