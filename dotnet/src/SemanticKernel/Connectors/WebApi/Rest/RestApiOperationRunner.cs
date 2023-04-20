// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.WebApi.Rest.Model;

namespace Microsoft.SemanticKernel.Connectors.WebApi.Rest;

/// <summary>
/// Runs REST API operation represented by RestApiOperation model class.
/// </summary>
internal class RestApiOperationRunner : IRestApiOperationRunner
{
    private const string MediaTypeApplicationJson = "application/json";

    /// <summary>
    /// An instance of the HttpClient class.
    /// </summary>
    private readonly HttpClient _httpClient;

    /// <summary>
    /// Delegate for authorizing the HTTP request.
    /// </summary>
    private readonly AuthenticateRequestAsyncCallback _authCallback;

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperationRunner"/> class.
    /// </summary>
    /// <param name="httpClient">An instance of the HttpClient class.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    public RestApiOperationRunner(HttpClient httpClient, AuthenticateRequestAsyncCallback? authCallback = null)
    {
        this._httpClient = httpClient;

        // If no auth callback provided, use empty function
        if (authCallback == null)
        {
            this._authCallback = (request) => { return Task.CompletedTask; };
        }
        else
        {
            this._authCallback = authCallback;
        }
    }

    /// <inheritdoc/>
    public Task<JsonNode?> RunAsync(RestApiOperation operation, IDictionary<string, string> arguments, CancellationToken cancellationToken = default)
    {
        var url = operation.BuildOperationUrl(arguments);

        var headers = operation.RenderHeaders(arguments);

        var payload = BuildOperationPayload(operation.Payload, arguments);

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
    /// <returns></returns>
    private async Task<JsonNode?> SendAsync(Uri url, HttpMethod method, IDictionary<string, string>? headers = null, HttpContent? payload = null,
        CancellationToken cancellationToken = default)
    {
        using var requestMessage = new HttpRequestMessage(method, url);

        await this._authCallback(requestMessage);

        if (payload != null)
        {
            requestMessage.Content = payload;
        }

        if (headers != null)
        {
            foreach (var header in headers)
            {
                requestMessage.Headers.Add(header.Key, header.Value);
            }
        }

        using var responseMessage = await this._httpClient.SendAsync(requestMessage, cancellationToken).ConfigureAwait(false);

        var content = await responseMessage.Content.ReadAsStringAsync().ConfigureAwait(false);

        responseMessage.EnsureSuccessStatusCode();

        return JsonNode.Parse(content);
    }

    /// <summary>
    /// Builds operation payload.
    /// </summary>
    /// <param name="payloadMetadata">The payload meta-data.</param>
    /// <param name="arguments">The payload arguments.</param>
    /// <returns>The HttpContent representing the payload.</returns>
    private static HttpContent? BuildOperationPayload(RestApiOperationPayload? payloadMetadata, IDictionary<string, string> arguments)
    {
        if (payloadMetadata == null)
        {
            return null;
        }

        if (!s_payloadFactoryByMediaType.TryGetValue(payloadMetadata.MediaType, out var payloadFactory))
        {
            throw new RestApiOperationException($"The media type {payloadMetadata.MediaType} is not supported by {nameof(RestApiOperationRunner)}.");
        }

        return payloadFactory.Invoke(payloadMetadata, arguments);
    }

    /// <summary>
    /// Builds "application/json" payload.
    /// </summary>
    /// <param name="payloadMetadata">The payload meta-data.</param>
    /// <param name="arguments">The payload arguments.</param>    /// <returns></returns>
    /// <returns>The HttpContent representing the payload.</returns>
    private static HttpContent BuildAppJsonPayload(RestApiOperationPayload payloadMetadata, IDictionary<string, string> arguments)
    {
        JsonNode BuildPayload(IList<RestApiOperationPayloadProperty> properties)
        {
            var result = new JsonObject();

            foreach (var propertyMetadata in properties)
            {
                switch (propertyMetadata.Type)
                {
                    case "object":
                    {
                        var propertyValue = BuildPayload(propertyMetadata.Properties);
                        result.Add(propertyMetadata.Name, propertyValue);
                        break;
                    }
                    default: //TODO: Use the default case for unsupported types.
                    {
                        if (!arguments.TryGetValue(propertyMetadata.Name, out var propertyValue))
                        {
                            throw new RestApiOperationException($"No argument is found for the '{propertyMetadata.Name}' payload property.");
                        }

                        result.Add(propertyMetadata.Name, propertyValue);
                        break;
                    }
                }
            }

            return result;
        }

        var payload = BuildPayload(payloadMetadata.Properties);

        return new StringContent(payload.ToJsonString(), Encoding.UTF8, MediaTypeApplicationJson);
        ;
    }

    /// <summary>
    /// List of payload builders/factories.
    /// </summary>
    private static readonly Dictionary<string, Func<RestApiOperationPayload, IDictionary<string, string>, HttpContent>> s_payloadFactoryByMediaType =
        new Dictionary<string, Func<RestApiOperationPayload, IDictionary<string, string>, HttpContent>>()
        {
            { MediaTypeApplicationJson, BuildAppJsonPayload }
        };

    #endregion
}
