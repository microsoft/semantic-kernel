// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Anthropic;
using Anthropic.Core;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Anthropic chat completion service using Microsoft.Extensions.AI (M.E.AI) architecture.
/// </summary>
/// <remarks>
/// <para>
/// Leverages the Anthropic SDK's native <see cref="IChatClient"/> implementation for all LLM communication.
/// All Anthropic-specific features (Extended Thinking, PDFs, Citations, etc.)
/// are handled by the SDK's <see cref="IChatClient"/> implementation.
/// </para>
/// <para>
/// To configure Anthropic-specific generation options (temperature, max tokens, stop sequences, etc.),
/// use <see cref="AnthropicPromptExecutionSettings"/> as the <see cref="PromptExecutionSettings"/> argument.
/// </para>
/// </remarks>
[Experimental("SKEXP0001")]
public sealed class AnthropicChatCompletionService : IChatCompletionService, ITextGenerationService, IDisposable
{
    // Implementation notes (M.E.AI pattern):
    // - Uses SDK's native AsIChatClient() for M.E.AI integration
    // - Uses UseKernelFunctionInvocation() for SK filter pipeline (IAutoFunctionInvocationFilter)
    // - Uses UseOpenTelemetry() for standardized telemetry
    // - Uses AsChatCompletionService() for SK integration

    #region Private Fields

    /// <summary>The M.E.AI chat client for direct access.</summary>
    private readonly IChatClient _chatClient;

    /// <summary>The SK wrapper for IChatCompletionService.</summary>
    private readonly IChatCompletionService _innerService;

    /// <summary>Storage for AI service attributes.</summary>
    private readonly Dictionary<string, object?> _attributes = new();

    /// <summary>Logger instance.</summary>
    private readonly ILogger _logger;

    /// <summary>Default base URL for the Anthropic API.</summary>
    private static readonly Uri s_defaultBaseUrl = new("https://api.anthropic.com");

    /// <summary>Disposed flag.</summary>
    private bool _disposed;

    #endregion

    #region Private Methods

    /// <summary>
    /// Throws <see cref="ObjectDisposedException"/> if the service has been disposed.
    /// </summary>
    private void ThrowIfDisposed()
    {
#if NET8_0_OR_GREATER
        ObjectDisposedException.ThrowIf(this._disposed, this);
#else
        if (this._disposed)
        {
            throw new ObjectDisposedException(nameof(AnthropicChatCompletionService));
        }
#endif
    }

    #endregion

    #region Constructors

    /// <summary>
    /// Create an instance of the Anthropic chat completion connector.
    /// </summary>
    /// <param name="modelId">Model name (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="apiKey">API Key for authentication.</param>
    /// <param name="baseUrl">Base URL for the API endpoint. Defaults to https://api.anthropic.com.</param>
    /// <param name="httpClient">
    /// Custom <see cref="HttpClient"/> for HTTP requests.
    /// If not provided, a new HttpClient is created with the default 100-second timeout.
    /// </param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <remarks>
    /// <para>
    /// <b>Retry and Timeout Policy:</b> This connector follows the Semantic Kernel pattern of delegating
    /// retry and timeout handling to the <see cref="HttpClient"/> layer rather than the SDK layer.
    /// This prevents conflicting retry/timeout behavior when both layers attempt to handle failures.
    /// </para>
    /// <para>
    /// When providing a custom <paramref name="httpClient"/>, ensure it is configured with appropriate:
    /// <list type="bullet">
    ///   <item><description>Timeout: Set <see cref="HttpClient.Timeout"/> (default is 100 seconds)</description></item>
    ///   <item><description>Retry policy: Use <c>IHttpClientFactory</c> with Polly for transient failure handling</description></item>
    /// </list>
    /// </para>
    /// </remarks>
    public AnthropicChatCompletionService(
        string modelId,
        string apiKey,
        Uri? baseUrl = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        loggerFactory ??= NullLoggerFactory.Instance;
        this._logger = loggerFactory.CreateLogger<AnthropicChatCompletionService>();

        // 1. Build ClientOptions for Anthropic SDK
        // Note: Retry and timeout are intentionally disabled at SDK level.
        // The HttpClient layer handles these concerns (see constructor remarks).
        // - Default HttpClient has 100-second timeout
        // - Use IHttpClientFactory + Polly for retry policies
        var clientOptions = new ClientOptions
        {
            APIKey = apiKey,
            BaseUrl = baseUrl ?? s_defaultBaseUrl,
            MaxRetries = 0,                      // Disabled: HttpClient/Polly handles retries
            Timeout = Timeout.InfiniteTimeSpan   // Disabled: HttpClient.Timeout applies
        };

        // Only set HttpClient if provided; otherwise SDK creates its own (SK pattern)
        if (httpClient is not null)
        {
            clientOptions.HttpClient = httpClient;
        }

        // 2. Create Anthropic SDK Client
        var anthropicClient = new AnthropicClient(clientOptions);

        // 3. Build M.E.AI Pipeline (using shared helper for consistent pipeline across Service and DI)
        this._chatClient = AnthropicPipelineHelpers.BuildChatClientPipeline(anthropicClient, modelId, loggerFactory);

        // 4. SK Wrapper
        this._innerService = this._chatClient.AsChatCompletionService();

        // 5. Attributes
        this._attributes[AIServiceExtensions.ModelIdKey] = modelId;
        this._attributes[AIServiceExtensions.EndpointKey] = (baseUrl ?? s_defaultBaseUrl).ToString();

        this._logger.LogDebug(
            "AnthropicChatCompletionService created: ModelId={ModelId}, BaseUrl={BaseUrl}",
            modelId, baseUrl ?? s_defaultBaseUrl);
    }

    /// <summary>
    /// Create an instance of the Anthropic chat completion connector using an existing AnthropicClient.
    /// </summary>
    /// <param name="modelId">Model name (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="anthropicClient">Pre-configured <see cref="AnthropicClient"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <remarks>
    /// Use this constructor when you need full control over the AnthropicClient configuration.
    /// Note: HttpClient injection and retry settings are the responsibility of the caller.
    /// </remarks>
    public AnthropicChatCompletionService(
        string modelId,
        AnthropicClient anthropicClient,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(anthropicClient);

        loggerFactory ??= NullLoggerFactory.Instance;
        this._logger = loggerFactory.CreateLogger<AnthropicChatCompletionService>();

        // Build M.E.AI Pipeline from existing client (using shared helper for consistent pipeline across Service and DI)
        this._chatClient = AnthropicPipelineHelpers.BuildChatClientPipeline(anthropicClient, modelId, loggerFactory);

        // SK Wrapper
        this._innerService = this._chatClient.AsChatCompletionService();

        // Attributes - use the actual BaseUrl from the client
        this._attributes[AIServiceExtensions.ModelIdKey] = modelId;
        this._attributes[AIServiceExtensions.EndpointKey] = anthropicClient.BaseUrl.ToString();

        this._logger.LogDebug(
            "AnthropicChatCompletionService created with existing client: ModelId={ModelId}, BaseUrl={BaseUrl}",
            modelId, anthropicClient.BaseUrl);
    }

    #endregion

    #region IChatCompletionService Implementation

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <inheritdoc/>
    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        this.ThrowIfDisposed();
        this._logger.LogDebug("GetChatMessageContentsAsync called with {MessageCount} messages", chatHistory.Count);
        return this._innerService.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        this.ThrowIfDisposed();
        this._logger.LogDebug("GetStreamingChatMessageContentsAsync called with {MessageCount} messages", chatHistory.Count);
        return this._innerService.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken);
    }

    #endregion

    #region ITextGenerationService Implementation

    /// <inheritdoc/>
    public async Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        this.ThrowIfDisposed();

        // Delegate to chat completion (same pattern as OpenAI/Gemini connectors)
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage(prompt);

        var results = await this.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken)
            .ConfigureAwait(false);

        return results
            .Select(m => new TextContent(m.Content, m.ModelId, m.InnerContent, Encoding.UTF8, m.Metadata))
            .ToList();
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.ThrowIfDisposed();

        // Delegate to chat completion (same pattern as OpenAI/Gemini connectors)
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage(prompt);

        await foreach (var chunk in this.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken)
            .ConfigureAwait(false))
        {
            yield return new StreamingTextContent(
                chunk.Content,
                chunk.ChoiceIndex,
                chunk.ModelId,
                chunk.InnerContent,
                Encoding.UTF8,
                chunk.Metadata);
        }
    }

    #endregion

    #region IDisposable

    /// <summary>
    /// Disposes the service and releases the underlying resources.
    /// </summary>
    /// <remarks>
    /// Disposes the M.E.AI chat client pipeline. Note: The underlying HttpClient is NOT disposed
    /// by this service or the Anthropic SDK. When no HttpClient is provided, the SDK creates a
    /// long-lived instance. When an HttpClient is injected, its lifetime is the caller's responsibility.
    /// This is the recommended pattern for HttpClient (long-lived instances avoid socket exhaustion).
    /// </remarks>
    public void Dispose()
    {
        if (this._disposed)
        {
            return;
        }

        this._disposed = true;

        // Dispose the M.E.AI chat client pipeline
        this._chatClient.Dispose();
    }

    #endregion
}
