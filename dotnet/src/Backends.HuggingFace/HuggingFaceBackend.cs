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

public sealed class HuggingFaceBackend : ITextCompletionClient, IEmbeddingGenerator<string, float>, IDisposable
{
    private const string HttpUserAgent = "Microsoft Semantic Kernel";
    private const string CompletionEndpoint = "/completions";
    private const string EmbeddingEndpoint = "/embeddings";

    private readonly string _model;
    private readonly HttpClient _httpClient;
    private readonly HttpClientHandler _httpClientHandler;

    public HuggingFaceBackend(Uri baseUri, string model, HttpClientHandler httpClientHandler)
    {
        this._model = model;

        this._httpClientHandler = httpClientHandler;
        this._httpClient = new(this._httpClientHandler);

        this._httpClient.BaseAddress = baseUri;
        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpUserAgent);
    }

    public HuggingFaceBackend(Uri baseUri, string model)
        : this(baseUri, model, new HttpClientHandler())
    {
    }

    public HuggingFaceBackend(string baseUri, string model)
        : this(new Uri(baseUri), model)
    {
    }

    public async Task<string> CompleteAsync(string text, CompleteRequestSettings requestSettings)
    {
        return await this.ExecuteCompleteRequestAsync(text);
    }

    public async Task<IList<Embedding<float>>> GenerateEmbeddingsAsync(IList<string> data)
    {
        return await this.ExecuteEmbeddingRequestAsync(data);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._httpClientHandler.Dispose();
    }

    #region private ================================================================================

    private async Task<string> ExecuteCompleteRequestAsync(string text)
    {
        try
        {
            var completionsRequest = new CompletionRequest
            {
                Prompt = text,
                Model = _model
            };

            using var httpRequestMessage = new HttpRequestMessage()
            {
                Method = HttpMethod.Post,
                RequestUri = new Uri(CompletionEndpoint, UriKind.Relative),
                Content = new StringContent(JsonSerializer.Serialize(completionsRequest)),
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
