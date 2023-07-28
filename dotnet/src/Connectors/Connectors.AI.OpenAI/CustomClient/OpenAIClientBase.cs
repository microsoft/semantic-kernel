// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.CustomClient;

/// <summary>Base type for OpenAI clients.</summary>
public abstract class OpenAIClientBase
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIClientBase"/> class.
    /// </summary>
    /// <param name="httpClient">The HttpClient used for making HTTP requests.</param>
    /// <param name="logger">The ILogger used for logging. If null, a NullLogger instance will be used.</param>
    private protected OpenAIClientBase(HttpClient? httpClient, ILogger? logger = null)
    {
        this._httpClient = httpClient ?? new HttpClient(NonDisposableHttpClientHandler.Instance, disposeHandler: false);
        this._logger = logger ?? NullLogger.Instance;
    }

    /// <summary>Adds headers to use for OpenAI HTTP requests.</summary>
    private protected virtual void AddRequestHeaders(HttpRequestMessage request)
    {
        request.Headers.Add("User-Agent", Telemetry.HttpUserAgent);
    }

    /// <summary>
    /// Asynchronously sends a text embedding request for the text.
    /// </summary>
    /// <param name="url">URL for the text embedding request API</param>
    /// <param name="requestBody">Request payload</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>List of text embeddings</returns>
    /// <exception cref="AIException">AIException thrown during the request.</exception>
    private protected async Task<IList<Embedding<float>>> ExecuteTextEmbeddingRequestAsync(
        string url,
        string requestBody,
        CancellationToken cancellationToken = default)
    {
        var result = await this.ExecutePostRequestAsync<TextEmbeddingResponse>(url, requestBody, cancellationToken).ConfigureAwait(false);
        if (result.Embeddings is not { Count: >= 1 })
        {
            throw new AIException(
                AIException.ErrorCodes.InvalidResponseContent,
                "Embeddings not found");
        }

        return result.Embeddings.Select(e => new Embedding<float>(e.Values, transferOwnership: true)).ToList();
    }

    /// <summary>
    /// Run the HTTP request to generate a list of images
    /// </summary>
    /// <param name="url">URL for the image generation request API</param>
    /// <param name="requestBody">Request payload</param>
    /// <param name="extractResponseFunc">Function to invoke to extract the desired portion of the image generation response.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>List of image URLs</returns>
    /// <exception cref="AIException">AIException thrown during the request.</exception>
    private protected async Task<IList<string>> ExecuteImageGenerationRequestAsync(
        string url,
        string requestBody,
        Func<ImageGenerationResponse.Image, string> extractResponseFunc,
        CancellationToken cancellationToken = default)
    {
        var result = await this.ExecutePostRequestAsync<ImageGenerationResponse>(url, requestBody, cancellationToken).ConfigureAwait(false);
        return result.Images.Select(extractResponseFunc).ToList();
    }

    private protected virtual string? GetErrorMessageFromResponse(string jsonResponsePayload)
    {
        try
        {
            JsonNode? root = JsonSerializer.Deserialize<JsonNode>(jsonResponsePayload);

            return root?["error"]?["message"]?.GetValue<string>();
        }
        catch (Exception ex) when (ex is NotSupportedException or JsonException)
        {
            this._logger.LogError(ex, "Unable to extract error from response body content. Exception: {0}:{1}", ex.GetType(), ex.Message);
        }

        return null;
    }

    #region private ================================================================================

    /// <summary>
    /// Logger
    /// </summary>
    private readonly ILogger _logger;

    /// <summary>
    /// The HttpClient used for making HTTP requests.
    /// </summary>
    private readonly HttpClient _httpClient;

    private protected async Task<T> ExecutePostRequestAsync<T>(string url, string requestBody, CancellationToken cancellationToken = default)
    {
        try
        {
            using var content = new StringContent(requestBody, Encoding.UTF8, "application/json");
            using var response = await this.ExecuteRequestAsync(url, HttpMethod.Post, content, cancellationToken).ConfigureAwait(false);
            string responseJson = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
            T result = this.JsonDeserialize<T>(responseJson);
            return result;
        }
        catch (Exception e) when (e is not AIException)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }

    private protected T JsonDeserialize<T>(string responseJson)
    {
        var result = Json.Deserialize<T>(responseJson);
        if (result is null)
        {
            throw new AIException(AIException.ErrorCodes.InvalidResponseContent, "Response JSON parse error");
        }

        return result;
    }

    private protected async Task<HttpResponseMessage> ExecuteRequestAsync(string url, HttpMethod method, HttpContent? content, CancellationToken cancellationToken = default)
    {
        try
        {
            HttpResponseMessage? response = null;
            using (var request = new HttpRequestMessage(method, url))
            {
                this.AddRequestHeaders(request);
                if (content != null)
                {
                    request.Content = content;
                }

                response = await this._httpClient.SendAsync(request, cancellationToken).ConfigureAwait(false);
            }

            this._logger.LogDebug("HTTP response: {0} {1}", (int)response.StatusCode, response.StatusCode.ToString("G"));

            if (response.IsSuccessStatusCode)
            {
                return response;
            }

            string responseJson = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
            string? errorDetail = this.GetErrorMessageFromResponse(responseJson);
            switch ((HttpStatusCodeType)response.StatusCode)
            {
                case HttpStatusCodeType.BadRequest:
                case HttpStatusCodeType.MethodNotAllowed:
                case HttpStatusCodeType.NotFound:
                case HttpStatusCodeType.NotAcceptable:
                case HttpStatusCodeType.Conflict:
                case HttpStatusCodeType.Gone:
                case HttpStatusCodeType.LengthRequired:
                case HttpStatusCodeType.PreconditionFailed:
                case HttpStatusCodeType.RequestEntityTooLarge:
                case HttpStatusCodeType.RequestUriTooLong:
                case HttpStatusCodeType.UnsupportedMediaType:
                case HttpStatusCodeType.RequestedRangeNotSatisfiable:
                case HttpStatusCodeType.ExpectationFailed:
                case HttpStatusCodeType.HttpVersionNotSupported:
                case HttpStatusCodeType.UpgradeRequired:
                case HttpStatusCodeType.MisdirectedRequest:
                case HttpStatusCodeType.UnprocessableEntity:
                case HttpStatusCodeType.Locked:
                case HttpStatusCodeType.FailedDependency:
                case HttpStatusCodeType.PreconditionRequired:
                case HttpStatusCodeType.RequestHeaderFieldsTooLarge:
                    throw new AIException(
                        AIException.ErrorCodes.InvalidRequest,
                        $"The request is not valid, HTTP status: {response.StatusCode:G}",
                        errorDetail);

                case HttpStatusCodeType.Unauthorized:
                case HttpStatusCodeType.Forbidden:
                case HttpStatusCodeType.ProxyAuthenticationRequired:
                case HttpStatusCodeType.UnavailableForLegalReasons:
                case HttpStatusCodeType.NetworkAuthenticationRequired:
                    throw new AIException(
                        AIException.ErrorCodes.AccessDenied,
                        $"The request is not authorized, HTTP status: {response.StatusCode:G}",
                        errorDetail);

                case HttpStatusCodeType.RequestTimeout:
                    throw new AIException(
                        AIException.ErrorCodes.RequestTimeout,
                        $"The request timed out, HTTP status: {response.StatusCode:G}");

                case HttpStatusCodeType.TooManyRequests:
                    throw new AIException(
                        AIException.ErrorCodes.Throttling,
                        $"Too many requests, HTTP status: {response.StatusCode:G}",
                        errorDetail);

                case HttpStatusCodeType.InternalServerError:
                case HttpStatusCodeType.NotImplemented:
                case HttpStatusCodeType.BadGateway:
                case HttpStatusCodeType.ServiceUnavailable:
                case HttpStatusCodeType.GatewayTimeout:
                case HttpStatusCodeType.InsufficientStorage:
                    throw new AIException(
                        AIException.ErrorCodes.ServiceError,
                        $"The service failed to process the request, HTTP status: {response.StatusCode:G}",
                        errorDetail);

                default:
                    throw new AIException(
                        AIException.ErrorCodes.UnknownError,
                        $"Unexpected HTTP response, status: {response.StatusCode:G}",
                        errorDetail);
            }
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
