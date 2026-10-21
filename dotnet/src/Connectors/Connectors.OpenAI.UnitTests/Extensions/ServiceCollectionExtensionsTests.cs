// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;
using Microsoft.SemanticKernel.TextToAudio;
using Microsoft.SemanticKernel.TextToImage;
using OpenAI;
using OpenAI.Images;
using Xunit;

#pragma warning disable MEAI001 // Image generation APIs are experimental.

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Extensions;

public class ServiceCollectionExtensionsTests
{
    private const string ObsoleteMessage = "This test is in a deprecated feature will be removed in a future version.";

    #region Chat completion

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    public void ItCanAddChatCompletionService(InitializationType type)
    {
        // Arrange
        var client = new OpenAIClient(new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(client);

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddOpenAIChatCompletion("deployment-name", "https://endpoint", "api-key"),
            InitializationType.ClientInline => builder.Services.AddOpenAIChatCompletion("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.Services.AddOpenAIChatCompletion("deployment-name"),
            _ => builder.Services
        };

        // Assert
        var chatCompletionService = builder.Build().GetRequiredService<IChatCompletionService>();
        Assert.True(chatCompletionService is OpenAIChatCompletionService);

        var textGenerationService = builder.Build().GetRequiredService<ITextGenerationService>();
        Assert.True(textGenerationService is OpenAIChatCompletionService);
    }

    #endregion

    [Fact]
    [Obsolete(ObsoleteMessage)]
    public void ItCanAddTextEmbeddingGenerationService()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAITextEmbeddingGeneration("model", "key")
            .BuildServiceProvider()
            .GetRequiredService<ITextEmbeddingGenerationService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    [Obsolete(ObsoleteMessage)]
    public void ItCanAddTextEmbeddingGenerationServiceWithOpenAIClient()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAITextEmbeddingGeneration("model", new OpenAIClient(new ApiKeyCredential("key")))
            .BuildServiceProvider()
            .GetRequiredService<ITextEmbeddingGenerationService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItCanAddEmbeddingGenerator()
    {
        // Arrange
        var sut = new ServiceCollection();
        // Act
        var service = sut.AddOpenAIEmbeddingGenerator("model", "key")
            .BuildServiceProvider()
            .GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();
        // Assert
        Assert.Equal("model", service.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelId);
    }

    [Fact]
    public void ItCanAddEmbeddingGeneratorServiceWithOpenAIClient()
    {
        var sut = new ServiceCollection();

        var service = sut.AddOpenAIEmbeddingGenerator("model", openAIClient: new OpenAIClient(new ApiKeyCredential("key")))
            .BuildServiceProvider()
            .GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        Assert.Equal("model", service.GetService<EmbeddingGeneratorMetadata>()!.DefaultModelId);
    }

    [Fact]
    public void ItCanAddImageToTextService()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAITextToImage("key", modelId: "model")
            .BuildServiceProvider()
            .GetRequiredService<ITextToImageService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItCanAddTextToAudioService()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAITextToAudio("model", "key")
            .BuildServiceProvider()
            .GetRequiredService<ITextToAudioService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItCanAddAudioToTextService()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAIAudioToText("model", "key")
            .BuildServiceProvider()
            .GetRequiredService<IAudioToTextService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItCanAddAudioToTextServiceWithOpenAIClient()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAIAudioToText("model", new OpenAIClient(new ApiKeyCredential("key")))
            .BuildServiceProvider()
            .GetRequiredService<IAudioToTextService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    [Obsolete(ObsoleteMessage)]
    public void ItCanAddFileService()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAIFiles("key")
            .BuildServiceProvider()
            .GetRequiredService<OpenAIFileService>();
    }

    #region Image Generation

    [Theory]
    [InlineData(InitializationType.ApiKey, null)]
    [InlineData(InitializationType.ApiKey, "images")]
    [InlineData(InitializationType.ClientInline, null)]
    [InlineData(InitializationType.ClientInline, "images")]
    [InlineData(InitializationType.ClientInServiceProvider, null)]
    [InlineData(InitializationType.ClientInServiceProvider, "images")]
    public async Task ItCanAddImageGeneratorServiceAsync(InitializationType type, string? serviceId)
    {
        // Arrange
        using var responseMessage = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("./TestData/text-to-image-b64_json-format-response.json"))
        };
        using var messageHandler = new HttpMessageHandlerStub { ResponseToReturn = responseMessage };
        using var httpClient = new HttpClient(messageHandler, false);
        var client = new OpenAIClient(new ApiKeyCredential("key"), ClientCore.GetOpenAIClientOptions(httpClient));
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(client);
        builder.Services.AddSingleton<ILoggerFactory>(NullLoggerFactory.Instance);
        bool telemetryConfigured = false;
        void configureTelemetry(OpenTelemetryImageGenerator _) => telemetryConfigured = true;
        string sourceName = $"OpenAIImages.{Guid.NewGuid():N}";
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
            InitializationType.ApiKey => builder.Services.AddOpenAIImageGenerator("gpt-image-1", "api-key", organizationId: "organization", serviceId: serviceId, httpClient: httpClient, openTelemetrySourceName: sourceName, openTelemetryConfig: configureTelemetry),
            InitializationType.ClientInline => builder.Services.AddOpenAIImageGenerator("gpt-image-1", client, serviceId, sourceName, configureTelemetry),
            InitializationType.ClientInServiceProvider => builder.Services.AddOpenAIImageGenerator("gpt-image-1", serviceId: serviceId, openTelemetrySourceName: sourceName, openTelemetryConfig: configureTelemetry),
            _ => throw new ArgumentOutOfRangeException(nameof(type))
        };
        using var provider = collection.BuildServiceProvider();
        var service = provider.GetRequiredKeyedService<IImageGenerator>(serviceId);
        var response = await service.GenerateImagesAsync("A sea otter", new Microsoft.Extensions.AI.ImageGenerationOptions
        {
            ImageSize = new System.Drawing.Size(1024, 1024)
        });

        // Assert
        Assert.Same(builder.Services, collection);
        Assert.Equal("gpt-image-1", service.GetService<ImageGeneratorMetadata>()!.DefaultModelId);
        Assert.Same(service, provider.GetRequiredKeyedService<IImageGenerator>(serviceId));
        var image = Assert.IsType<DataContent>(Assert.Single(response.Contents));
        Assert.Equal(Convert.FromBase64String("iVBORw0KGgoAAA=="), image.Data.ToArray());
        Assert.Equal("image/png", image.MediaType);
        Assert.True(telemetryConfigured);
        Assert.NotNull(imageActivity);
        Assert.Equal(sourceName, imageActivity.Source.Name);

        using var request = JsonDocument.Parse(messageHandler.RequestContent!);
        Assert.Equal("gpt-image-1", request.RootElement.GetProperty("model").GetString());
        Assert.Equal("A sea otter", request.RootElement.GetProperty("prompt").GetString());
        Assert.Equal("1024x1024", request.RootElement.GetProperty("size").GetString());
        Assert.Equal(1, request.RootElement.GetProperty("n").GetInt32());
        if (type == InitializationType.ApiKey)
        {
            Assert.Equal("organization", Assert.Single(messageHandler.RequestHeaders!.GetValues("OpenAI-Organization")));
        }
    }

    [Fact]
    public async Task ImageGeneratorCanEditImagesAsync()
    {
        // Arrange
        using var responseMessage = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent("""{"created":1726234481,"output_format":"jpeg","data":[{"b64_json":"AQID"}]}""")
        };
        using var messageHandler = new HttpMessageHandlerStub { ResponseToReturn = responseMessage };
        using var httpClient = new HttpClient(messageHandler, false);
        using var provider = new ServiceCollection()
            .AddOpenAIImageGenerator("gpt-image-1", "api-key", httpClient: httpClient)
            .BuildServiceProvider();
        var service = provider.GetRequiredService<IImageGenerator>();

        // Act
        var response = await service.EditImageAsync(
            new DataContent(new byte[] { 1, 2, 3 }, "image/png") { Name = "input.png" },
            "Make the background red",
            new Microsoft.Extensions.AI.ImageGenerationOptions
            {
                MediaType = "image/jpeg",
                RawRepresentationFactory = _ => new ImageEditOptions { Quality = GeneratedImageQuality.LowQuality }
            });

        // Assert
        var image = Assert.IsType<DataContent>(Assert.Single(response.Contents));
        Assert.Equal(new byte[] { 1, 2, 3 }, image.Data.ToArray());
        Assert.Equal("image/jpeg", image.MediaType);
        Assert.EndsWith("/images/edits", messageHandler.RequestUri!.AbsolutePath);
        Assert.Equal("multipart/form-data", messageHandler.ContentHeaders!.ContentType!.MediaType);
        var request = Encoding.UTF8.GetString(messageHandler.RequestContent!);
        Assert.Contains("input.png", request);
        Assert.Contains("Make the background red", request);
        Assert.Matches("name=\"?quality\"?\\r\\n(?:[^\\r\\n]+\\r\\n)*\\r\\nlow\\r\\n", request);
        Assert.Matches("name=\"?output_format\"?\\r\\n(?:[^\\r\\n]+\\r\\n)*\\r\\njpeg\\r\\n", request);
    }

    [Fact]
    public void ImageGeneratorRequiresRegisteredOpenAIClient()
    {
        // Arrange
        using var provider = new ServiceCollection()
            .AddOpenAIImageGenerator("gpt-image-1")
            .BuildServiceProvider();

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => provider.GetRequiredService<IImageGenerator>());
    }

    #endregion

    public enum InitializationType
    {
        ApiKey,
        ClientInline,
        ClientInServiceProvider,
        ClientEndpoint,
    }
}
