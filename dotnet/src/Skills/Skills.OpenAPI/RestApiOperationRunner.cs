// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;

namespace Microsoft.SemanticKernel.Skills.OpenAPI;

/// <summary>
/// Runs REST API operation represented by RestApiOperation model class.
/// </summary>
internal sealed class RestApiOperationRunner
{
    private const string MediaTypeApplicationJson = "application/json";
    private const string MediaTypeTextPlain = "text/plain";

    /// <summary>
    /// An instance of the HttpClient class.
    /// </summary>
    private readonly HttpClient _httpClient;

    /// <summary>
    /// Delegate for authorizing the HTTP request.
    /// </summary>
    private readonly AuthenticateRequestAsyncCallback _authCallback;

    /// <summary>
    /// Request-header field containing information about the user agent originating the request
    /// </summary>
    private readonly string? _userAgent;

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperationRunner"/> class.
    /// </summary>
    /// <param name="httpClient">An instance of the HttpClient class.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <param name="userAgent">Optional request-header field containing information about the user agent originating the request</param>
    public RestApiOperationRunner(HttpClient httpClient, AuthenticateRequestAsyncCallback? authCallback = null, string? userAgent = null)
    {
        this._httpClient = httpClient;
        this._userAgent = userAgent;

        // If no auth callback provided, use empty function
        if (authCallback == null)
        {
            this._authCallback = _ => Task.CompletedTask;
        }
        else
        {
            this._authCallback = authCallback;
        }
    }

    public Task<JsonNode?> RunAsync(RestApiOperation operation, IDictionary<string, string> arguments, CancellationToken cancellationToken = default)
    {
        var url = operation.BuildOperationUrl(arguments);

        var headers = operation.RenderHeaders(arguments);

        var payload = BuildOperationPayload(operation, arguments);

        return this.SendAsync(url, operation.Method, headers, payload, cancellationToken);
    }

    #region private

    /// <summary>
    /// Sends an HTTP request.
    /// </summary>
    /// <param name="url">The url to send request to.</param>
    /// <param name="method">The HTTP request method.</param>
    /// <param name="headers">Headers to include into the HTTP request.</param>
    /// <param name="payload">HTTP request payload.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>Response content and content type</returns>
    private async Task<JsonNode?> SendAsync(
        Uri url,
        HttpMethod method,
        IDictionary<string, string>? headers = null,
        HttpContent? payload = null,
        CancellationToken cancellationToken = default)
    {
        using var requestMessage = new HttpRequestMessage(method, url);

        await this._authCallback(requestMessage).ConfigureAwait(false);

        if (payload != null)
        {
            requestMessage.Content = payload;
        }

        if (!string.IsNullOrWhiteSpace(this._userAgent))
        {
            requestMessage.Headers.Add("User-Agent", this._userAgent);
        }

        if (headers != null)
        {
            foreach (var header in headers)
            {
                requestMessage.Headers.Add(header.Key, header.Value);
            }
        }

        using var response = await this._httpClient.SendAsync(requestMessage, cancellationToken).ConfigureAwait(false);

        var content = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

        response.EnsureSuccess(content);

        // First iteration allowing to associate additional metadata with the returned content.
        var result = new RestApiOperationResponse(
            content,
            response.Content.Headers.ContentType.ToString());

        return JsonSerializer.SerializeToNode(result);
    }

    /// <summary>
    /// Builds operation payload.
    /// </summary>
    /// <param name="operation">The operation.</param>
    /// <param name="arguments">The payload arguments.</param>
    /// <returns>The HttpContent representing the payload.</returns>
    private static HttpContent? BuildOperationPayload(RestApiOperation operation, IDictionary<string, string> arguments)
    {
        if (operation?.Method != HttpMethod.Put && operation?.Method != HttpMethod.Post)
        {
            return null;
        }

        var mediaType = operation.Payload?.MediaType;

        // A try to resolve payload content type from the operation arguments if it's missing in the payload metadata.
        if (string.IsNullOrEmpty(mediaType))
        {
            if (!arguments.TryGetValue(RestApiOperation.ContentTypeArgumentName, out mediaType))
            {
                throw new SKException($"No content type is provided for the {operation.Id} operation.");
            }
        }

        if (!s_payloadFactoryByMediaType.TryGetValue(mediaType!, out var payloadFactory))
        {
            throw new SKException($"The media type {mediaType} of the {operation.Id} operation is not supported by {nameof(RestApiOperationRunner)}.");
        }

        return payloadFactory.Invoke(arguments);
    }

    /// <summary>
    /// Builds "application/json" payload.
    /// </summary>
    /// <param name="arguments">The payload arguments.</param>
    /// <returns>The HttpContent representing the payload.</returns>
    private static HttpContent BuildAppJsonPayload(IDictionary<string, string> arguments)
    {
        if (!arguments.TryGetValue(RestApiOperation.PayloadArgumentName, out var content))
        {
            throw new SKException($"No argument is found for the '{RestApiOperation.PayloadArgumentName}' payload content.");
        }

        return new StringContent(content, Encoding.UTF8, MediaTypeApplicationJson);
    }

    /// <summary>
    /// Builds "text/plain" payload.
    /// </summary>
    /// <param name="arguments">The payload arguments.</param>
    /// <returns>The HttpContent representing the payload.</returns>
    private static HttpContent BuildPlainTextPayload(IDictionary<string, string> arguments)
    {
        if (!arguments.TryGetValue(RestApiOperation.PayloadArgumentName, out var propertyValue))
        {
            throw new SKException($"No argument is found for the '{RestApiOperation.PayloadArgumentName}' payload content.");
        }

        return new StringContent(propertyValue, Encoding.UTF8, MediaTypeTextPlain);
    }

    /// <summary>
    /// List of payload builders/factories.
    /// </summary>
    private static readonly Dictionary<string, Func<IDictionary<string, string>, HttpContent>> s_payloadFactoryByMediaType =
        new()
        {
            { MediaTypeApplicationJson, BuildAppJsonPayload },
            { MediaTypeTextPlain, BuildPlainTextPayload }
        };

    #endregion
}
