// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Net.Http;
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
/// AzureOpenAI service client.
/// </summary>
public sealed class AzureOpenAIServiceClient : IAzureOpenAIServiceClient
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIServiceClient"/> class.
    /// </summary>
    /// <param name="httpClient">The HTTP client.</param>
    /// <param name="apiKey">The AzureOPenAI API key</param>
    /// <param name="apiVersion">The AzureOPenAI API version.</param>
    /// <param name="logger">The logger.</param>
    public AzureOpenAIServiceClient(HttpClient httpClient, string apiKey, string apiVersion = DefaultAzureAPIVersion, ILogger? logger = null)
    {
        Verify.NotNull(httpClient, "The httpClient is not set to an instance of an object.");
        Verify.NotEmpty(apiKey, "Invalid Azure OpenAI key.");
        Verify.NotEmpty(apiVersion, "Invalid Azure OpenAI API version.");

        this._httpClient = httpClient;
        this._apiKey = apiKey;
        this._apiVersion = apiVersion;
        this._logger = logger ?? NullLogger.Instance;
    }

    /// <inheritdoc/>
    public async Task<EmbeddingResponse> CreateEmbeddingAsync(EmbeddingRequest request, string deploymentName, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(request, "The embedding request is not set to an instance of an object.");
        Verify.NotEmpty(deploymentName, "The deployment name is not provided.");

        var endpoint = string.Format(CultureInfo.InvariantCulture, EmbeddingsPath, deploymentName, this._apiVersion);

        var uri = this.GetAzureOpenAIRequestURI(endpoint);

        this._logger.LogDebug("Sending OpenAI embedding request to {0}", uri);

        return await this.PostAsync<EmbeddingResponse, EmbeddingRequest>(uri, request, cancellationToken);
    }

    /// <inheritdoc/>
    public async Task<CompletionResponse> ExecuteCompletionAsync(AzureCompletionRequest request, string deploymentName, CancellationToken cancellationToken)
    {
        Verify.NotNull(request, "The completion request is not set to an instance of an object.");
        Verify.NotEmpty(deploymentName, "The deployment name is not provided.");

        var endpoint = string.Format(CultureInfo.InvariantCulture, CompletionsPath, deploymentName, this._apiVersion);

        var uri = this.GetAzureOpenAIRequestURI(endpoint);

        this._logger.LogDebug("Sending Azure OpenAI completion request to {0}", uri);

        return await this.PostAsync<CompletionResponse, AzureCompletionRequest>(uri, request, cancellationToken);
    }

    /// <inheritdoc/>
    public async Task<AzureDeployments> GetDeploymentsAsync(CancellationToken cancellationToken = default)
    {
        var endpoint = string.Format(CultureInfo.InvariantCulture, DeploymentsPath, this._apiVersion);

        var uri = this.GetAzureOpenAIRequestURI(endpoint);

        this._logger.LogDebug("Sending Azure OpenAI deployments request to {0}", uri);

        return await this.GetAsync<AzureDeployments>(uri, cancellationToken);
    }

    /// <summary>
    /// Send a POST request to the specified Uri.
    /// </summary>
    /// <typeparam name="TR">The result type.</typeparam>
    /// <typeparam name="TI">The request type.</typeparam>
    /// <param name="uri">The Uri to send the POST request to.</param>
    /// <param name="request">The request to send.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The response.</returns>
    private async Task<TR> PostAsync<TR, TI>(string uri, TI request, CancellationToken cancellationToken)
    {
        Verify.NotNull(uri, "The uri is not provided.");
        Verify.NotNull(request, "The request is not provided.");

        using var requestMessage = new HttpRequestMessage(HttpMethod.Post, uri);

        requestMessage.Content = new StringContent(Json.Serialize(request), Encoding.UTF8, MediaTypeNames.Application.Json);

        requestMessage.Headers.Add(ApiKeyHeaderName, this._apiKey);

        using var responseMessage = await this._httpClient.SendAsync(requestMessage, cancellationToken);

        return await responseMessage.HandleResponseAsync<TR>();
    }

    /// <summary>
    /// Send a GET request to the specified Uri.
    /// </summary>
    /// <typeparam name="TR">The result type.</typeparam>
    /// <param name="uri">The Uri to send the GET request to.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The response.</returns>
    private async Task<TR> GetAsync<TR>(string uri, CancellationToken cancellationToken)
    {
        Verify.NotNull(uri, "The uri is not provided.");

        using var requestMessage = new HttpRequestMessage(HttpMethod.Get, uri);

        requestMessage.Headers.Add(ApiKeyHeaderName, this._apiKey);

        using var responseMessage = await this._httpClient.SendAsync(requestMessage, cancellationToken);

        return await responseMessage.HandleResponseAsync<TR>();
    }

    /// <summary>
    /// Get URI for Azure OpenAI request with specified endpoint.
    /// </summary>
    /// <param name="endpoint">OpenAI endpoint.</param>
    /// <returns>The URI for the OpenAI Request.</returns>
    private string GetAzureOpenAIRequestURI(string endpoint)
    {
        return string.Concat(this._httpClient.BaseAddress?.AbsoluteUri?.TrimEnd('/'), endpoint);
    }

    #region private ================================================================================

    /// <summary>
    /// Path format for the "embeddings" Azure OpenAI endpoint/resource.
    /// </summary>
    private const string EmbeddingsPath = "/openai/deployments/{0}/embeddings?api-version={1}";

    /// <summary>
    /// Path format for the "completions" Azure OpenAI endpoint/resource.
    /// </summary>
    private const string CompletionsPath = "/openai/deployments/{0}/completions?api-version={1}";

    /// <summary>
    /// Path format for the "deployments" Azure OpenAI endpoint/resource.
    /// </summary>
    private const string DeploymentsPath = "/openai/deployments?api-version={0}";

    /// <summary>
    /// Default Azure OpenAI REST API version.
    /// </summary>
    private const string DefaultAzureAPIVersion = "2022-12-01";

    /// <summary>
    /// Azure OpenAI API key header name.
    /// </summary>
    private const string ApiKeyHeaderName = "api-key";

    /// <summary>
    /// The Azure OpenAI API key.
    /// </summary>
    private readonly string _apiKey;

    /// <summary>
    /// The HTTP client.
    /// </summary>
    private readonly HttpClient _httpClient;

    /// <summary>
    /// The logger.
    /// </summary>
    private readonly ILogger _logger;

    /// <summary>
    /// AzureOpenAI API version.
    /// </summary>
    private readonly string _apiVersion;

    #endregion
}
