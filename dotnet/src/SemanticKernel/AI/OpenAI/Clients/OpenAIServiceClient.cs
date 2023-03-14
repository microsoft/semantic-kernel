// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Mime;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.AI.OpenAI.Clients;

/// <summary>
/// OpenAI service client.
/// </summary>
public sealed class OpenAIServiceClient : IOpenAIServiceClient
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIServiceClient"/> class.
    /// </summary>
    /// <param name="httpClient">The HTTP client.</param>
    /// <param name="apiKey">OpenAI API key.</param>
    /// <param name="orgId">OpenAI organization id.</param>
    /// <param name="logger">The logger.</param>
    public OpenAIServiceClient(HttpClient httpClient, string apiKey, string? orgId, ILogger? logger = null)
    {
        Verify.NotNull(httpClient, "The embedding request is not set to an instance of an object.");
        Verify.NotEmpty(apiKey, "Invalid OpenAI key.");

        this._httpClient = httpClient;
        this._orgId = orgId;
        this._apiKey = apiKey;
        this._logger = logger ?? NullLogger.Instance;
    }

    /// <inheritdoc/>
    public async Task<EmbeddingResponse> CreateEmbeddingAsync(OpenAIEmbeddingRequest request, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(request, "The embedding request is not set to an instance of an object.");

        var uri = this.GetOpenAIRequestURI(EmbeddingsPath);

        this._logger.LogDebug("Sending OpenAI embedding request to {0}", uri);

        return await this.PostAsync<EmbeddingResponse, OpenAIEmbeddingRequest>(uri, request, cancellationToken);
    }

    /// <inheritdoc/>
    public async Task<CompletionResponse> ExecuteCompletionAsync(OpenAICompletionRequest request, string modelId, CancellationToken cancellationToken)
    {
        Verify.NotNull(request, "The completion request is not set to an instance of an object.");
        Verify.NotEmpty(modelId, "The model id is not provided.");

        var endpoint = string.Format(CultureInfo.InvariantCulture, CompletionsPath, modelId);

        var uri = this.GetOpenAIRequestURI(endpoint);

        this._logger.LogDebug("Sending OpenAI completion request to {0}", uri);

        return await this.PostAsync<CompletionResponse, OpenAICompletionRequest>(uri, request, cancellationToken);
    }

    /// <summary>
    /// Send a POST request to the specified Uri.
    /// </summary>
    /// <typeparam name="TResponse">The response type.</typeparam>
    /// <typeparam name="TRequest">The request type.</typeparam>
    /// <param name="uri">The Uri to send the POST request to.</param>
    /// <param name="request">The request to send.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The response.</returns>
    private async Task<TResponse> PostAsync<TResponse, TRequest>(string uri, TRequest request, CancellationToken cancellationToken)
    {
        Verify.NotNull(uri, "The uri is not provided.");
        Verify.NotNull(request, "The request is not provided.");

        using var requestMessage = new HttpRequestMessage(HttpMethod.Post, uri);

        requestMessage.Content = new StringContent(Json.Serialize(request), Encoding.UTF8, MediaTypeNames.Application.Json);

        requestMessage.Headers.Authorization = new AuthenticationHeaderValue(AuthenticationScheme, this._apiKey);

        if (!string.IsNullOrEmpty(this._orgId))
        {
            requestMessage.Headers.Add(OrganizationHeaderName, this._orgId);
        }

        using var responseMessage = await this._httpClient.SendAsync(requestMessage, cancellationToken);

        return await responseMessage.HandleResponseAsync<TResponse>();
    }

    /// <summary>
    /// Get URI for OpenAI request with specified endpoint.
    /// </summary>
    /// <param name="endpoint">OpenAI endpoint.</param>
    /// <returns>The URI for the OpenAI Request.</returns>
    private string GetOpenAIRequestURI(string endpoint)
    {
        return string.Concat(this._httpClient.BaseAddress?.AbsoluteUri?.TrimEnd('/'), endpoint);
    }

    #region private ================================================================================

    /// <summary>
    /// Path format for the "embeddings" OpenAI endpoint/resource.
    /// </summary>
    private const string EmbeddingsPath = "/embeddings";

    /// <summary>
    /// Path format for the "completions" OpenAI endpoint/resource.
    /// </summary>
    private const string CompletionsPath = "/engines/{0}/completions";

    /// <summary>
    /// OpenAI organization header name.
    /// </summary>
    private const string OrganizationHeaderName = "OpenAI-Organization";

    /// <summary>
    /// Authentication scheme.
    /// </summary>
    private const string AuthenticationScheme = "Bearer";

    /// <summary>
    /// The HTTP client.
    /// </summary>
    private readonly HttpClient _httpClient;

    /// <summary>
    /// The OpenAI organization id.
    /// </summary>
    private readonly string? _orgId;

    /// <summary>
    /// The OpenAI API key.
    /// </summary>
    private readonly string _apiKey;

    /// <summary>
    /// The logger.
    /// </summary>
    private readonly ILogger _logger;

    #endregion
}
