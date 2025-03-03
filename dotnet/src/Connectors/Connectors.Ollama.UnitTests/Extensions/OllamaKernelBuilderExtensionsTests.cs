// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Ollama;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
using OllamaSharp;
using Xunit;

namespace SemanticKernel.Connectors.Ollama.UnitTests.Extensions;

/// <summary>
/// Unit tests of <see cref="OllamaKernelBuilderExtensions"/>.
/// </summary>
public class OllamaKernelBuilderExtensionsTests
{
    [Fact]
    public void AddOllamaTextGenerationCreatesService()
    {
        var builder = Kernel.CreateBuilder();
        builder.AddOllamaTextGeneration("model", new Uri("http://localhost:11434"));

        var kernel = builder.Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();

        Assert.NotNull(kernel);
        Assert.NotNull(service);
        Assert.IsType<OllamaTextGenerationService>(service);
    }

    [Fact]
    public void AddOllamaChatCompletionCreatesService()
    {
        var builder = Kernel.CreateBuilder();
        builder.AddOllamaChatCompletion("model", new Uri("http://localhost:11434"));

        var kernel = builder.Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        Assert.NotNull(kernel);
        Assert.NotNull(service);
    }

    [Fact]
    public void AddOllamaTextEmbeddingGenerationCreatesService()
    {
        var builder = Kernel.CreateBuilder();
        builder.AddOllamaTextEmbeddingGeneration("model", new Uri("http://localhost:11434"));

        var kernel = builder.Build();
        var service = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        Assert.NotNull(kernel);
        Assert.NotNull(service);
    }

    [Theory]
    [MemberData(nameof(AddOllamaApiClientScenarios))]
    public async Task AddOllamaApiClientEmbeddingsFromServiceCollectionAsync(ServiceCollectionRegistration registration)
    {
        using var myHttpClientHandler = new FakeHttpMessageHandler(File.ReadAllText("TestData/embeddings_test_response.json"));
        using var httpClient = new HttpClient(myHttpClientHandler) { BaseAddress = new Uri("http://localhost:11434"), };
        using var client = new OllamaApiClient(httpClient);
        var builder = Kernel.CreateBuilder();
        var services = builder.Services;

        string? serviceId = null;
        switch (registration)
        {
            case ServiceCollectionRegistration.KeyedOllamaApiClient:
                services.AddKeyedSingleton<OllamaApiClient>(serviceId = "model", client);
                break;
            case ServiceCollectionRegistration.KeyedIOllamaApiClient:
                services.AddKeyedSingleton<IOllamaApiClient>(serviceId = "model", client);
                break;
            case ServiceCollectionRegistration.OllamaApiClient:
                services.AddSingleton<OllamaApiClient>(client);
                break;
            case ServiceCollectionRegistration.Endpoint:
                services.AddSingleton<IOllamaApiClient>(client);
                break;
        }

        services.AddOllamaTextEmbeddingGeneration(serviceId: serviceId);
        var serviceProvider = services.BuildServiceProvider();

        var kernel = builder.Build();

        ITextEmbeddingGenerationService service = kernel.GetRequiredService<ITextEmbeddingGenerationService>(serviceId);

        Assert.NotNull(service);

        await service.GenerateEmbeddingsAsync(["text"]);

        Assert.Equal(1, myHttpClientHandler.InvokedCount);
    }

    [Theory]
    [MemberData(nameof(AddOllamaApiClientScenarios))]
    public async Task AddOllamaApiClientChatCompletionFromServiceCollectionAsync(ServiceCollectionRegistration registration)
    {
        using var myHttpClientHandler = new FakeHttpMessageHandler(File.ReadAllText("TestData/chat_completion_test_response.txt"));
        using var httpClient = new HttpClient(myHttpClientHandler) { BaseAddress = new Uri("http://localhost:11434"), };
        using var client = new OllamaApiClient(httpClient);
        var builder = Kernel.CreateBuilder();
        var services = builder.Services;

        string? serviceId = null;
        switch (registration)
        {
            case ServiceCollectionRegistration.KeyedOllamaApiClient:
                services.AddKeyedSingleton<OllamaApiClient>(serviceId = "model", client);
                break;
            case ServiceCollectionRegistration.KeyedIOllamaApiClient:
                services.AddKeyedSingleton<IOllamaApiClient>(serviceId = "model", client);
                break;
            case ServiceCollectionRegistration.OllamaApiClient:
                services.AddSingleton<OllamaApiClient>(client);
                break;
            case ServiceCollectionRegistration.Endpoint:
                services.AddSingleton<IOllamaApiClient>(client);
                break;
        }

        builder.AddOllamaChatCompletion(serviceId: serviceId);
        var kernel = builder.Build();

        IChatCompletionService service = kernel.GetRequiredService<IChatCompletionService>(serviceId);

        Assert.NotNull(service);

        await service.GetChatMessageContentsAsync(new());

        Assert.Equal(1, myHttpClientHandler.InvokedCount);
    }

    [Theory]
    [MemberData(nameof(AddOllamaApiClientScenarios))]
    public async Task AddOllamaApiClientTextGenerationFromServiceCollectionAsync(ServiceCollectionRegistration registration)
    {
        using var myHttpClientHandler = new FakeHttpMessageHandler(File.ReadAllText("TestData/chat_completion_test_response.txt"));
        using var httpClient = new HttpClient(myHttpClientHandler) { BaseAddress = new Uri("http://localhost:11434"), };
        using var client = new OllamaApiClient(httpClient, "model");
        var builder = Kernel.CreateBuilder();
        var services = builder.Services;

        string? serviceId = null;
        switch (registration)
        {
            case ServiceCollectionRegistration.KeyedOllamaApiClient:
                services.AddKeyedSingleton<OllamaApiClient>(serviceId = "model", client);
                break;
            case ServiceCollectionRegistration.KeyedIOllamaApiClient:
                services.AddKeyedSingleton<IOllamaApiClient>(serviceId = "model", client);
                break;
            case ServiceCollectionRegistration.OllamaApiClient:
                services.AddSingleton<OllamaApiClient>(client);
                break;
            case ServiceCollectionRegistration.Endpoint:
                services.AddSingleton<IOllamaApiClient>(client);
                break;
        }

        builder.AddOllamaTextGeneration(serviceId: serviceId);
        var kernel = builder.Build();

        ITextGenerationService service = kernel.GetRequiredService<ITextGenerationService>(serviceId);

        Assert.NotNull(service);

        await service.GetStreamingTextContentsAsync("test prompt").GetAsyncEnumerator().MoveNextAsync();

        Assert.Equal(1, myHttpClientHandler.InvokedCount);
    }

    public enum ServiceCollectionRegistration
    {
        KeyedOllamaApiClient,
        KeyedIOllamaApiClient,
        OllamaApiClient,
        Endpoint,
    }

    public static TheoryData<ServiceCollectionRegistration> AddOllamaApiClientScenarios => new()
    {
        { ServiceCollectionRegistration.KeyedOllamaApiClient },
        { ServiceCollectionRegistration.KeyedIOllamaApiClient },
        { ServiceCollectionRegistration.OllamaApiClient },
        { ServiceCollectionRegistration.Endpoint },
    };

    private sealed class FakeHttpMessageHandler(string responseContent) : HttpMessageHandler
    {
        public int InvokedCount { get; private set; }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            this.InvokedCount++;

            return Task.FromResult(
                new HttpResponseMessage(HttpStatusCode.OK)
                {
                    Content = new StringContent(responseContent)
                });
        }
    }
}
