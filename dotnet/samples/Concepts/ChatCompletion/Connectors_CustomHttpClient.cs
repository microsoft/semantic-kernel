// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;
using Xunit.Abstractions;

namespace ChatCompletion;

// These examples show how to use a custom HttpClient with SK connectors.
public class Connectors_CustomHttpClient(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Demonstrates the usage of the default HttpClient provided by the SK SDK.
    /// </summary>
    [Fact]
    public void UseDefaultHttpClient()
    {
        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey) // If you need to use the default HttpClient from the SK SDK, simply omit the argument for the httpMessageInvoker parameter.
            .Build();
    }

    /// <summary>
    /// Demonstrates the usage of a custom HttpClient.
    /// </summary>
    [Fact]
    public void UseCustomHttpClient()
    {
        using var httpClient = new HttpClient();

        // If you need to use a custom HttpClient, simply pass it as an argument for the httpClient parameter.
        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey,
                httpClient: httpClient)
            .Build();
    }

    /// <summary>
    /// Demonstrates how to use a custom DelegatingHandler to send the 'api-key' header
    /// and 'api-version' parameter required by Azure AI Foundry / Model Catalog deployments (resolves #10455).
    /// </summary>
    [Fact]
    public void UseCustomHttpClientWithApiKeyHeaderForAzureAIFoundry()
    {
        // Azure AI Foundry model inference endpoints (e.g. Phi-3, Mistral, Llama) require an 'api-key' header
        // and an 'api-version' query parameter rather than the standard OpenAI 'Authorization: Bearer' token.
        using var handler = new AzureAIFoundryApiKeyHandler("test-api-key");
        using var httpClient = new HttpClient(handler);

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "Phi-3-small-8k-instruct",
                endpoint: new Uri("https://my-resource.services.ai.azure.com/models"),
                apiKey: "test-api-key",
                httpClient: httpClient)
            .Build();

        Assert.NotNull(kernel);
    }

    /// <summary>
    /// Verifies that AzureAIFoundryApiKeyHandler injects the 'api-key' header and 'api-version'
    /// query parameter, and preserves existing values without contacting external services.
    /// </summary>
    [Fact]
    public async Task AzureAIFoundryApiKeyHandler_InjectsHeaderAndApiVersionAsync()
    {
        HttpRequestMessage? capturedRequest = null;
        var innerHandler = new RecordingHandler(req => capturedRequest = req);
        using var handler = new AzureAIFoundryApiKeyHandler("my-secret-key", "2024-05-01-preview", innerHandler);
        using var invoker = new HttpMessageInvoker(handler);

        using var request = new HttpRequestMessage(HttpMethod.Post, "https://my-resource.services.ai.azure.com/models/chat/completions");
        using var response = await invoker.SendAsync(request, CancellationToken.None);

        Assert.NotNull(capturedRequest);
        Assert.True(capturedRequest.Headers.Contains("api-key"));
        Assert.Equal("my-secret-key", capturedRequest.Headers.GetValues("api-key").First());
        Assert.NotNull(capturedRequest.RequestUri);
        Assert.Contains("api-version=2024-05-01-preview", capturedRequest.RequestUri.Query);
    }

    /// <summary>
    /// Verifies that an existing 'api-key' header is preserved if already set on the request.
    /// </summary>
    [Fact]
    public async Task AzureAIFoundryApiKeyHandler_PreservesExistingHeaderAsync()
    {
        HttpRequestMessage? capturedRequest = null;
        var innerHandler = new RecordingHandler(req => capturedRequest = req);
        using var handler = new AzureAIFoundryApiKeyHandler("default-key", "2024-05-01-preview", innerHandler);
        using var invoker = new HttpMessageInvoker(handler);

        using var request = new HttpRequestMessage(HttpMethod.Post, "https://my-resource.services.ai.azure.com/models/chat/completions?existing=1");
        request.Headers.Add("api-key", "explicit-key");
        using var response = await invoker.SendAsync(request, CancellationToken.None);

        Assert.NotNull(capturedRequest);
        Assert.Equal("explicit-key", capturedRequest.Headers.GetValues("api-key").First());
        Assert.NotNull(capturedRequest.RequestUri);
        Assert.Contains("existing=1", capturedRequest.RequestUri.Query);
        Assert.Contains("api-version=2024-05-01-preview", capturedRequest.RequestUri.Query);
    }

    /// <summary>
    /// DelegatingHandler that injects the 'api-key' header and 'api-version' query parameter
    /// for Azure AI Foundry and OpenAI-compatible endpoints.
    /// </summary>
    private sealed class AzureAIFoundryApiKeyHandler : DelegatingHandler
    {
        private readonly string _apiKey;
        private readonly string _apiVersion;

        public AzureAIFoundryApiKeyHandler(string apiKey, string apiVersion = "2024-05-01-preview", HttpMessageHandler? innerHandler = null)
            : base(innerHandler ?? new HttpClientHandler())
        {
            this._apiKey = apiKey;
            this._apiVersion = apiVersion;
        }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            // 1. Ensure required 'api-key' header is present
            if (!request.Headers.Contains("api-key"))
            {
                request.Headers.Add("api-key", this._apiKey);
            }

            // 2. Ensure required 'api-version' query parameter is present on inference endpoint
            if (request.RequestUri is not null)
            {
                var uriBuilder = new UriBuilder(request.RequestUri);
                if (!uriBuilder.Query.Contains("api-version="))
                {
                    var query = string.IsNullOrEmpty(uriBuilder.Query) ? string.Empty : uriBuilder.Query.TrimStart('?') + "&";
                    query += $"api-version={Uri.EscapeDataString(this._apiVersion)}";
                    uriBuilder.Query = query;
                    request.RequestUri = uriBuilder.Uri;
                }
            }

            return base.SendAsync(request, cancellationToken);
        }
    }

    /// <summary>
    /// In-memory handler for testing HTTP request transformations without live network calls.
    /// </summary>
    private sealed class RecordingHandler(Action<HttpRequestMessage> onRequest) : HttpMessageHandler
    {
        private readonly Action<HttpRequestMessage> _onRequest = onRequest;

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            this._onRequest(request);
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK));
        }
    }
}
