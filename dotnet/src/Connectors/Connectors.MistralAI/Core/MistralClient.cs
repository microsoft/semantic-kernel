// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.MistralAI;

/// <summary>
/// The Mistral client.
/// </summary>
internal sealed class MistralClient
{
    internal MistralClient(
        string modelId,
        HttpClient httpClient,
        Uri? endpoint = null,
        string? apiKey = null,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(httpClient);

        endpoint ??= new Uri("https://api.mistral.ai/v1");
        this._separator = endpoint.AbsolutePath.EndsWith("/", StringComparison.InvariantCulture) ? string.Empty : "/";
        this._endpoint = endpoint;
        this._modelId = modelId;
        this._apiKey = apiKey;
        this._httpClient = httpClient;
        this._logger = logger ?? NullLogger.Instance;
    }

    internal Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    internal IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    internal Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    #region private
    private readonly string _modelId;
    private readonly string? _apiKey;
    private readonly Uri? _endpoint;
    private readonly string _separator;
    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;
    #endregion
}
