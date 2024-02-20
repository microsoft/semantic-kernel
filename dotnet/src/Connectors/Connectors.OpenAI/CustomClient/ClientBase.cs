// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

internal abstract class CustomClientBase
{
    protected IHttpRequestFactory HttpRequestFactory { get; }
    protected IEndpointProvider EndpointProvider { get; }
    protected HttpClient HttpClient { get; }
    protected ILogger Logger { get; }

    protected CustomClientBase(
        HttpClient httpClient,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        ILogger? logger)
    {
        this.HttpClient = httpClient;
        this.HttpRequestFactory = httpRequestFactory;
        this.EndpointProvider = endpointProvider;
        this.Logger = logger ?? NullLogger.Instance;
    }

    protected async Task<string> SendRequestAndGetStringBodyAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        using var response = await this.HttpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        var body = await response.Content.ReadAsStringWithExceptionMappingAsync()
            .ConfigureAwait(false);
        return body;
    }

    protected async Task<HttpResponseMessage> SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        var response = await this.HttpClient.SendWithSuccessCheckAsync(httpRequestMessage, HttpCompletionOption.ResponseHeadersRead, cancellationToken)
            .ConfigureAwait(false);
        return response;
    }

    protected static T DeserializeResponse<T>(string body, JsonSerializerOptions? options = null!)
    {
        try
        {
            T? response = JsonSerializer.Deserialize<T>(body, options);
            if (response is null)
            {
                throw new JsonException("Response is null");
            }

            return response;
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
