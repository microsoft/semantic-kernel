// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime;
using Amazon.Runtime.Endpoints;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Amazon.UnitTests;

/// <summary>
/// Unit tests for the BedrockServiceCollectionExtension class.
/// </summary>
public sealed class BedrockServiceCollectionExtensionTests : IDisposable
{
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;
    private readonly Mock<ILogger<BedrockServiceCollectionExtensionTests>> _mockLogger;

    public BedrockServiceCollectionExtensionTests()
    {
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
        this._mockLogger = new Mock<ILogger<BedrockServiceCollectionExtensionTests>>();
        this._mockLoggerFactory.Setup(lf => lf.CreateLogger(It.IsAny<string>())).Returns(this._mockLogger.Object);
        this._mockLogger.Setup(l => l.IsEnabled(It.IsAny<LogLevel>())).Returns(true);
    }
    /// <summary>
    /// Ensures that IServiceCollection.AddBedrockChatCompletionService registers the <see cref="IChatCompletionService"/> with the correct implementation.
    /// </summary>
    [Fact]
    public void AddBedrockChatCompletionServiceRegistersCorrectService()
    {
        // Arrange
        var services = new ServiceCollection();
        var modelId = "amazon.titan-text-premier-v1:0";
        var bedrockRuntime = new Mock<IAmazonBedrockRuntime>().Object;

        // Act
        services.AddBedrockChatCompletionService(modelId, bedrockRuntime);
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatService = serviceProvider.GetService<IChatCompletionService>();
        Assert.NotNull(chatService);
        Assert.IsType<BedrockChatCompletionService>(chatService);
    }

    /// <summary>
    /// Ensures that IServiceCollection.AddBedrockTextGenerationService registers the <see cref="ITextGenerationService"/> with the correct implementation.
    /// </summary>
    [Fact]
    public void AddBedrockTextGenerationServiceRegistersCorrectService()
    {
        // Arrange
        var services = new ServiceCollection();
        var modelId = "amazon.titan-text-premier-v1:0";
        var bedrockRuntime = new Mock<IAmazonBedrockRuntime>().Object;

        // Act
        services.AddBedrockTextGenerationService(modelId, bedrockRuntime);
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var textGenerationService = serviceProvider.GetService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<BedrockTextGenerationService>(textGenerationService);
    }

    /// <summary>
    /// Ensures that IServiceCollection.AddBedrockTextEmbeddingGenerationService registers the <see cref="ITextEmbeddingGenerationService"/> with the correct implementation.
    /// </summary>
    [Fact]
    [Obsolete("This test is deprecated and will be removed in a future release.")]
    public void AddBedrockTextEmbeddingServiceRegistersCorrectService()
    {
        // Arrange
        var services = new ServiceCollection();
        var modelId = "amazon.titan-embed-text-v2:0";
        var bedrockRuntime = new Mock<IAmazonBedrockRuntime>().Object;

        // Act
        services.AddBedrockTextEmbeddingGenerationService(modelId, bedrockRuntime);
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var textEmbeddingService = serviceProvider.GetService<ITextEmbeddingGenerationService>();
        Assert.NotNull(textEmbeddingService);
        Assert.IsType<BedrockTextEmbeddingGenerationService>(textEmbeddingService);
    }

    [Fact]
    public void AwsServiceClientBeforeServiceRequestDoesNothingForNonWebServiceRequestEventArgs()
    {
        // Arrange
        var requestEventArgs = new Mock<RequestEventArgs>();

        // Act
        BedrockClientUtilities.BedrockServiceClientRequestHandler(null!, requestEventArgs.Object);

        // Assert
        // No exceptions should be thrown
    }

    [Fact]
    public async Task ChatClientUsesOpenTelemetrySourceNameAsync()
    {
        // Arrange
        string customSourceName = "CustomSourceName";
        bool correctSourceNameUsed = false;
        bool configCallbackInvoked = false;
        var services = new ServiceCollection();
        var modelId = "amazon.titan-text-v2:0";

        // Arrange
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(this.CreateConverseResponse("Hello, world!", ConversationRole.Assistant));
        var bedrockRuntime = mockBedrockApi.Object;

        // Set up an ActivityListener to capture the activity events
        using var activityListener = new ActivityListener
        {
            ShouldListenTo = activitySource => activitySource.Name == customSourceName,
            Sample = (ref ActivityCreationOptions<ActivityContext> _) => ActivitySamplingResult.AllData,
            ActivityStarted = activity => correctSourceNameUsed = true
        };

        ActivitySource.AddActivityListener(activityListener);

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(this._mockLoggerFactory.Object);
        builder.AddBedrockChatClient(
            modelId: modelId,
            bedrockRuntime: bedrockRuntime,
            openTelemetrySourceName: customSourceName,
            openTelemetryConfig: _ => configCallbackInvoked = true);
        var kernel = builder.Build();

        var sut = kernel.GetRequiredService<IChatClient>();

        // Act
        var result = await sut.GetResponseAsync([]);

        // Assert
        Assert.True(correctSourceNameUsed, "The custom OpenTelemetry source name should have been used");
        Assert.True(configCallbackInvoked, "The OpenTelemetry config callback should have been invoked");
    }

    [Fact]
    public async Task EmbeddingGeneratorUsesOpenTelemetrySourceNameAsync()
    {
        // Arrange
        string customSourceName = "CustomSourceName";
        bool correctSourceNameUsed = false;
        bool configCallbackInvoked = false;
        var services = new ServiceCollection();
        var modelId = "amazon.titan-embed-text-v2:0";

        // Arrange
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(this.CreateEmbeddingInvokeResponse([0.1f, 0.2f, 0.3f]));
        var bedrockRuntime = mockBedrockApi.Object;

        // Set up an ActivityListener to capture the activity events
        using var activityListener = new ActivityListener
        {
            ShouldListenTo = activitySource => activitySource.Name == customSourceName,
            Sample = (ref ActivityCreationOptions<ActivityContext> _) => ActivitySamplingResult.AllData,
            ActivityStarted = activity => correctSourceNameUsed = true
        };

        ActivitySource.AddActivityListener(activityListener);

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(this._mockLoggerFactory.Object);
        builder.AddBedrockEmbeddingGenerator(
            modelId: modelId,
            bedrockRuntime: bedrockRuntime,
            openTelemetrySourceName: customSourceName,
            openTelemetryConfig: _ => configCallbackInvoked = true);
        var kernel = builder.Build();

        var sut = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Act
        var result = await sut.GenerateAsync(["test"]);

        // Assert
        Assert.True(correctSourceNameUsed, "The custom OpenTelemetry source name should have been used");
        Assert.True(configCallbackInvoked, "The OpenTelemetry config callback should have been invoked");
    }

    public void Dispose()
    {
        // Disable OpenTelemetry diagnostics after tests
        AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnostics", false);
    }

    private ConverseResponse CreateConverseResponse(string text, ConversationRole role)
    {
        return new ConverseResponse
        {
            Output = new ConverseOutput
            {
                Message = new Message
                {
                    Role = role,
                    Content = new List<ContentBlock> { new() { Text = text } }
                }
            },
            Metrics = new ConverseMetrics(),
            StopReason = StopReason.Max_tokens,
            Usage = new TokenUsage()
        };
    }

    private InvokeModelResponse CreateEmbeddingInvokeResponse(float[] embedding)
    {
        var memoryStream = new MemoryStream(System.Text.Json.JsonSerializer.SerializeToUtf8Bytes(new EmbeddingResponse()
        {
            Embedding = embedding,
            InputTextTokenCount = embedding.Length
        }));

        return new InvokeModelResponse
        {
            Body = memoryStream
        };
    }

    private sealed class EmbeddingResponse
    {
        [JsonPropertyName("embedding")]
        public float[]? Embedding { get; set; }

        [JsonPropertyName("inputTextTokenCount")]
        public int? InputTextTokenCount { get; set; }
    }
}
