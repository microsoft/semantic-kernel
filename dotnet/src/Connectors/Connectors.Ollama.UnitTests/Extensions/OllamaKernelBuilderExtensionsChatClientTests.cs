// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using OllamaSharp;
using Xunit;

namespace SemanticKernel.Connectors.Ollama.UnitTests.Extensions;

/// <summary>
/// Unit tests of <see cref="OllamaKernelBuilderExtensions"/> for IChatClient.
/// </summary>
public class OllamaKernelBuilderExtensionsChatClientTests
{
    [Fact]
    public void AddOllamaChatClientNullArgsThrow()
    {
        // Arrange
        IKernelBuilder builder = null!;
        string modelId = "llama3.2";
        var endpoint = new Uri("http://localhost:11434");
        string serviceId = "test_service_id";

        // Act & Assert
        var exception = Assert.Throws<ArgumentNullException>(() => builder.AddOllamaChatClient(modelId, endpoint, serviceId));
        Assert.Equal("builder", exception.ParamName);

        using var httpClient = new HttpClient();
        exception = Assert.Throws<ArgumentNullException>(() => builder.AddOllamaChatClient(modelId, httpClient, serviceId));
        Assert.Equal("builder", exception.ParamName);

        exception = Assert.Throws<ArgumentNullException>(() => builder.AddOllamaChatClient(null, serviceId));
        Assert.Equal("builder", exception.ParamName);
    }

    [Fact]
    public void AddOllamaChatClientWithEndpointValidParametersRegistersService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        string modelId = "llama3.2";
        var endpoint = new Uri("http://localhost:11434");
        string serviceId = "test_service_id";

        // Act
        builder.AddOllamaChatClient(modelId, endpoint, serviceId);

        // Assert
        var kernel = builder.Build();
        Assert.NotNull(kernel.GetRequiredService<IChatClient>());
        Assert.NotNull(kernel.GetRequiredService<IChatClient>(serviceId));
    }

    [Fact]
    public void AddOllamaChatClientWithHttpClientValidParametersRegistersService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        string modelId = "llama3.2";
        using var httpClient = new HttpClient() { BaseAddress = new Uri("http://localhost:11434") };
        string serviceId = "test_service_id";

        // Act
        builder.AddOllamaChatClient(modelId, httpClient, serviceId);

        // Assert
        var kernel = builder.Build();
        Assert.NotNull(kernel.GetRequiredService<IChatClient>());
        Assert.NotNull(kernel.GetRequiredService<IChatClient>(serviceId));
    }

    [Fact]
    public void AddOllamaChatClientWithOllamaClientValidParametersRegistersService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        using var httpClient = new HttpClient() { BaseAddress = new Uri("http://localhost:11434") };
        using var ollamaClient = new OllamaApiClient(httpClient, "llama3.2");
        string serviceId = "test_service_id";

        // Act
        builder.AddOllamaChatClient(ollamaClient, serviceId);

        // Assert
        var kernel = builder.Build();
        Assert.NotNull(kernel.GetRequiredService<IChatClient>());
        Assert.NotNull(kernel.GetRequiredService<IChatClient>(serviceId));
    }

    [Fact]
    public void AddOllamaChatClientWithoutServiceIdRegistersDefaultService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        string modelId = "llama3.2";
        var endpoint = new Uri("http://localhost:11434");

        // Act
        builder.AddOllamaChatClient(modelId, endpoint);

        // Assert
        var kernel = builder.Build();
        Assert.NotNull(kernel.GetRequiredService<IChatClient>());
    }

    [Fact]
    public void AddOllamaChatClientWithHttpClientWithoutServiceIdRegistersDefaultService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        string modelId = "llama3.2";
        using var httpClient = new HttpClient() { BaseAddress = new Uri("http://localhost:11434") };

        // Act
        builder.AddOllamaChatClient(modelId, httpClient);

        // Assert
        var kernel = builder.Build();
        Assert.NotNull(kernel.GetRequiredService<IChatClient>());
    }
}
