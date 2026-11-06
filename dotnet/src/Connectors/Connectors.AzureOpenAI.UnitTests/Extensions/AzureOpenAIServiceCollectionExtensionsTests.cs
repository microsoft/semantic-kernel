// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
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

#pragma warning disable MEAI001 // Image generation APIs are experimental.

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Extensions;
/// <summary>
/// Unit tests for the service collection extensions in the <see cref="Microsoft.SemanticKernel.AzureOpenAIServiceCollectionExtensions"/> class.
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
    [Obsolete("Temporary Obsoleted AzureOpenAITextEmbeddingGeneration tests.")]
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

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    [InlineData(InitializationType.ApiVersion)]
    [InlineData(InitializationType.HttpClient)]
    public void ServiceCollectionAddAzureOpenAIEmbeddingGeneratorAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("https://localhost"), new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<AzureOpenAIClient>(client);

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureOpenAIEmbeddingGenerator("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.Services.AddAzureOpenAIEmbeddingGenerator("deployment-name", "https://endpoint", credentials),
            InitializationType.ClientInline => builder.Services.AddAzureOpenAIEmbeddingGenerator("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.Services.AddAzureOpenAIEmbeddingGenerator("deployment-name"),
            InitializationType.ApiVersion => builder.Services.AddAzureOpenAIEmbeddingGenerator("deployment-name", "https://endpoint", "api-key", apiVersion: "2024-10-01-preview"),
            InitializationType.HttpClient => builder.Services.AddAzureOpenAIEmbeddingGenerator("deployment-name", "https://endpoint", "api-key", httpClient: this._httpClient),
            _ => builder.Services
        };

        // Assert
        var service = builder.Build().GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        Assert.NotNull(service);
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

    #region Image Generation

    [Theory]
    [InlineData(InitializationType.ApiKey, null)]
    [InlineData(InitializationType.ApiKey, "images")]
    [InlineData(InitializationType.TokenCredential, null)]
    [InlineData(InitializationType.TokenCredential, "images")]
    [InlineData(InitializationType.ClientInline, null)]
    [InlineData(InitializationType.ClientInline, "images")]
    [InlineData(InitializationType.ClientInServiceProvider, null)]
    [InlineData(InitializationType.ClientInServiceProvider, "images")]
    [InlineData(InitializationType.ApiVersion, null)]
    [InlineData(InitializationType.ApiVersion, "images")]
    [InlineData(InitializationType.HttpClient, null)]
    [InlineData(InitializationType.HttpClient, "images")]
    public async Task ServiceCollectionAddAzureOpenAIImageGeneratorAddsValidServiceAsync(InitializationType type, string? serviceId)
    {
        // Arrange
        using var responseMessage = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("./TestData/text-to-image-b64_json-format-response.json"))
        };
        using var messageHandler = new HttpMessageHandlerStub { ResponseToReturn = responseMessage };
        using var httpClient = new HttpClient(messageHandler, false);
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken("test-token", DateTimeOffset.UtcNow.AddHours(1)));
        var client = new AzureOpenAIClient(
            new Uri("https://endpoint"),
            new ApiKeyCredential("key"),
            AzureClientCore.GetAzureOpenAIClientOptions(httpClient));
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(client);
        builder.Services.AddSingleton(httpClient);
        builder.Services.AddSingleton<ILoggerFactory>(NullLoggerFactory.Instance);
        bool telemetryConfigured = false;
        void configureTelemetry(OpenTelemetryImageGenerator _) => telemetryConfigured = true;
        string sourceName = $"AzureOpenAIImages.{Guid.NewGuid():N}";
        Activity? imageActivity = null;
        using var listener = new ActivityListener
        {
            ShouldListenTo = source => source.Name == sourceName,
            Sample = (ref ActivityCreationOptions<ActivityContext> _) => ActivitySamplingResult.AllData,
            ActivityStopped = activity => imageActivity = activity
        };
        ActivitySource.AddActivityListener(listener);

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAzureOpenAIImageGenerator("deployment-name", "https://endpoint", "api-key", serviceId, httpClient: httpClient, openTelemetrySourceName: sourceName, openTelemetryConfig: configureTelemetry),
            InitializationType.TokenCredential => builder.Services.AddAzureOpenAIImageGenerator("deployment-name", "https://endpoint", credentials, serviceId, httpClient: httpClient, openTelemetrySourceName: sourceName, openTelemetryConfig: configureTelemetry),
            InitializationType.ClientInline => builder.Services.AddAzureOpenAIImageGenerator("deployment-name", client, serviceId, sourceName, configureTelemetry),
            InitializationType.ClientInServiceProvider => builder.Services.AddAzureOpenAIImageGenerator("deployment-name", serviceId: serviceId, openTelemetrySourceName: sourceName, openTelemetryConfig: configureTelemetry),
            InitializationType.ApiVersion => builder.Services.AddAzureOpenAIImageGenerator("deployment-name", "https://endpoint", "api-key", serviceId, apiVersion: "2025-04-01-preview", httpClient: httpClient, openTelemetrySourceName: sourceName, openTelemetryConfig: configureTelemetry),
            InitializationType.HttpClient => builder.Services.AddAzureOpenAIImageGenerator("deployment-name", "https://endpoint", "api-key", serviceId, openTelemetrySourceName: sourceName, openTelemetryConfig: configureTelemetry),
            _ => throw new ArgumentOutOfRangeException(nameof(type))
        };
        using var provider = collection.BuildServiceProvider();
        var service = provider.GetRequiredKeyedService<IImageGenerator>(serviceId);
        var response = await service.GenerateImagesAsync("A sea otter", new ImageGenerationOptions
        {
            ImageSize = new System.Drawing.Size(1024, 1024)
        });

        // Assert
        Assert.Same(builder.Services, collection);
        Assert.Equal("deployment-name", service.GetService<ImageGeneratorMetadata>()!.DefaultModelId);
        Assert.Same(service, provider.GetRequiredKeyedService<IImageGenerator>(serviceId));
        var image = Assert.IsType<DataContent>(Assert.Single(response.Contents));
        Assert.Equal(Convert.FromBase64String("iVBORw0KGgoAAA=="), image.Data.ToArray());
        Assert.Equal("image/png", image.MediaType);
        Assert.True(telemetryConfigured);
        Assert.NotNull(imageActivity);
        Assert.Equal(sourceName, imageActivity.Source.Name);
        Assert.Equal("endpoint", messageHandler.RequestUri!.Host);

        using var request = JsonDocument.Parse(messageHandler.RequestContent!);
        Assert.Equal("deployment-name", request.RootElement.GetProperty("model").GetString());
        Assert.Equal("A sea otter", request.RootElement.GetProperty("prompt").GetString());
        Assert.Equal("1024x1024", request.RootElement.GetProperty("size").GetString());
        Assert.Equal(1, request.RootElement.GetProperty("n").GetInt32());
        if (type == InitializationType.ApiVersion)
        {
            Assert.Contains("api-version=2025-04-01-preview", messageHandler.RequestUri.Query);
        }
        if (type == InitializationType.TokenCredential)
        {
            Assert.Equal("Bearer", messageHandler.RequestHeaders!.Authorization!.Scheme);
            Assert.Equal("test-token", messageHandler.RequestHeaders.Authorization.Parameter);
        }
    }

    [Fact]
    public async Task ImageGeneratorCanEditImagesAsync()
    {
        // Arrange
        using var responseMessage = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent("""{"created":1726234481,"data":[{"b64_json":"AQID"}]}""")
        };
        using var messageHandler = new HttpMessageHandlerStub { ResponseToReturn = responseMessage };
        using var httpClient = new HttpClient(messageHandler, false);
        using var provider = new ServiceCollection()
            .AddAzureOpenAIImageGenerator("deployment-name", "https://endpoint", "api-key", apiVersion: "2025-04-01-preview", httpClient: httpClient)
            .BuildServiceProvider();
        var service = provider.GetRequiredService<IImageGenerator>();

        // Act
        var response = await service.EditImageAsync(
            new DataContent(new byte[] { 1, 2, 3 }, "image/png") { Name = "input.png" },
            "Make the background red");

        // Assert
        var image = Assert.IsType<DataContent>(Assert.Single(response.Contents));
        Assert.Equal(new byte[] { 1, 2, 3 }, image.Data.ToArray());
        Assert.Equal("image/png", image.MediaType);
        Assert.Equal("endpoint", messageHandler.RequestUri!.Host);
        Assert.EndsWith("/images/edits", messageHandler.RequestUri.AbsolutePath);
        Assert.Contains("api-version=2025-04-01-preview", messageHandler.RequestUri.Query);
        Assert.Equal("multipart/form-data", messageHandler.ContentHeaders!.ContentType!.MediaType);
    }

    [Fact]
    public void ImageGeneratorRequiresRegisteredAzureOpenAIClient()
    {
        // Arrange
        using var provider = new ServiceCollection()
            .AddAzureOpenAIImageGenerator("deployment-name")
            .BuildServiceProvider();

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => provider.GetRequiredService<IImageGenerator>());
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
