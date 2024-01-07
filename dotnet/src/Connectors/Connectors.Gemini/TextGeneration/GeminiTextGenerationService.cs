#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Gemini.Abstract;
using Microsoft.SemanticKernel.Connectors.Gemini.Core;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.Gemini;

/// <summary>
/// Represents a service for generating text using the Gemini API.
/// </summary>
public sealed class GeminiTextGenerationService : ITextGenerationService
{
    private readonly Dictionary<string, object?> _attributes = new();
    private readonly IGeminiClient _client;

    /// <summary>
    /// Initializes a new instance of the <see cref="GeminiTextGenerationService"/> class.
    /// </summary>
    /// <param name="model">The model identifier.</param>
    /// <param name="apiKey">The API key.</param>
    /// <param name="httpClient">The optional HTTP client.</param>
    public GeminiTextGenerationService(string model, string apiKey, HttpClient? httpClient = null)
    {
        Verify.NotNullOrWhiteSpace(model);
        Verify.NotNullOrWhiteSpace(apiKey);

        var geminiConfiguration = new GeminiConfiguration(apiKey) { ModelId = model };
        this._client = new GeminiClient(HttpClientProvider.GetHttpClient(httpClient), geminiConfiguration);
        this._attributes.Add(AIServiceExtensions.ModelIdKey, model);
    }

    internal GeminiTextGenerationService(IGeminiClient client)
    {
        this._client = client;
        this._attributes.Add(AIServiceExtensions.ModelIdKey, client.ModelId);
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <inheritdoc />
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this._client.GenerateTextAsync(prompt, executionSettings, cancellationToken);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this._client.StreamGenerateTextAsync(prompt, executionSettings, cancellationToken);
    }
}
