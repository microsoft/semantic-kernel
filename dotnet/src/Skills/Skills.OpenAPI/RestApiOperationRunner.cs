// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
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
    /// List of payload builders/factories.
    /// </summary>
    private readonly Dictionary<string, HttpContentFactory> _payloadFactoryByMediaType;

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
    /// Determines whether the operation payload is constructed dynamically based on operation payload metadata.
    /// If false, the operation payload must be provided via the 'payload' property.
    /// </summary>
    private readonly bool _enableDynamicPayload;

    /// <summary>
    /// Determines whether payload parameters are resolved from the arguments by
    /// full name (parameter name prefixed with the parent property name).
    /// </summary>
    private readonly bool _enablePayloadNamespacing;

    /// <summary>
    /// Creates an instance of the <see cref="RestApiOperationRunner"/> class.
    /// </summary>
    /// <param name="httpClient">An instance of the HttpClient class.</param>
    /// <param name="authCallback">Optional callback for adding auth data to the API requests.</param>
    /// <param name="userAgent">Optional request-header field containing information about the user agent originating the request.</param>
    /// <param name="enableDynamicPayload">Determines whether the operation payload is constructed dynamically based on operation payload metadata.
    /// If false, the operation payload must be provided via the 'payload' property.
    /// </param>
    /// <param name="enablePayloadNamespacing">Determines whether payload parameters are resolved from the arguments by
    /// full name (parameter name prefixed with the parent property name).</param>
    public RestApiOperationRunner(
        HttpClient httpClient,
        AuthenticateRequestAsyncCallback? authCallback = null,
        string? userAgent = null,
        bool enableDynamicPayload = false,
        bool enablePayloadNamespacing = false)
    {
        this._httpClient = httpClient;
        this._userAgent = userAgent ?? Telemetry.HttpUserAgent;
        this._enableDynamicPayload = enableDynamicPayload;
        this._enablePayloadNamespacing = enablePayloadNamespacing;

        // If no auth callback provided, use empty function
        if (authCallback is null)
        {
            this._authCallback = _ => Task.CompletedTask;
        }
        else
        {
            this._authCallback = authCallback;
        }

        this._payloadFactoryByMediaType = new()
        {
            { MediaTypeApplicationJson, this.BuildJsonPayload },
            { MediaTypeTextPlain, this.BuildPlainTextPayload }
        };
    }

    /// <summary>
    /// Executes the specified <paramref name="operation"/> asynchronously, using the provided <paramref name="config"/>.
    /// </summary>
    /// <param name="operation">The REST API operation to execute.</param>
    /// <param name="config">Configuration for REST API operation run.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The task execution result.</returns>
    public Task<JsonNode?> RunAsync(RestApiOperation operation, RestApiOperationRunConfig config, CancellationToken cancellationToken = default)
    {
        var url = operation.BuildOperationUrl(config.Arguments, config.ServerUrlOverride, config.DocumentUri);

        var headers = operation.RenderHeaders(config.Arguments);

        var payload = this.BuildOperationPayload(operation, config.Arguments);

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

        requestMessage.Headers.Add("User-Agent", !string.IsNullOrWhiteSpace(this._userAgent)
            ? this._userAgent
            : Telemetry.HttpUserAgent);

        if (headers != null)
        {
            foreach (var header in headers)
            {
                requestMessage.Headers.Add(header.Key, header.Value);
            }
        }

        using var responseMessage = await this._httpClient.SendWithSuccessCheckAsync(requestMessage, cancellationToken).ConfigureAwait(false);

        var content = await responseMessage.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        // First iteration allowing to associate additional metadata with the returned content.
        var result = new RestApiOperationResponse(
            content,
            responseMessage.Content.Headers.ContentType.ToString());

        return JsonSerializer.SerializeToNode(result);
    }

    /// <summary>
    /// Builds operation payload.
    /// </summary>
    /// <param name="operation">The operation.</param>
    /// <param name="arguments">The payload arguments.</param>
    /// <returns>The HttpContent representing the payload.</returns>
    private HttpContent? BuildOperationPayload(RestApiOperation operation, IDictionary<string, string> arguments)
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

        if (!this._payloadFactoryByMediaType.TryGetValue(mediaType!, out var payloadFactory))
        {
            throw new SKException($"The media type {mediaType} of the {operation.Id} operation is not supported by {nameof(RestApiOperationRunner)}.");
        }

        return payloadFactory.Invoke(operation.Payload, arguments);
    }

    /// <summary>
    /// Builds "application/json" payload.
    /// </summary>
    /// <param name="payloadMetadata">The payload meta-data.</param>
    /// <param name="arguments">The payload arguments.</param>
    /// <returns>The HttpContent representing the payload.</returns>
    private HttpContent BuildJsonPayload(RestApiOperationPayload? payloadMetadata, IDictionary<string, string> arguments)
    {
        //Build operation payload dynamically
        if (this._enableDynamicPayload is true)
        {
            if (payloadMetadata == null)
            {
                throw new SKException("Payload can't be built dynamically due to the missing payload metadata.");
            }

            var payload = this.BuildJsonObject(payloadMetadata.Properties, arguments);

            return new StringContent(payload.ToJsonString(), Encoding.UTF8, MediaTypeApplicationJson);
        }

        //Get operation payload content from the 'payload' argument if dynamic payload building is not required.
        if (!arguments.TryGetValue(RestApiOperation.PayloadArgumentName, out var content))
        {
            throw new SKException($"No argument is found for the '{RestApiOperation.PayloadArgumentName}' payload content.");
        }

        return new StringContent(content, Encoding.UTF8, MediaTypeApplicationJson);
    }

    /// <summary>
    /// Builds a JSON object from a list of RestAPI operation payload properties.
    /// </summary>
    /// <param name="properties">The properties.</param>
    /// <param name="arguments">The arguments.</param>
    /// <param name="propertyNamespace">The namespace to add to the property name.</param>
    /// <returns>The JSON object.</returns>
    private JsonObject BuildJsonObject(IList<RestApiOperationPayloadProperty> properties, IDictionary<string, string> arguments, string? propertyNamespace = null)
    {
        var result = new JsonObject();

        foreach (var propertyMetadata in properties)
        {
            var argumentName = this.GetArgumentNameForPayload(propertyMetadata.Name, propertyNamespace);

            if (propertyMetadata.Type == "object")
            {
                var node = this.BuildJsonObject(propertyMetadata.Properties, arguments, argumentName);
                result.Add(propertyMetadata.Name, node);
                continue;
            }

            if (!arguments.TryGetValue(argumentName, out var propertyValue))
            {
                throw new SKException($"No argument is found for the '{propertyMetadata.Name}' payload property.");
            }

            result.Add(propertyMetadata.Name, ConvertJsonPropertyValueType(propertyValue, propertyMetadata));
        }

        return result;
    }

    /// <summary>
    /// Converts the JSON property value to the REST API type specified in metadata.
    /// </summary>
    /// <param name="propertyValue">The value of the property to be converted.</param>
    /// <param name="propertyMetadata">The metadata of the property.</param>
    /// <returns>A JsonNode representing the converted property value.</returns>
    private static JsonNode? ConvertJsonPropertyValueType(string propertyValue, RestApiOperationPayloadProperty propertyMetadata)
    {
        switch (propertyMetadata.Type)
        {
            case "number":
            {
                if (long.TryParse(propertyValue, out var intValue))
                {
                    return JsonValue.Create(intValue);
                }

                return JsonValue.Create(double.Parse(propertyValue, CultureInfo.InvariantCulture));
            }

            case "boolean":
            {
                return JsonValue.Create(bool.Parse(propertyValue));
            }

            case "integer":
            {
                return JsonValue.Create(int.Parse(propertyValue, CultureInfo.InvariantCulture));
            }

            case "array":
            {
                if (JsonArray.Parse(propertyValue) is JsonArray array)
                {
                    return array;
                }

                throw new SKException($"Can't convert OpenAPI property - {propertyMetadata.Name} value - {propertyValue} of 'array' type to JSON array.");
            }

            case "string":
            {
                return JsonValue.Create(propertyValue);
            }

            default:
            {
                throw new SKException($"Unexpected OpenAPI data type - {propertyMetadata.Type}");
            }
        }
    }

    /// <summary>
    /// Builds "text/plain" payload.
    /// </summary>
    /// <param name="payloadMetadata">The payload meta-data.</param>
    /// <param name="arguments">The payload arguments.</param>
    /// <returns>The HttpContent representing the payload.</returns>
    private HttpContent BuildPlainTextPayload(RestApiOperationPayload? payloadMetadata, IDictionary<string, string> arguments)
    {
        if (!arguments.TryGetValue(RestApiOperation.PayloadArgumentName, out var propertyValue))
        {
            throw new SKException($"No argument is found for the '{RestApiOperation.PayloadArgumentName}' payload content.");
        }

        return new StringContent(propertyValue, Encoding.UTF8, MediaTypeTextPlain);
    }

    /// <summary>
    /// Retrieves the argument name for a payload property.
    /// </summary>
    /// <param name="propertyName">The name of the property.</param>
    /// <param name="propertyNamespace">The namespace to add to the property name (optional).</param>
    /// <returns>The argument name for the payload property.</returns>
    private string GetArgumentNameForPayload(string propertyName, string? propertyNamespace)
    {
        if (this._enablePayloadNamespacing is false)
        {
            return propertyName;
        }

        return string.IsNullOrEmpty(propertyNamespace) ? propertyName : $"{propertyNamespace}.{propertyName}";
    }

    #endregion
}
