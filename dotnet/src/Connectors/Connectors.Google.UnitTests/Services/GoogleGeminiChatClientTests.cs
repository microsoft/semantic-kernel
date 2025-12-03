// Copyright (c) Microsoft. All rights reserved.

#if NET

using System;
using Google.GenAI;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Services;

public sealed class GoogleGeminiChatClientTests
{
    [Fact]
    public void GenAIChatClientShouldBeCreatedWithApiKey()
    {
        // Arrange
        string modelId = "gemini-1.5-pro";
        string apiKey = "test-api-key";

        // Act
        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddGoogleGenAIChatClient(modelId, apiKey);
        var kernel = kernelBuilder.Build();

        // Assert
        var chatClient = kernel.GetRequiredService<IChatClient>();
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void VertexAIChatClientShouldBeCreated()
    {
        // Arrange
        string modelId = "gemini-1.5-pro";

        // Act
        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddGoogleVertexAIChatClient(modelId, project: "test-project", location: "us-central1");
        var kernel = kernelBuilder.Build();

        // Assert - just verify no exception during registration
        // Resolution requires real credentials, so skip that in unit tests
        Assert.NotNull(kernel.Services);
    }

    [Fact]
    public void ChatClientShouldBeCreatedWithGoogleClient()
    {
        // Arrange
        string modelId = "gemini-1.5-pro";
        using var googleClient = new Client(apiKey: "test-api-key");

        // Act
        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddGoogleAIChatClient(modelId, googleClient);
        var kernel = kernelBuilder.Build();

        // Assert
        var chatClient = kernel.GetRequiredService<IChatClient>();
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void GenAIChatClientShouldBeCreatedWithServiceId()
    {
        // Arrange
        string modelId = "gemini-1.5-pro";
        string apiKey = "test-api-key";
        string serviceId = "test-service";

        // Act
        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddGoogleGenAIChatClient(modelId, apiKey, serviceId: serviceId);
        var kernel = kernelBuilder.Build();

        // Assert
        var chatClient = kernel.GetRequiredService<IChatClient>(serviceId);
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void VertexAIChatClientShouldBeCreatedWithServiceId()
    {
        // Arrange
        string modelId = "gemini-1.5-pro";
        string serviceId = "test-service";

        // Act
        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddGoogleVertexAIChatClient(modelId, project: "test-project", location: "us-central1", serviceId: serviceId);
        var kernel = kernelBuilder.Build();

        // Assert - just verify no exception during registration
        // Resolution requires real credentials, so skip that in unit tests
        Assert.NotNull(kernel.Services);
    }

    [Fact]
    public void GenAIChatClientThrowsForNullModelId()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act & Assert
        Assert.ThrowsAny<ArgumentException>(() => kernelBuilder.AddGoogleGenAIChatClient(null!, "apiKey"));
    }

    [Fact]
    public void GenAIChatClientThrowsForEmptyModelId()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act & Assert
        Assert.ThrowsAny<ArgumentException>(() => kernelBuilder.AddGoogleGenAIChatClient("", "apiKey"));
    }

    [Fact]
    public void GenAIChatClientThrowsForNullApiKey()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act & Assert
        Assert.ThrowsAny<ArgumentException>(() => kernelBuilder.AddGoogleGenAIChatClient("modelId", null!));
    }

    [Fact]
    public void GenAIChatClientThrowsForEmptyApiKey()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act & Assert
        Assert.ThrowsAny<ArgumentException>(() => kernelBuilder.AddGoogleGenAIChatClient("modelId", ""));
    }

    [Fact]
    public void VertexAIChatClientThrowsForNullModelId()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act & Assert
        Assert.ThrowsAny<ArgumentException>(() => kernelBuilder.AddGoogleVertexAIChatClient(null!, project: "test-project", location: "us-central1"));
    }

    [Fact]
    public void VertexAIChatClientThrowsForEmptyModelId()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act & Assert
        Assert.ThrowsAny<ArgumentException>(() => kernelBuilder.AddGoogleVertexAIChatClient("", project: "test-project", location: "us-central1"));
    }
}

#endif
