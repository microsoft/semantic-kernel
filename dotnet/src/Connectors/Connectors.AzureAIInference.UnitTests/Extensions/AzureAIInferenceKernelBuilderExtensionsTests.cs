// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure;
using Azure.AI.Inference;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Connectors.AzureAIInference.UnitTests.Extensions;

public sealed class AzureAIInferenceKernelBuilderExtensionsTests
{
    private readonly Uri _endpoint = new("https://endpoint");

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.BreakingGlassClientInline)]
    [InlineData(InitializationType.BreakingGlassInServiceProvider)]
    public void KernelBuilderAddAzureAIInferenceChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var client = new ChatCompletionsClient(this._endpoint, new AzureKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureAIInferenceChatCompletion("model-id", "api-key", this._endpoint),
            InitializationType.BreakingGlassClientInline => builder.AddAzureAIInferenceChatCompletion("model-id", client),
            InitializationType.BreakingGlassInServiceProvider => builder.AddAzureAIInferenceChatCompletion("model-id", chatClient: null),
            _ => builder
        };

        // Assert
        var chatCompletionService = builder.Build().GetRequiredService<IChatCompletionService>();
        Assert.Equal("ChatClientChatCompletionService", chatCompletionService.GetType().Name);
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.BreakingGlassClientInline)]
    [InlineData(InitializationType.BreakingGlassInServiceProvider)]
    public void KernelBuilderAddAzureAIInferenceChatClientAddsValidService(InitializationType type)
    {
        // Arrange
        var client = new ChatCompletionsClient(this._endpoint, new AzureKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureAIInferenceChatClient("model-id", "api-key", this._endpoint),
            InitializationType.BreakingGlassClientInline => builder.AddAzureAIInferenceChatClient("model-id", client),
            InitializationType.BreakingGlassInServiceProvider => builder.AddAzureAIInferenceChatClient("model-id", chatClient: null),
            _ => builder
        };

        // Assert
        var sut = builder.Build().GetRequiredService<IChatClient>();
        Assert.NotNull(sut);
        Assert.Equal("KernelFunctionInvokingChatClient", sut.GetType().Name);
    }

    public enum InitializationType
    {
        ApiKey,
        BreakingGlassClientInline,
        BreakingGlassInServiceProvider,
    }
}
