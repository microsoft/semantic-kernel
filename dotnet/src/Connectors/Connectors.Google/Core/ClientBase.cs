// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

internal abstract class ClientBase
{
    private readonly Func<ValueTask<string>>? _bearerTokenProvider;

    protected ILogger Logger { get; }

    protected HttpClient HttpClient { get; }

    protected ClientBase(
        HttpClient httpClient,
        ILogger? logger,
        Func<ValueTask<string>> bearerTokenProvider)
        : this(httpClient, logger)
    {
        Verify.NotNull(bearerTokenProvider);
        this._bearerTokenProvider = bearerTokenProvider;
    }

    protected ClientBase(
        HttpClient httpClient,
        ILogger? logger)
    {
        Verify.NotNull(httpClient);

        this.HttpClient = httpClient;
        this.Logger = logger ?? NullLogger.Instance;
    }

    protected static void ValidateMaxTokens(int? maxTokens)
    {
        // If maxTokens is null, it means that the user wants to use the default model value
        if (maxTokens is < 1)
        {
            throw new ArgumentException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
        }
    }

    protected async Task<string> SendRequestAndGetStringBodyAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        using var response = await this.HttpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        var body = await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken)
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

    protected static T DeserializeResponse<T>(string body)
    {
        try
        {
            return JsonSerializer.Deserialize<T>(body) ?? throw new JsonException("Response is null");
        }
        catch (JsonException exc)
        {
            throw new KernelException("Unexpected response from model", exc)
            {
                Data = { { "ResponseData", body } },
            };
        }
    }

    protected async Task<HttpRequestMessage> CreateHttpRequestAsync(object requestData, Uri endpoint)
    {
        var httpRequestMessage = HttpRequest.CreatePostRequest(endpoint, requestData);
        httpRequestMessage.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        httpRequestMessage.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion,
            HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ClientBase)));

        if (this._bearerTokenProvider is not null && await this._bearerTokenProvider().ConfigureAwait(false) is { } bearerKey)
        {
            httpRequestMessage.Headers.Authorization =
                new AuthenticationHeaderValue("Bearer", bearerKey);
        }

        return httpRequestMessage;
    }

    protected static string GetApiVersionSubLink(GoogleAIVersion apiVersion)
        => apiVersion switch
        {
            GoogleAIVersion.V1 => "v1",
            GoogleAIVersion.V1_Beta => "v1beta",
            _ => throw new NotSupportedException($"Google API version {apiVersion} is not supported.")
        };

    protected static string GetApiVersionSubLink(VertexAIVersion apiVersion)
        => apiVersion switch
        {
            VertexAIVersion.V1 => "v1",
            VertexAIVersion.V1_Beta => "v1beta1",
            _ => throw new NotSupportedException($"Vertex API version {apiVersion} is not supported.")
        };
}
