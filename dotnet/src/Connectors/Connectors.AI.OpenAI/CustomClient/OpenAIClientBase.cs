// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
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
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.CustomClient;

/// <summary>
/// An abstract OpenAI Client.
/// </summary>
[SuppressMessage("Design", "CA1054:URI-like parameters should not be strings", Justification = "OpenAI users use strings")]
public abstract class OpenAIClientBase : IDisposable
{
    /// <summary>
    /// Logger
    /// </summary>
    protected ILogger Log { get; } = NullLogger.Instance;

    /// <summary>
    /// HTTP client
    /// </summary>
    protected HttpClient HTTPClient { get; }

    private readonly HttpClientHandler _httpClientHandler;
    private readonly IDelegatingHandlerFactory _handlerFactory;
    private readonly DelegatingHandler _retryHandler;

    internal OpenAIClientBase(ILogger? log = null, IDelegatingHandlerFactory? handlerFactory = null)
    {
        this.Log = log ?? this.Log;
        this._handlerFactory = handlerFactory ?? new DefaultHttpRetryHandlerFactory();

        this._httpClientHandler = new() { CheckCertificateRevocationList = true };
        this._retryHandler = this._handlerFactory.Create(this.Log);
        this._retryHandler.InnerHandler = this._httpClientHandler;

        this.HTTPClient = new HttpClient(this._retryHandler);
        this.HTTPClient.DefaultRequestHeaders.Add("User-Agent", HTTPUseragent);
    }

    /// <summary>
    /// Asynchronously sends a text embedding request for the text.
    /// </summary>
    /// <param name="url">URL for the text embedding request API</param>
    /// <param name="requestBody">Request payload</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>List of text embeddings</returns>
    /// <exception cref="AIException">AIException thrown during the request.</exception>
    protected async Task<IList<Embedding<float>>> ExecuteTextEmbeddingRequestAsync(
        string url,
        string requestBody,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var result = await this.ExecutePostRequestAsync<TextEmbeddingResponse>(url, requestBody, cancellationToken);
            if (result.Embeddings.Count < 1)
            {
                throw new AIException(
                    AIException.ErrorCodes.InvalidResponseContent,
                    "Embeddings not found");
            }

            return result.Embeddings.Select(e => new Embedding<float>(e.Values.ToArray())).ToList();
        }
        catch (Exception e) when (e is not AIException)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }

    /// <summary>
    /// Run the HTTP request to generate a list of images
    /// </summary>
    /// <param name="url">URL for the image generation request API</param>
    /// <param name="requestBody">Request payload</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>List of image URLs</returns>
    /// <exception cref="AIException">AIException thrown during the request.</exception>
    protected async Task<IList<string>> ExecuteImageUrlGenerationRequestAsync(
        string url,
        string requestBody,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var result = await this.ExecutePostRequestAsync<ImageGenerationResponse>(url, requestBody, cancellationToken);
            return result.Images.Select(x => x.Url).ToList();
        }
        catch (Exception e) when (e is not AIException)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }

    /// <summary>
    /// Run the HTTP request to generate a list of images
    /// </summary>
    /// <param name="url">URL for the image generation request API</param>
    /// <param name="requestBody">Request payload</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>List of images serialized in base64</returns>
    /// <exception cref="AIException">AIException thrown during the request.</exception>
    protected async Task<IList<string>> ExecuteImageBase64GenerationRequestAsync(
        string url,
        string requestBody,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var result = await this.ExecutePostRequestAsync<ImageGenerationResponse>(url, requestBody, cancellationToken);
            return result.Images.Select(x => x.AsBase64).ToList();
        }
        catch (Exception e) when (e is not AIException)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }

    /// <summary>
    /// Explicit finalizer called by IDisposable
    /// </summary>
    public void Dispose()
    {
        this.Dispose(true);
        // Request CL runtime not to call the finalizer - reduce cost of GC
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Overridable finalizer for concrete classes
    /// </summary>
    /// <param name="disposing"></param>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this.HTTPClient.Dispose();
            this._httpClientHandler.Dispose();
            this._retryHandler.Dispose();
        }
    }

    protected virtual string? GetErrorMessageFromResponse(string? jsonResponsePayload)
    {
        if (jsonResponsePayload is null)
        {
            return null;
        }

        try
        {
            JsonNode? root = JsonSerializer.Deserialize<JsonNode>(jsonResponsePayload);

            return root?["error"]?["message"]?.GetValue<string>();
        }
        catch (Exception ex) when (ex is NotSupportedException or JsonException)
        {
            this.Log.LogTrace("Unable to extract error from response body content. Exception: {0}:{1}", ex.GetType(), ex.Message);
            return null;
        }
    }

    #region private ================================================================================

    // HTTP user agent sent to remote endpoints
    private const string HTTPUseragent = "Microsoft Semantic Kernel";

    private async Task<T> ExecutePostRequestAsync<T>(string url, string requestBody, CancellationToken cancellationToken = default)
    {
        string responseJson;

        try
        {
            using HttpContent content = new StringContent(requestBody, Encoding.UTF8, "application/json");
            HttpResponseMessage response = await this.HTTPClient.PostAsync(url, content, cancellationToken);

            if (response == null)
            {
                throw new AIException(AIException.ErrorCodes.NoResponse, "Empty response");
            }

            this.Log.LogTrace("HTTP response: {0} {1}", (int)response.StatusCode, response.StatusCode.ToString("G"));

            responseJson = await response.Content.ReadAsStringAsync();
            string? errorDetail = this.GetErrorMessageFromResponse(responseJson);

            if (!response.IsSuccessStatusCode)
            {
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
        }
        catch (Exception e) when (e is not AIException)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }

        try
        {
            var result = Json.Deserialize<T>(responseJson);
            if (result != null) { return result; }

            throw new AIException(
                AIException.ErrorCodes.InvalidResponseContent,
                "Response JSON parse error");
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
