// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.MistralAI;

/// <summary>
/// Mistral chat completion service.
/// </summary>
public sealed class MistralAIChatCompletionService : IChatCompletionService
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MistralAIChatCompletionService"/> class.
    /// </summary>
    /// <param name="model">The HuggingFace model for the text generation service.</param>
    /// <param name="endpoint">The uri endpoint including the port where HuggingFace server is hosted</param>
    /// <param name="apiKey">Optional API key for accessing the HuggingFace service.</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the HuggingFace API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public MistralAIChatCompletionService(string model, Uri? endpoint, string? apiKey, HttpClient httpClient, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);

        this.Client = new MistralClient(
        modelId: model,
            endpoint: endpoint ?? httpClient?.BaseAddress,
            apiKey: apiKey,
#pragma warning disable CA2000 // Dispose objects before losing scope
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
#pragma warning restore CA2000 // Dispose objects before losing scope
            logger: loggerFactory?.CreateLogger(this.GetType()) ?? NullLogger.Instance
        );

        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <inheritdoc/>
    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this.Client.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken);

    /// <inheritdoc/>
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this.Client.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken);

    #region private
    private Dictionary<string, object?> AttributesInternal { get; } = new();
    private MistralClient Client { get; }
    #endregion
}
