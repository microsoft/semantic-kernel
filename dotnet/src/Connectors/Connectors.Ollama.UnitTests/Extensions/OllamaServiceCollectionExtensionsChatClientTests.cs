// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using OllamaSharp;
using Xunit;

namespace SemanticKernel.Connectors.Ollama.UnitTests.Extensions;

/// <summary>
/// Unit tests of <see cref="Microsoft.Extensions.DependencyInjection.OllamaServiceCollectionExtensions"/> for IChatClient.
/// </summary>
public class OllamaServiceCollectionExtensionsChatClientTests
{
    [Fact]
    public void AddOllamaChatClientNullArgsThrow()
    {
        // Arrange
        IServiceCollection services = null!;
        string modelId = "llama3.2";
        var endpoint = new Uri("http://localhost:11434");
        string serviceId = "test_service_id";

        // Act & Assert
        var exception = Assert.Throws<ArgumentNullException>(() => services.AddOllamaChatClient(modelId, endpoint, serviceId));
        Assert.Equal("services", exception.ParamName);

        using var httpClient = new HttpClient();
        exception = Assert.Throws<ArgumentNullException>(() => services.AddOllamaChatClient(modelId, httpClient, serviceId));
        Assert.Equal("services", exception.ParamName);

        exception = Assert.Throws<ArgumentNullException>(() => services.AddOllamaChatClient(null, serviceId));
        Assert.Equal("services", exception.ParamName);
    }

    [Fact]
    public void AddOllamaChatClientWithEndpointValidParametersRegistersService()
    {
        // Arrange
        var services = new ServiceCollection();
        string modelId = "llama3.2";
        var endpoint = new Uri("http://localhost:11434");
        string serviceId = "test_service_id";

        // Act
        services.AddOllamaChatClient(modelId, endpoint, serviceId);

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var chatClient = serviceProvider.GetKeyedService<IChatClient>(serviceId);
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void AddOllamaChatClientWithHttpClientValidParametersRegistersService()
    {
        // Arrange
        var services = new ServiceCollection();
        string modelId = "llama3.2";
        using var httpClient = new HttpClient() { BaseAddress = new Uri("http://localhost:11434") };
        string serviceId = "test_service_id";

        // Act
        services.AddOllamaChatClient(modelId, httpClient, serviceId);

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var chatClient = serviceProvider.GetKeyedService<IChatClient>(serviceId);
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void AddOllamaChatClientWithOllamaClientValidParametersRegistersService()
    {
        // Arrange
        var services = new ServiceCollection();
        using var httpClient = new HttpClient() { BaseAddress = new Uri("http://localhost:11434") };
        using var ollamaClient = new OllamaApiClient(httpClient, "llama3.2");
        string serviceId = "test_service_id";

        // Act
        services.AddOllamaChatClient(ollamaClient, serviceId);

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var chatClient = serviceProvider.GetKeyedService<IChatClient>(serviceId);
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void AddOllamaChatClientWorksWithKernel()
    {
        // Arrange
        var services = new ServiceCollection();
        string modelId = "llama3.2";
        var endpoint = new Uri("http://localhost:11434");
        string serviceId = "test_service_id";

        // Act
        services.AddOllamaChatClient(modelId, endpoint, serviceId);
        services.AddKernel();

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var kernel = serviceProvider.GetRequiredService<Kernel>();

        var serviceFromCollection = serviceProvider.GetKeyedService<IChatClient>(serviceId);
        var serviceFromKernel = kernel.GetRequiredService<IChatClient>(serviceId);

        Assert.NotNull(serviceFromKernel);
        Assert.Same(serviceFromCollection, serviceFromKernel);
    }

    [Fact]
    public void AddOllamaChatClientWithoutServiceIdRegistersDefaultService()
    {
        // Arrange
        var services = new ServiceCollection();
        string modelId = "llama3.2";
        var endpoint = new Uri("http://localhost:11434");

        // Act
        services.AddOllamaChatClient(modelId, endpoint);

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var chatClient = serviceProvider.GetService<IChatClient>();
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void AddOllamaChatClientWithHttpClientWithoutServiceIdRegistersDefaultService()
    {
        // Arrange
        var services = new ServiceCollection();
        string modelId = "llama3.2";
        using var httpClient = new HttpClient() { BaseAddress = new Uri("http://localhost:11434") };

        // Act
        services.AddOllamaChatClient(modelId, httpClient);

        // Assert
        var serviceProvider = services.BuildServiceProvider();
        var chatClient = serviceProvider.GetService<IChatClient>();
        Assert.NotNull(chatClient);
    }
}
