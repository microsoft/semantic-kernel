// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Abstract;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core;

internal abstract class ClientBase
{
    protected readonly IHttpRequestFactory HTTPRequestFactory;
    protected readonly IEndpointProvider EndpointProvider;
    protected readonly HttpClient HTTPClient;
    protected readonly ILogger Logger;

    protected ClientBase(
        HttpClient httpClient,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        ILogger? logger)
    {
        this.HTTPClient = httpClient;
        this.HTTPRequestFactory = httpRequestFactory;
        this.EndpointProvider = endpointProvider;
        this.Logger = logger ?? NullLogger.Instance;
    }

    protected static void ValidateMaxTokens(int? maxTokens)
    {
        if (maxTokens is < 1)
        {
            throw new ArgumentException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
        }
    }

    protected async Task<string> SendRequestAndGetStringBodyAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        using var response = await this.HTTPClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        var body = await response.Content.ReadAsStringWithExceptionMappingAsync()
            .ConfigureAwait(false);
        return body;
    }

    protected async Task<HttpResponseMessage> SendRequestAndGetResponseStreamAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        var response = await this.HTTPClient.SendWithSuccessCheckAsync(httpRequestMessage, HttpCompletionOption.ResponseHeadersRead, cancellationToken)
            .ConfigureAwait(false);
        return response;
    }

    protected static T DeserializeResponse<T>(string body)
    {
        try
        {
            T? geminiResponse = JsonSerializer.Deserialize<T>(body);
            if (geminiResponse is null)
            {
                throw new JsonException();
            }

            return geminiResponse;
        }
        catch (JsonException exc)
        {
            throw new KernelException("Unexpected response from model", exc)
            {
                Data = { { "ResponseData", body } },
            };
        }
    }
}
