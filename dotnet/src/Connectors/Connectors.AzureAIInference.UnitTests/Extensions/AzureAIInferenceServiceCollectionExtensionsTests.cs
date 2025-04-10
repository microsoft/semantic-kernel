// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure;
using Azure.AI.Inference;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Connectors.AzureAIInference.UnitTests.Extensions;

public sealed class AzureAIInferenceServiceCollectionExtensionsTests
{
    private readonly Uri _endpoint = new("https://endpoint");

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    public void ItCanAddChatCompletionService(InitializationType type)
    {
        // Arrange
        var client = new ChatCompletionsClient(this._endpoint, new AzureKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(client);

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureAIInferenceChatCompletion("modelId", "api-key", this._endpoint),
            InitializationType.ClientInline => builder.Services.AddAzureAIInferenceChatCompletion("modelId", client),
            InitializationType.ClientInServiceProvider => builder.Services.AddAzureAIInferenceChatCompletion("modelId", chatClient: null),
            _ => builder.Services
        };

        // Assert
        var chatCompletionService = builder.Build().GetRequiredService<IChatCompletionService>();
        Assert.Equal("ChatClientChatCompletionService", chatCompletionService.GetType().Name);
    }

    public enum InitializationType
    {
        ApiKey,
        ClientInline,
        ChatClientInline,
        ClientInServiceProvider,
    }
}
