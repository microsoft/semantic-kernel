// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Backends.HuggingFace.HttpSchema;

namespace Microsoft.SemanticKernel.Backends.HuggingFace;

/// <summary>
/// Backend implementation for HuggingFace models usage.
/// </summary>
public sealed class HuggingFaceBackend : ITextCompletionClient, IEmbeddingGenerator<string, float>, IDisposable
{
    private const string HttpUserAgent = "Microsoft Semantic Kernel";
    private const string CompletionEndpoint = "/completions";
    private const string EmbeddingEndpoint = "/embeddings";

    private readonly string _model;
    private readonly HttpClient _httpClient;
    private readonly HttpClientHandler? _httpClientHandler;

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceBackend"/> class.
    /// </summary>
    /// <param name="baseUri">Base URI to call for backend operations.</param>
    /// <param name="model">Model to use for backend operations.</param>
    /// <param name="httpClientHandler">Instance of <see cref="HttpClientHandler"/> to setup specific scenarios.</param>
    public HuggingFaceBackend(Uri baseUri, string model, HttpClientHandler httpClientHandler)
    {
        this._model = model;

        this._httpClient = new(httpClientHandler);

        this._httpClient.BaseAddress = baseUri;
        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpUserAgent);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceBackend"/> class.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="baseUri">Base URI to call for backend operations.</param>
    /// <param name="model">Model to use for backend operations.</param>
    public HuggingFaceBackend(Uri baseUri, string model)
    {
        this._model = model;

        this._httpClientHandler = new();
        this._httpClient = new(this._httpClientHandler);

        this._httpClient.BaseAddress = baseUri;
        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpUserAgent);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceBackend"/> class.
    /// </summary>
    /// <param name="baseUri">Base URI to call for backend operations in <see cref="string"/> format.</param>
    /// <param name="model">Model to use for backend operations.</param>
    /// <param name="httpClientHandler">Instance of <see cref="HttpClientHandler"/> to setup specific scenarios.</param>
    public HuggingFaceBackend(string baseUri, string model, HttpClientHandler httpClientHandler)
        : this(new Uri(baseUri), model, httpClientHandler)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HuggingFaceBackend"/> class.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="baseUri">Base URI to call for backend operations in <see cref="string"/> format.</param>
    /// <param name="model">Model to use for backend operations.</param>
    public HuggingFaceBackend(string baseUri, string model)
        : this(new Uri(baseUri), model)
    {
    }

    /// <inheritdoc/>
    public async Task<string> CompleteAsync(string text, CompleteRequestSettings requestSettings)
    {
        return await this.ExecuteCompleteRequestAsync(text);
    }

    /// <inheritdoc/>
    public async Task<IList<Embedding<float>>> GenerateEmbeddingsAsync(IList<string> data)
    {
        return await this.ExecuteEmbeddingRequestAsync(data);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._httpClient.Dispose();
        this._httpClientHandler?.Dispose();
    }

    #region private ================================================================================

    /// <summary>
    /// Performs HTTP request to given base URI for completion.
    /// </summary>
    /// <param name="text">Text to complete.</param>
    /// <returns>Completed text.</returns>
    /// <exception cref="AIException">Exception when backend didn't respond with completed text.</exception>
    private async Task<string> ExecuteCompleteRequestAsync(string text)
    {
        try
        {
            var completionRequest = new CompletionRequest
            {
                Prompt = text,
                Model = _model
            };

            using var httpRequestMessage = new HttpRequestMessage()
            {
                Method = HttpMethod.Post,
                RequestUri = new Uri(CompletionEndpoint, UriKind.Relative),
                Content = new StringContent(JsonSerializer.Serialize(completionRequest)),
            };

            var response = await this._httpClient.SendAsync(httpRequestMessage).ConfigureAwait(false);
            var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

            var completionResponse = JsonSerializer.Deserialize<CompletionResponse>(body);

            return completionResponse?.Choices.First().Text!;
        }
        catch (Exception e) when (e is not AIException)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }

    /// <summary>
    /// Performs HTTP request to given base URI for embedding generation.
    /// </summary>
    /// <param name="data">Data to embed.</param>
    /// <returns>List of generated embeddings.</returns>
    /// <exception cref="AIException">Exception when backend didn't respond with generated embeddings.</exception>
    private async Task<IList<Embedding<float>>> ExecuteEmbeddingRequestAsync(IList<string> data)
    {
        try
        {
            var embeddingRequest = new EmbeddingRequest
            {
                Input = data,
                Model = _model
            };

            using var httpRequestMessage = new HttpRequestMessage()
            {
                Method = HttpMethod.Post,
                RequestUri = new Uri(EmbeddingEndpoint, UriKind.Relative),
                Content = new StringContent(JsonSerializer.Serialize(embeddingRequest)),
            };

            var response = await this._httpClient.SendAsync(httpRequestMessage).ConfigureAwait(false);
            var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

            var embeddingResponse = JsonSerializer.Deserialize<EmbeddingResponse>(body);

            return embeddingResponse?.Embeddings?.Select(l => new Embedding<float>(l.Embedding.ToArray())).ToList()!;
        }
        catch (Exception e) when (e is not AIException)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }

    #endregion
}
