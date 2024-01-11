// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
using Microsoft.SemanticKernel.TextToImage;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// Unit tests for <see cref="OpenAIServiceCollectionExtensions"/> class.
/// </summary>
public sealed class OpenAIServiceCollectionExtensionsTests : IDisposable
{
    private readonly HttpClient _httpClient;

    public OpenAIServiceCollectionExtensionsTests()
    {
        this._httpClient = new HttpClient();
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.OpenAIClient)]
    public void KernelBuilderAddAzureOpenAITextGenerationAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureOpenAITextGeneration("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.AddAzureOpenAITextGeneration("deployment-name", "https://endpoint", credentials),
            InitializationType.OpenAIClient => builder.AddAzureOpenAITextGeneration("deployment-name", client),
            _ => builder
        };

        // Assert
        var service = builder.Build().GetRequiredService<ITextGenerationService>();

        Assert.NotNull(service);
        Assert.True(service is AzureOpenAITextGenerationService);
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.OpenAIClient)]
    public void ServiceCollectionAddAzureOpenAITextGenerationAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureOpenAITextGeneration("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.Services.AddAzureOpenAITextGeneration("deployment-name", "https://endpoint", credentials),
            InitializationType.OpenAIClient => builder.Services.AddAzureOpenAITextGeneration("deployment-name", client),
            _ => builder.Services
        };

        // Assert
        var service = builder.Build().GetRequiredService<ITextGenerationService>();

        Assert.NotNull(service);
        Assert.True(service is AzureOpenAITextGenerationService);
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.OpenAIClient)]
    public void KernelBuilderAddOpenAITextGenerationAddsValidService(InitializationType type)
    {
        // Arrange
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddOpenAITextGeneration("model-id", "api-key"),
            InitializationType.OpenAIClient => builder.AddOpenAITextGeneration("model-id", client),
            _ => builder
        };

        // Assert
        var service = builder.Build().GetRequiredService<ITextGenerationService>();

        Assert.NotNull(service);
        Assert.True(service is OpenAITextGenerationService);
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.OpenAIClient)]
    public void ServiceCollectionAddOpenAITextGenerationAddsValidService(InitializationType type)
    {
        // Arrange
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddOpenAITextGeneration("model-id", "api-key"),
            InitializationType.OpenAIClient => builder.Services.AddOpenAITextGeneration("model-id", client),
            _ => builder.Services
        };

        // Assert
        var service = builder.Build().GetRequiredService<ITextGenerationService>();

        Assert.NotNull(service);
        Assert.True(service is OpenAITextGenerationService);
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.OpenAIClient)]
    public void KernelBuilderAddAzureOpenAITextEmbeddingGenerationAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureOpenAITextEmbeddingGeneration("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.AddAzureOpenAITextEmbeddingGeneration("deployment-name", "https://endpoint", credentials),
            InitializationType.OpenAIClient => builder.AddAzureOpenAITextEmbeddingGeneration("deployment-name", client),
            _ => builder
        };

        // Assert
        var service = builder.Build().GetRequiredService<ITextEmbeddingGenerationService>();

        Assert.NotNull(service);
        Assert.True(service is AzureOpenAITextEmbeddingGenerationService);
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.OpenAIClient)]
    public void ServiceCollectionAddAzureOpenAITextEmbeddingGenerationAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureOpenAITextEmbeddingGeneration("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.Services.AddAzureOpenAITextEmbeddingGeneration("deployment-name", "https://endpoint", credentials),
            InitializationType.OpenAIClient => builder.Services.AddAzureOpenAITextEmbeddingGeneration("deployment-name", client),
            _ => builder.Services
        };

        // Assert
        var service = builder.Build().GetRequiredService<ITextEmbeddingGenerationService>();

        Assert.NotNull(service);
        Assert.True(service is AzureOpenAITextEmbeddingGenerationService);
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.OpenAIClient)]
    public void KernelBuilderAddOpenAITextEmbeddingGenerationAddsValidService(InitializationType type)
    {
        // Arrange
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddOpenAITextEmbeddingGeneration("model-id", "api-key"),
            InitializationType.OpenAIClient => builder.AddOpenAITextEmbeddingGeneration("model-id", client),
            _ => builder
        };

        // Assert
        var service = builder.Build().GetRequiredService<ITextEmbeddingGenerationService>();

        Assert.NotNull(service);
        Assert.True(service is OpenAITextEmbeddingGenerationService);
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.OpenAIClient)]
    public void ServiceCollectionAddOpenAITextEmbeddingGenerationAddsValidService(InitializationType type)
    {
        // Arrange
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddOpenAITextEmbeddingGeneration("model-id", "api-key"),
            InitializationType.OpenAIClient => builder.Services.AddOpenAITextEmbeddingGeneration("model-id", client),
            _ => builder.Services
        };

        // Assert
        var service = builder.Build().GetRequiredService<ITextEmbeddingGenerationService>();

        Assert.NotNull(service);
        Assert.True(service is OpenAITextEmbeddingGenerationService);
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.OpenAIClient)]
    [InlineData(InitializationType.ChatCompletionWithData)]
    public void KernelBuilderAddAzureOpenAIChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new OpenAIClient("key");
        var config = this.GetCompletionWithDataConfig();
        var builder = Kernel.CreateBuilder();

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureOpenAIChatCompletion("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.AddAzureOpenAIChatCompletion("deployment-name", "https://endpoint", credentials),
            InitializationType.OpenAIClient => builder.AddAzureOpenAIChatCompletion("deployment-name", client),
            InitializationType.ChatCompletionWithData => builder.AddAzureOpenAIChatCompletion(config),
            _ => builder
        };

        // Assert
        var service = builder.Build().GetRequiredService<IChatCompletionService>();

        Assert.NotNull(service);

        if (type == InitializationType.ChatCompletionWithData)
        {
            Assert.True(service is AzureOpenAIChatCompletionWithDataService);
        }
        else
        {
            Assert.True(service is AzureOpenAIChatCompletionService);
        }
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.OpenAIClient)]
    [InlineData(InitializationType.ChatCompletionWithData)]
    public void ServiceCollectionAddAzureOpenAIChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new OpenAIClient("key");
        var config = this.GetCompletionWithDataConfig();
        var builder = Kernel.CreateBuilder();

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureOpenAIChatCompletion("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.Services.AddAzureOpenAIChatCompletion("deployment-name", "https://endpoint", credentials),
            InitializationType.OpenAIClient => builder.Services.AddAzureOpenAIChatCompletion("deployment-name", client),
            InitializationType.ChatCompletionWithData => builder.Services.AddAzureOpenAIChatCompletion(config),
            _ => builder.Services
        };

        // Assert
        var service = builder.Build().GetRequiredService<IChatCompletionService>();

        Assert.NotNull(service);

        if (type == InitializationType.ChatCompletionWithData)
        {
            Assert.True(service is AzureOpenAIChatCompletionWithDataService);
        }
        else
        {
            Assert.True(service is AzureOpenAIChatCompletionService);
        }
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.OpenAIClient)]
    public void KernelBuilderAddOpenAIChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddOpenAIChatCompletion("model-id", "api-key"),
            InitializationType.OpenAIClient => builder.AddOpenAIChatCompletion("model-id", client),
            _ => builder
        };

        // Assert
        var service = builder.Build().GetRequiredService<IChatCompletionService>();

        Assert.NotNull(service);
        Assert.True(service is OpenAIChatCompletionService);
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.OpenAIClient)]
    public void ServiceCollectionAddOpenAIChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddOpenAIChatCompletion("model-id", "api-key"),
            InitializationType.OpenAIClient => builder.Services.AddOpenAIChatCompletion("model-id", client),
            _ => builder.Services
        };

        // Assert
        var service = builder.Build().GetRequiredService<IChatCompletionService>();

        Assert.NotNull(service);
        Assert.True(service is OpenAIChatCompletionService);
    }

    [Fact]
    public void KernelBuilderAddAzureOpenAITextToImageAddsValidService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();

        // Act
        builder = builder.AddAzureOpenAITextToImage("deployment-name", "https://endpoint", "api-key");

        // Assert
        var service = builder.Build().GetRequiredService<ITextToImageService>();

        Assert.NotNull(service);
        Assert.True(service is AzureOpenAITextToImageService);
    }

    [Fact]
    public void ServiceCollectionAddAzureOpenAITextToImageAddsValidService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();

        // Act
        builder.Services.AddAzureOpenAITextToImage("deployment-name", "https://endpoint", "api-key");

        // Assert
        var service = builder.Build().GetRequiredService<ITextToImageService>();

        Assert.NotNull(service);
        Assert.True(service is AzureOpenAITextToImageService);
    }

    [Fact]
    public void KernelBuilderAddOpenAITextToImageAddsValidService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();

        // Act
        builder = builder.AddOpenAITextToImage("model-id", "api-key");

        // Assert
        var service = builder.Build().GetRequiredService<ITextToImageService>();

        Assert.NotNull(service);
        Assert.True(service is OpenAITextToImageService);
    }

    [Fact]
    public void ServiceCollectionAddOpenAITextToImageAddsValidService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();

        // Act
        builder.Services.AddOpenAITextToImage("model-id", "api-key");

        // Assert
        var service = builder.Build().GetRequiredService<ITextToImageService>();

        Assert.NotNull(service);
        Assert.True(service is OpenAITextToImageService);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
    }

    public enum InitializationType
    {
        ApiKey,
        TokenCredential,
        OpenAIClient,
        ChatCompletionWithData
    }

    private AzureOpenAIChatCompletionWithDataConfig GetCompletionWithDataConfig()
    {
        return new()
        {
            CompletionApiKey = "completion-api-key",
            CompletionApiVersion = "completion-v1",
            CompletionEndpoint = "https://completion-endpoint",
            CompletionModelId = "completion-model-id",
            DataSourceApiKey = "data-source-api-key",
            DataSourceEndpoint = "https://data-source-endpoint",
            DataSourceIndex = "data-source-index"
        };
    }
}
