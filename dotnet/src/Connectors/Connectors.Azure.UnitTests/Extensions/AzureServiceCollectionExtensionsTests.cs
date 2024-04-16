// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Azure;
using Xunit;

namespace SemanticKernel.Connectors.Azure.UnitTests;

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
    public void KernelBuilderAddAzureAzureChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureChatCompletion("deployment-name", new Uri("https://endpoint"), "api-key"),
            InitializationType.TokenCredential => builder.AddAzureChatCompletion("deployment-name", new Uri("https://endpoint"), credentials),
            InitializationType.AzureClientInline => builder.AddAzureChatCompletion("deployment-name", client),
            InitializationType.AzureClientInServiceProvider => builder.AddAzureChatCompletion("deployment-name"),
            _ => builder
        };

        // Assert
        var service = builder.Build().GetRequiredService<IChatCompletionService>();

        Assert.NotNull(service);
        Assert.True(service is AzureChatCompletionService);
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.AzureClientInline)]
    [InlineData(InitializationType.AzureClientInServiceProvider)]
    public void ServiceCollectionAddAzureAzureChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<OpenAIClient>(client);

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureChatCompletion("deployment-name", new Uri("https://endpoint"), "api-key"),
            InitializationType.TokenCredential => builder.Services.AddAzureChatCompletion("deployment-name", new Uri("https://endpoint"), credentials),
            InitializationType.AzureClientInline => builder.Services.AddAzureChatCompletion("deployment-name", client),
            InitializationType.AzureClientInServiceProvider => builder.Services.AddAzureChatCompletion("deployment-name"),
            _ => builder.Services
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
    public void KernelBuilderAddAzureChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureChatCompletion("model-id", new Uri("https://endpoint"), "api-key"),
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

        builder.Services.AddSingleton(client);

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureChatCompletion("model-id", new Uri("https://endpoint"), "api-key"),
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
