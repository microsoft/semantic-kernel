// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Amazon.Runtime;
using Microsoft.Extensions.DependencyInjection;
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
public class BedrockServiceCollectionExtensionTests
{
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
}
