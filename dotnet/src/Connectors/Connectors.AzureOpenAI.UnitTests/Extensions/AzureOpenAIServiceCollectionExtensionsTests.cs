// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
using Microsoft.SemanticKernel.TextToAudio;
using Microsoft.SemanticKernel.TextToImage;
using Moq;
using Moq.Protected;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Extensions;
/// <summary>
/// Unit tests for the service collection extensions in the <see cref="AzureOpenAIServiceCollectionExtensions"/> class.
/// </summary>
public sealed class AzureOpenAIServiceCollectionExtensionsTests : IDisposable
{
    public AzureOpenAIServiceCollectionExtensionsTests()
    {
        this._mockHttpMessageHandler = new Mock<HttpMessageHandler>();

        this._httpResponseMessage = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_test_response.json"))
        };

        this._mockHttpMessageHandler.Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(this._httpResponseMessage);

        this._httpClient = new HttpClient(this._mockHttpMessageHandler.Object);
    }
    private readonly HttpResponseMessage _httpResponseMessage;
    private readonly HttpClient _httpClient;
    private readonly Mock<HttpMessageHandler> _mockHttpMessageHandler;
    #region Chat completion

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._httpResponseMessage.Dispose();
    }
    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    [InlineData(InitializationType.ApiVersion)]
    [InlineData(InitializationType.HttpClient)]
    public async Task ServiceCollectionAddAzureOpenAIChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("https://localhost"), new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(client);

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureOpenAIChatCompletion("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.Services.AddAzureOpenAIChatCompletion("deployment-name", "https://endpoint", credentials),
            InitializationType.ClientInline => builder.Services.AddAzureOpenAIChatCompletion("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.Services.AddAzureOpenAIChatCompletion("deployment-name"),
            InitializationType.ApiVersion => builder.Services.AddAzureOpenAIChatCompletion("deployment-name", "https://endpoint", "api-key", apiVersion: "2024-10-01-preview"),
            InitializationType.HttpClient => builder.Services.AddAzureOpenAIChatCompletion("deployment-name", "https://localhost", "api-key", httpClient: this._httpClient),
            _ => builder.Services
        };

        // Assert
        var chatCompletionService = builder.Build().GetRequiredService<IChatCompletionService>();
        Assert.True(chatCompletionService is AzureOpenAIChatCompletionService);

        var textGenerationService = builder.Build().GetRequiredService<ITextGenerationService>();
        Assert.True(textGenerationService is AzureOpenAIChatCompletionService);

        if (type == InitializationType.HttpClient) //Verify that the httpclient passed in is used
        {
            await chatCompletionService.GetChatMessageContentAsync("what is the weather");
            this._mockHttpMessageHandler.Protected().Verify("SendAsync", Times.Once(), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        }
    }

    #endregion

    #region Text embeddings

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    [InlineData(InitializationType.ApiVersion)]
    [InlineData(InitializationType.HttpClient)]
    public void ServiceCollectionAddAzureOpenAITextEmbeddingGenerationAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("https://localhost"), new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<AzureOpenAIClient>(client);

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureOpenAITextEmbeddingGeneration("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.Services.AddAzureOpenAITextEmbeddingGeneration("deployment-name", "https://endpoint", credentials),
            InitializationType.ClientInline => builder.Services.AddAzureOpenAITextEmbeddingGeneration("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.Services.AddAzureOpenAITextEmbeddingGeneration("deployment-name"),
            InitializationType.ApiVersion => builder.Services.AddAzureOpenAITextEmbeddingGeneration("deployment-name", "https://endpoint", "api-key", apiVersion: "2024-10-01-preview"),
            InitializationType.HttpClient => builder.Services.AddAzureOpenAITextEmbeddingGeneration("deployment-name", "https://endpoint", "api-key", httpClient: this._httpClient),
            _ => builder.Services
        };

        // Assert
        var service = builder.Build().GetRequiredService<ITextEmbeddingGenerationService>();

        Assert.NotNull(service);
        Assert.True(service is AzureOpenAITextEmbeddingGenerationService);
    }

    #endregion

    #region Text to audio

    [Fact]
    public void ServiceCollectionAddAzureOpenAITextToAudioAddsValidService()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddAzureOpenAITextToAudio("deployment-name", "https://endpoint", "api-key", apiVersion: "2024-10-01-preview")
            .BuildServiceProvider()
            .GetRequiredService<ITextToAudioService>();

        // Assert
        Assert.IsType<AzureOpenAITextToAudioService>(service);
    }

    #endregion

    #region Text to image

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    [InlineData(InitializationType.ApiVersion)]
    public void ServiceCollectionExtensionsAddAzureOpenAITextToImageService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("https://localhost"), new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<AzureOpenAIClient>(client);

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureOpenAITextToImage("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.Services.AddAzureOpenAITextToImage("deployment-name", "https://endpoint", credentials),
            InitializationType.ClientInline => builder.Services.AddAzureOpenAITextToImage("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.Services.AddAzureOpenAITextToImage("deployment-name"),
            InitializationType.ApiVersion => builder.Services.AddAzureOpenAITextToImage("deployment-name", "https://endpoint", "api-key", apiVersion: "2024-10-01-preview"),
            _ => builder.Services
        };

        // Assert
        var service = builder.Build().GetRequiredService<ITextToImageService>();

        Assert.True(service is AzureOpenAITextToImageService);
    }

    #endregion

    #region Audio to text

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    [InlineData(InitializationType.ApiVersion)]
    public void ServiceCollectionAddAzureOpenAIAudioToTextAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("http://endpoint"), new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<AzureOpenAIClient>(client);

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureOpenAIAudioToText("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.Services.AddAzureOpenAIAudioToText("deployment-name", "https://endpoint", credentials),
            InitializationType.ClientInline => builder.Services.AddAzureOpenAIAudioToText("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.Services.AddAzureOpenAIAudioToText("deployment-name"),
            InitializationType.ApiVersion => builder.Services.AddAzureOpenAIAudioToText("deployment-name", "https://endpoint", "api-key", apiVersion: "2024-10-01-preview"),
            _ => builder.Services
        };

        // Assert
        var service = builder.Build().GetRequiredService<IAudioToTextService>();

        Assert.True(service is AzureOpenAIAudioToTextService);
    }

    #endregion

    public enum InitializationType
    {
        ApiKey,
        TokenCredential,
        ClientInline,
        ClientInServiceProvider,
        ClientEndpoint,
        ApiVersion,
        HttpClient
    }
}
