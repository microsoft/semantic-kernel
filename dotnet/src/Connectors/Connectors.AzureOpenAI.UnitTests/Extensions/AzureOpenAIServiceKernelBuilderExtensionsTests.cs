// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.TextGeneration;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Extensions;

/// <summary>
/// Unit tests for the kernel builder extensions in the <see cref="AzureOpenAIServiceCollectionExtensions"/> class.
/// </summary>
public sealed class AzureOpenAIServiceKernelBuilderExtensionsTests
{
    #region Chat completion

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.OpenAIClientInline)]
    [InlineData(InitializationType.OpenAIClientInServiceProvider)]
    public void KernelBuilderAddAzureOpenAIChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("http://localhost"), "key");
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureOpenAIChatCompletion("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.AddAzureOpenAIChatCompletion("deployment-name", "https://endpoint", credentials),
            InitializationType.OpenAIClientInline => builder.AddAzureOpenAIChatCompletion("deployment-name", client),
            InitializationType.OpenAIClientInServiceProvider => builder.AddAzureOpenAIChatCompletion("deployment-name"),
            _ => builder
        };

        // Assert
        var chatCompletionService = builder.Build().GetRequiredService<IChatCompletionService>();
        Assert.True(chatCompletionService is AzureOpenAIChatCompletionService);

        var textGenerationService = builder.Build().GetRequiredService<ITextGenerationService>();
        Assert.True(textGenerationService is AzureOpenAIChatCompletionService);
    }

    #endregion

    public enum InitializationType
    {
        ApiKey,
        TokenCredential,
        OpenAIClientInline,
        OpenAIClientInServiceProvider,
        OpenAIClientEndpoint,
    }
}
