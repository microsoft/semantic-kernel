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
    /// <param name="model">The MistralAI model for the text generation service.</param>
    /// <param name="apiKey">API key for accessing the MistralAI service.</param>
    /// <param name="endpoint">Optional  uri endpoint including the port where MistralAI server is hosted. Default is https://api.mistral.ai.</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the MistralAI API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public MistralAIChatCompletionService(string model, string apiKey, Uri? endpoint = null, HttpClient? httpClient = null, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);

        this.Client = new MistralClient(
        modelId: model,
            endpoint: endpoint ?? httpClient?.BaseAddress,
            apiKey: apiKey,
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
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
