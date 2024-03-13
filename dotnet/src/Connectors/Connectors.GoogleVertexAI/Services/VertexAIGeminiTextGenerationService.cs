// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Represents a service for generating text using the Vertex AI Gemini API.
/// </summary>
public sealed class VertexAIGeminiTextGenerationService : ITextGenerationService
{
    private readonly Dictionary<string, object?> _attributesInternal = new();
    private readonly GeminiTextGenerationClient _textGenerationClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="VertexAIGeminiTextGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">The model identifier.</param>
    /// <param name="bearerKey">The Bearer Key for authentication.</param>
    /// <param name="location">The region to process the request.</param>
    /// <param name="projectId">Your Project Id.</param>
    /// <param name="httpClient">The optional HTTP client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public VertexAIGeminiTextGenerationService(
        string modelId,
        string bearerKey,
        string location,
        string projectId,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
        : this(modelId, () => bearerKey, location, projectId, httpClient, loggerFactory)
    {
        Verify.NotNullOrWhiteSpace(bearerKey);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VertexAIGeminiTextGenerationService"/> class.
    /// </summary>
    /// <param name="modelId">The model identifier.</param>
    /// <param name="bearerKeyProvider">The Bearer Key provider for authentication.</param>
    /// <param name="location">The region to process the request.</param>
    /// <param name="projectId">Your Project Id.</param>
    /// <param name="httpClient">The optional HTTP client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    /// <remarks>
    /// This <paramref name="bearerKeyProvider"/> will be called on every request,
    /// when providing the token consider using caching strategy and refresh token logic
    /// when it is expired or close to expiration.
    /// </remarks>
    public VertexAIGeminiTextGenerationService(
        string modelId,
        Func<string> bearerKeyProvider,
        string location,
        string projectId,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(bearerKeyProvider);
        Verify.NotNullOrWhiteSpace(location);
        Verify.NotNullOrWhiteSpace(projectId);

        this._textGenerationClient = new GeminiTextGenerationClient(new GeminiChatCompletionClient(
#pragma warning disable CA2000
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
#pragma warning restore CA2000
            modelId: modelId,
            bearerKeyProvider: bearerKeyProvider,
            location: location,
            projectId: projectId,
            logger: loggerFactory?.CreateLogger(typeof(VertexAIGeminiTextGenerationService))));
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this._attributesInternal;

    /// <inheritdoc />
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => this._textGenerationClient.GenerateTextAsync(prompt, executionSettings, kernel, cancellationToken);

    /// <inheritdoc />
    public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => this._textGenerationClient.StreamGenerateTextAsync(prompt, executionSettings, kernel, cancellationToken);
}
