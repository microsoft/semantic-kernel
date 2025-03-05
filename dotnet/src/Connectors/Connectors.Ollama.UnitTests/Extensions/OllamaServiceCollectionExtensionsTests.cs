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
/// Unit tests of <see cref="OllamaServiceCollectionExtensions"/>.
/// </summary>
public class OllamaServiceCollectionExtensionsTests
{
    [Fact]
    public void AddOllamaTextGenerationToServiceCollection()
    {
        var services = new ServiceCollection();
        services.AddOllamaTextGeneration("model", new Uri("http://localhost:11434"));

        var serviceProvider = services.BuildServiceProvider();
        var service = serviceProvider.GetRequiredService<ITextGenerationService>();

        Assert.NotNull(service);
        Assert.IsType<OllamaTextGenerationService>(service);
    }

    [Fact]
    public void AddOllamaChatCompletionToServiceCollection()
    {
        var services = new ServiceCollection();
        services.AddOllamaChatCompletion("model", new Uri("http://localhost:11434"));

        var serviceProvider = services.BuildServiceProvider();
        var service = serviceProvider.GetRequiredService<IChatCompletionService>();

        Assert.NotNull(service);
    }

    [Fact]
    public void AddOllamaChatCompletionFromServiceCollection()
    {
        var services = new ServiceCollection();
        using var ollamaClient = new OllamaApiClient(new Uri("http://localhost:11434"), "model");

        services.AddSingleton(ollamaClient);
        services.AddOllamaChatCompletion();
        var serviceProvider = services.BuildServiceProvider();
        var service = serviceProvider.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(service);
    }

    [Fact]
    public void AddOllamaTextEmbeddingGenerationFromServiceCollection()
    {
        var services = new ServiceCollection();
        using var ollamaClient = new OllamaApiClient(new Uri("http://localhost:11434"), "model");

        services.AddSingleton(ollamaClient);
        services.AddOllamaTextEmbeddingGeneration();
        var serviceProvider = services.BuildServiceProvider();
        var service = serviceProvider.GetRequiredService<ITextEmbeddingGenerationService>();
        Assert.NotNull(service);
    }

    [Fact]
    public void AddOllamaTextEmbeddingsGenerationToServiceCollection()
    {
        var services = new ServiceCollection();
        services.AddOllamaTextEmbeddingGeneration("model", new Uri("http://localhost:11434"));

        var serviceProvider = services.BuildServiceProvider();
        var service = serviceProvider.GetRequiredService<ITextEmbeddingGenerationService>();

        Assert.NotNull(service);
    }

    [Theory]
    [MemberData(nameof(AddOllamaApiClientScenarios))]
    public async Task AddOllamaApiClientEmbeddingsFromServiceCollectionAsync(ServiceCollectionRegistration registration)
    {
        using var myHttpClientHandler = new FakeHttpMessageHandler(File.ReadAllText("TestData/embeddings_test_response.json"));
        using var httpClient = new HttpClient(myHttpClientHandler) { BaseAddress = new Uri("http://localhost:11434"), };
        using var client = new OllamaApiClient(httpClient);
        var services = new ServiceCollection();
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

        ITextEmbeddingGenerationService service;
        if (registration is ServiceCollectionRegistration.KeyedOllamaApiClient
                         or ServiceCollectionRegistration.KeyedIOllamaApiClient)
        {
            service = serviceProvider.GetRequiredKeyedService<ITextEmbeddingGenerationService>(serviceId);
        }
        else
        {
            service = serviceProvider.GetRequiredService<ITextEmbeddingGenerationService>();
        }

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
        var services = new ServiceCollection();
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

        services.AddOllamaChatCompletion(serviceId: serviceId);
        var serviceProvider = services.BuildServiceProvider();

        IChatCompletionService service;
        if (registration is ServiceCollectionRegistration.KeyedOllamaApiClient
                         or ServiceCollectionRegistration.KeyedIOllamaApiClient)
        {
            service = serviceProvider.GetRequiredKeyedService<IChatCompletionService>(serviceId);
        }
        else
        {
            service = serviceProvider.GetRequiredService<IChatCompletionService>();
        }

        Assert.NotNull(service);

        await service.GetChatMessageContentsAsync(new());

        Assert.Equal(1, myHttpClientHandler.InvokedCount);
    }

    [Theory]
    [MemberData(nameof(AddOllamaApiClientScenarios))]
    public async Task AddOllamaApiClientTextGenerationFromServiceCollectionAsync(ServiceCollectionRegistration registration)
    {
        using var myHttpClientHandler = new FakeHttpMessageHandler(File.ReadAllText("TestData/text_generation_test_response_stream.txt"));
        using var httpClient = new HttpClient(myHttpClientHandler) { BaseAddress = new Uri("http://localhost:11434"), };
        using var client = new OllamaApiClient(httpClient, "model");
        var services = new ServiceCollection();
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

        services.AddOllamaTextGeneration(serviceId: serviceId);
        var serviceProvider = services.BuildServiceProvider();

        ITextGenerationService service;
        if (registration is ServiceCollectionRegistration.KeyedOllamaApiClient
                         or ServiceCollectionRegistration.KeyedIOllamaApiClient)
        {
            service = serviceProvider.GetRequiredKeyedService<ITextGenerationService>(serviceId);
        }
        else
        {
            service = serviceProvider.GetRequiredService<ITextGenerationService>();
        }

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
