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
    public void ChatClientShouldBeCreatedWithApiKey()
    {
        // Arrange
        string modelId = "gemini-1.5-pro";
        string apiKey = "test-api-key";

        // Act
        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddGoogleAIChatClient(modelId, apiKey);
        var kernel = kernelBuilder.Build();

        // Assert
        var chatClient = kernel.GetRequiredService<IChatClient>();
        Assert.NotNull(chatClient);
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
    public void ChatClientShouldBeCreatedWithServiceId()
    {
        // Arrange
        string modelId = "gemini-1.5-pro";
        string apiKey = "test-api-key";
        string serviceId = "test-service";

        // Act
        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddGoogleAIChatClient(modelId, apiKey, serviceId: serviceId);
        var kernel = kernelBuilder.Build();

        // Assert
        var chatClient = kernel.GetRequiredService<IChatClient>(serviceId);
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void ChatClientThrowsForNullModelId()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act & Assert
        Assert.ThrowsAny<ArgumentException>(() => kernelBuilder.AddGoogleAIChatClient(null!, "apiKey"));
    }

    [Fact]
    public void ChatClientThrowsForEmptyModelId()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act & Assert
        Assert.ThrowsAny<ArgumentException>(() => kernelBuilder.AddGoogleAIChatClient("", "apiKey"));
    }

    [Fact]
    public void ChatClientThrowsForNullApiKey()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act & Assert
        Assert.ThrowsAny<ArgumentException>(() => kernelBuilder.AddGoogleAIChatClient("modelId", (string)null!));
    }

    [Fact]
    public void ChatClientThrowsForEmptyApiKey()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act & Assert
        Assert.ThrowsAny<ArgumentException>(() => kernelBuilder.AddGoogleAIChatClient("modelId", ""));
    }
}

#endif
