// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Mime;
using System.Text;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;
using Microsoft.SemanticKernel.Skills.OpenAPI.Rest;
using RestSkills.Authentication;

namespace RestSkills;

/// <summary>
/// Runs REST API operation represented by RestApiOperation model class.
/// </summary>
internal class RestApiOperationRunner : IRestApiOperationRunner
{
    /// <summary>
    /// An instance of the HttpClient class.
    /// </summary>
    private HttpClient _httpClient;

    /// <summary>
    /// The authentication handler.
    /// </summary>
    private readonly IAuthenticationHandler _authenticationHandler;

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperationRunner"/> class.
    /// </summary>
    /// <param name="httpClient">An instance of the HttpClient class.</param>
    /// <param name="authenticationHandler">An instance of authentication handler.</param>
    public RestApiOperationRunner(HttpClient httpClient, IAuthenticationHandler authenticationHandler)
    {
        this._httpClient = httpClient;
        this._authenticationHandler = authenticationHandler;
    }

    /// <inheritdoc/>
    public async Task<JsonNode?> RunAsync(RestApiOperation operation, IDictionary<string, string> arguments, JsonNode? payload = null, CancellationToken cancellationToken = default)
    {
        var uri = operation.BuildOperationUri(arguments);

        var method = operation.Method;

        var headers = operation.Headers;

        return await this.SendAsync(uri, method, headers, payload, cancellationToken);
    }

    #region private

    /// <summary>
    /// Sends an HTTP request.
    /// </summary>
    /// <param name="uri">The uri to send request to.</param>
    /// <param name="method">The HTTP request method.</param>
    /// <param name="payload">The HTTP request payload.</param>
    /// <param name="headers">Headers to include into the HTTP request.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns></returns>
    private async Task<JsonNode?> SendAsync(Uri uri, HttpMethod method, IDictionary<string, string>? headers = null, JsonNode? payload = null, CancellationToken cancellationToken = default)
    {
        using var requestMessage = new HttpRequestMessage(method, uri);

        this._authenticationHandler.AddAuthenticationData(requestMessage);

        if (payload != null)
        {
            requestMessage.Content = new StringContent(payload.ToJsonString(), Encoding.UTF8, MediaTypeNames.Application.Json);
        }

        if (headers != null)
        {
            foreach (var header in headers)
            {
                requestMessage.Headers.Add(header.Key, header.Value);
            }
        }

        using var responseMessage = await this._httpClient.SendAsync(requestMessage, cancellationToken);

        var content = await responseMessage.Content.ReadAsStringAsync();

        responseMessage.EnsureSuccessStatusCode();

        return JsonNode.Parse(content);
    }

    #endregion
}
