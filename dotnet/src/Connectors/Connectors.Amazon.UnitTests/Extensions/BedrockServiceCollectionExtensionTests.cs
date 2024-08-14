// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Amazon.Runtime;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.ChatCompletion;
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
    /// Ensures that AddBedrockChatCompletionService registers the IChatCompletionService with the correct implementation.
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
    /// Ensures that AddBedrockTextGenerationService registers the ITextGenerationService with the correct implementation.
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
    /// Makes sure AWSServiceClient created BeforeServiceRequest DoesNothingForNonWebServiceRequestEventArgs
    /// </summary>
    [Fact]
    public void AwsServiceClientBeforeServiceRequestDoesNothingForNonWebServiceRequestEventArgs()
    {
        // Arrange
        var requestEventArgs = new Mock<RequestEventArgs>();

        // Act
        BedrockServiceCollectionExtensions.AWSServiceClient_BeforeServiceRequest(null!, requestEventArgs.Object);

        // Assert
        // No exceptions should be thrown
    }
}
