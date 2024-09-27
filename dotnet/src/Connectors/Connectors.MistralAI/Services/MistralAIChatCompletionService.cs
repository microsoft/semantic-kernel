// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI.Client;
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
    /// <param name="modelId">The MistralAI modelId for the text generation service.</param>
    /// <param name="apiKey">API key for accessing the MistralAI service.</param>
    /// <param name="endpoint">Optional  uri endpoint including the port where MistralAI server is hosted. Default is https://api.mistral.ai.</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the MistralAI API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public MistralAIChatCompletionService(string modelId, string apiKey, Uri? endpoint = null, HttpClient? httpClient = null, ILoggerFactory? loggerFactory = null)
    {
        this.Client = new MistralClient(
            modelId: modelId,
            endpoint: endpoint ?? httpClient?.BaseAddress,
            apiKey: apiKey,
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
            logger: loggerFactory?.CreateLogger(this.GetType()) ?? NullLogger.Instance
        );

        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <inheritdoc/>
    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this.Client.GetChatMessageContentsAsync(chatHistory, cancellationToken, executionSettings, kernel);

    /// <inheritdoc/>
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        => this.Client.GetStreamingChatMessageContentsAsync(chatHistory, cancellationToken, executionSettings, kernel);

    #region private
    private Dictionary<string, object?> AttributesInternal { get; } = new();
    private MistralClient Client { get; }
    #endregion
}
