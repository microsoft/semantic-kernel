// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Azure;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
using Microsoft.SemanticKernel.TextToAudio;
using Microsoft.SemanticKernel.TextToImage;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Azure;

/// <summary>
/// Unit tests for <see cref="AzureServiceCollectionExtensions"/> class.
/// </summary>
public sealed class AzureServiceCollectionExtensionsTests : IDisposable
{
    private readonly HttpClient _httpClient;

    public AzureServiceCollectionExtensionsTests()
    {
        this._httpClient = new HttpClient();
    }

    #region Chat completion

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.AzureClientInline)]
    [InlineData(InitializationType.AzureClientInServiceProvider)]
    [InlineData(InitializationType.ChatCompletionWithData)]
    public void KernelBuilderAddAzureAzureChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new OpenAIClient("key");
        var config = this.GetCompletionWithDataConfig();
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<OpenAIClient>(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureAzureChatCompletion("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.AddAzureAzureChatCompletion("deployment-name", "https://endpoint", credentials),
            InitializationType.AzureClientInline => builder.AddAzureAzureChatCompletion("deployment-name", client),
            InitializationType.AzureClientInServiceProvider => builder.AddAzureAzureChatCompletion("deployment-name"),
            InitializationType.ChatCompletionWithData => builder.AddAzureAzureChatCompletion(config),
            _ => builder
        };

        // Assert
        var service = builder.Build().GetRequiredService<IChatCompletionService>();

        Assert.NotNull(service);

        if (type == InitializationType.ChatCompletionWithData)
        {
            Assert.True(service is AzureAzureChatCompletionWithDataService);
        }
        else
        {
            Assert.True(service is AzureAzureChatCompletionService);
        }
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.AzureClientInline)]
    [InlineData(InitializationType.AzureClientInServiceProvider)]
    [InlineData(InitializationType.ChatCompletionWithData)]
    public void ServiceCollectionAddAzureAzureChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new OpenAI ("key");
        var config = this.GetCompletionWithDataConfig();
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<OpenAIClient>(client);

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureAzureChatCompletion("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.Services.AddAzureAzureChatCompletion("deployment-name", "https://endpoint", credentials),
            InitializationType.AzureClientInline => builder.Services.AddAzureAzureChatCompletion("deployment-name", client),
            InitializationType.AzureClientInServiceProvider => builder.Services.AddAzureAzureChatCompletion("deployment-name"),
            InitializationType.ChatCompletionWithData => builder.Services.AddAzureAzureChatCompletion(config),
            _ => builder.Services
        };

        // Assert
        var service = builder.Build().GetRequiredService<IChatCompletionService>();

        Assert.NotNull(service);

        if (type == InitializationType.ChatCompletionWithData)
        {
            Assert.True(service is AzureAzureChatCompletionWithDataService);
        }
        else
        {
            Assert.True(service is AzureAzureChatCompletionService);
        }
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.AzureClientInline)]
    [InlineData(InitializationType.AzureClientInServiceProvider)]
    public void KernelBuilderAddAzureChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<OpenAIClient>(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureChatCompletion("model-id", "api-key"),
            InitializationType.AzureClientInline => builder.AddAzureChatCompletion("model-id", client),
            InitializationType.AzureClientInServiceProvider => builder.AddAzureChatCompletion("model-id"),
            _ => builder
        };

        // Assert
        var service = builder.Build().GetRequiredService<IChatCompletionService>();

        Assert.NotNull(service);
        Assert.True(service is AzureChatCompletionService);
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.AzureClientInline)]
    [InlineData(InitializationType.AzureClientInServiceProvider)]
    public void ServiceCollectionAddAzureChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<OpenAIClient>(client);

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureChatCompletion("model-id", "api-key"),
            InitializationType.AzureClientInline => builder.Services.AddAzureChatCompletion("model-id", client),
            InitializationType.AzureClientInServiceProvider => builder.Services.AddAzureChatCompletion("model-id"),
            _ => builder.Services
        };

        // Assert
        var service = builder.Build().GetRequiredService<IChatCompletionService>();

        Assert.NotNull(service);
        Assert.True(service is AzureChatCompletionService);
    }

    #endregion

    public void Dispose()
    {
        this._httpClient.Dispose();
    }

    public enum InitializationType
    {
        ApiKey,
        TokenCredential,
        AzureClientInline,
        AzureClientInServiceProvider
    }
}
