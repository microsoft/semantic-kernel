// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Mime;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.AI.OpenAI.Clients;

/// <summary>
/// An abstract OpenAI Client.
/// </summary>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1054:URI-like parameters should not be strings", Justification = "OpenAI users use strings")]
public abstract class OpenAIClientAbstract : IDisposable
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
    private readonly IDelegatingHandlerFactory _handlerFactory = new DefaultHttpRetryHandlerFactory();
    private readonly DelegatingHandler _retryHandler;

    internal OpenAIClientAbstract(ILogger? log = null, IDelegatingHandlerFactory? handlerFactory = null)
    {
        this.Log = log ?? this.Log;
        this._handlerFactory = handlerFactory ?? this._handlerFactory;

        this._httpClientHandler = new() { CheckCertificateRevocationList = true };
        this._retryHandler = this._handlerFactory.Create(this.Log);
        this._retryHandler.InnerHandler = this._httpClientHandler;

        this.HTTPClient = new HttpClient(this._retryHandler);
        this.HTTPClient.DefaultRequestHeaders.Add("User-Agent", HTTPUseragent);
    }

    /// <summary>
    /// Asynchronously sends a completion request for the prompt
    /// </summary>
    /// <param name="url">URL for the completion request API</param>
    /// <param name="requestBody">Prompt to complete</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>The completed text</returns>
    /// <exception cref="AIException">AIException thrown during the request.</exception>
    protected async Task<string> ExecuteCompleteRequestAsync(string url, string requestBody, CancellationToken cancellationToken = default)
    {
        try
        {
            this.Log.LogDebug("Sending completion request to {0}: {1}", url, requestBody);

            var result = await this.ExecutePostRequestAsync<CompletionResponse>(url, requestBody, cancellationToken);
            if (result.Completions.Count < 1)
            {
                throw new AIException(
                    AIException.ErrorCodes.InvalidResponseContent,
                    "Completions not found");
            }

            return result.Completions.First().Text;
        }
        catch (Exception e) when (e is not AIException)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }

    /// <summary>
    /// Asynchronously sends an embedding request for the text.
    /// </summary>
    /// <param name="url"></param>
    /// <param name="requestBody"></param>
    /// <returns></returns>
    /// <exception cref="AIException"></exception>
    protected async Task<IList<Embedding<float>>> ExecuteEmbeddingRequestAsync(string url, string requestBody)
    {
        try
        {
            var result = await this.ExecutePostRequestAsync<EmbeddingResponse>(url, requestBody);
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

    #region private ================================================================================

    // HTTP user agent sent to remote endpoints
    private const string HTTPUseragent = "Microsoft Semantic Kernel";

    private async Task<T> ExecutePostRequestAsync<T>(string url, string requestBody, CancellationToken cancellationToken = default)
    {
        string responseJson;

        try
        {
            using HttpContent content = new StringContent(requestBody, Encoding.UTF8, MediaTypeNames.Application.Json);
            HttpResponseMessage response = await this.HTTPClient.PostAsync(url, content, cancellationToken);

            if (response == null)
            {
                throw new AIException(AIException.ErrorCodes.NoResponse, "Empty response");
            }

            this.Log.LogTrace("HTTP response: {0} {1}", (int)response.StatusCode, response.StatusCode.ToString("G"));

            responseJson = await response.Content.ReadAsStringAsync();
            if (!response.IsSuccessStatusCode)
            {
                switch (response.StatusCode)
                {
                    case HttpStatusCode.BadRequest:
                    case HttpStatusCode.MethodNotAllowed:
                    case HttpStatusCode.NotFound:
                    case HttpStatusCode.NotAcceptable:
                    case HttpStatusCode.Conflict:
                    case HttpStatusCode.Gone:
                    case HttpStatusCode.LengthRequired:
                    case HttpStatusCode.PreconditionFailed:
                    case HttpStatusCode.RequestEntityTooLarge:
                    case HttpStatusCode.RequestUriTooLong:
                    case HttpStatusCode.UnsupportedMediaType:
                    case HttpStatusCode.RequestedRangeNotSatisfiable:
                    case HttpStatusCode.ExpectationFailed:
                    case HttpStatusCode.MisdirectedRequest:
                    case HttpStatusCode.UnprocessableEntity:
                    case HttpStatusCode.Locked:
                    case HttpStatusCode.FailedDependency:
                    case HttpStatusCode.UpgradeRequired:
                    case HttpStatusCode.PreconditionRequired:
                    case HttpStatusCode.RequestHeaderFieldsTooLarge:
                    case HttpStatusCode.HttpVersionNotSupported:
                        throw new AIException(
                            AIException.ErrorCodes.InvalidRequest,
                            $"The request is not valid, HTTP status: {response.StatusCode:G}");

                    case HttpStatusCode.Unauthorized:
                    case HttpStatusCode.Forbidden:
                    case HttpStatusCode.ProxyAuthenticationRequired:
                    case HttpStatusCode.UnavailableForLegalReasons:
                    case HttpStatusCode.NetworkAuthenticationRequired:
                        throw new AIException(
                            AIException.ErrorCodes.AccessDenied,
                            $"The request is not authorized, HTTP status: {response.StatusCode:G}");

                    case HttpStatusCode.RequestTimeout:
                        throw new AIException(
                            AIException.ErrorCodes.RequestTimeout,
                            $"The request timed out, HTTP status: {response.StatusCode:G}");

                    case HttpStatusCode.TooManyRequests:
                        throw new AIException(
                            AIException.ErrorCodes.Throttling,
                            $"Too many requests, HTTP status: {response.StatusCode:G}");

                    case HttpStatusCode.InternalServerError:
                    case HttpStatusCode.NotImplemented:
                    case HttpStatusCode.BadGateway:
                    case HttpStatusCode.ServiceUnavailable:
                    case HttpStatusCode.GatewayTimeout:
                    case HttpStatusCode.InsufficientStorage:
                        throw new AIException(
                            AIException.ErrorCodes.ServiceError,
                            $"The service failed to process the request, HTTP status: {response.StatusCode:G}");

                    default:
                        throw new AIException(
                            AIException.ErrorCodes.UnknownError,
                            $"Unexpected HTTP response, status: {response.StatusCode:G}");
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

    /// <summary>
    /// C# finalizer
    /// </summary>
    ~OpenAIClientAbstract()
    {
        this.Dispose(false);
    }

    #endregion
}
