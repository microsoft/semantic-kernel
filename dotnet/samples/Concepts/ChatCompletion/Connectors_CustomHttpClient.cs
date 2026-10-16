// Copyright (c) Microsoft. All rights reserved.

using System;
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
    /// required by Azure AI Foundry / Model Catalog deployments (resolves #10455).
    /// </summary>
    [Fact]
    public void UseCustomHttpClientWithApiKeyHeaderForAzureAIFoundry()
    {
        // Azure AI Foundry model inference endpoints (e.g. Phi-3, Mistral, Llama) require an 'api-key' header
        // rather than the standard OpenAI 'Authorization: Bearer' token.
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
    /// DelegatingHandler that injects the 'api-key' header for Azure AI Foundry and OpenAI-compatible endpoints.
    /// </summary>
    private sealed class AzureAIFoundryApiKeyHandler(string apiKey) : DelegatingHandler(new HttpClientHandler())
    {
        private readonly string _apiKey = apiKey;

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            // Ensure the required 'api-key' header is present on outgoing requests
            if (!request.Headers.Contains("api-key"))
            {
                request.Headers.Add("api-key", this._apiKey);
            }

            return base.SendAsync(request, cancellationToken);
        }
    }
}
