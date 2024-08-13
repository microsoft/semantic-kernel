// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Amazon.Runtime;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Amazon.UnitTests;

/// <summary>
/// Kernel Builder Extension Tests for Bedrock.
/// </summary>
public class BedrockKernelBuilderExtensionTests
{
    /// <summary>
    /// Checks that AddBedrockTextGenerationService builds a proper kernel with a null bedrockRuntime.
    /// </summary>
    [Fact]
    public void AddBedrockTextGenerationCreatesServiceWithNonNullBedrockRuntime()
    {
        // Arrange
        var bedrockRuntime = new Mock<IAmazonBedrockRuntime>().Object;
        var builder = Kernel.CreateBuilder();
        builder.AddBedrockTextGenerationService("amazon.titan-text-premier-v1:0", bedrockRuntime);

        // Act
        var kernel = builder.Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();

        // Assert
        Assert.NotNull(kernel);
        Assert.NotNull(service);
        Assert.IsType<BedrockTextGenerationService>(service);
    }

    /// <summary>
    /// Checks that AddBedrockChatCompletionService builds a proper kernel with a non-null bedrockRuntime.
    /// </summary>
    [Fact]
    public void AddBedrockChatCompletionCreatesServiceWithNonNullBedrockRuntime()
    {
        // Arrange
        var bedrockRuntime = new Mock<IAmazonBedrockRuntime>().Object;
        var builder = Kernel.CreateBuilder();
        builder.AddBedrockChatCompletionService("amazon.titan-text-premier-v1:0", bedrockRuntime);

        // Act
        var kernel = builder.Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Assert
        Assert.NotNull(kernel);
        Assert.NotNull(service);
        Assert.IsType<BedrockChatCompletionService>(service);
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
        BedrockKernelBuilderExtensions.AWSServiceClient_BeforeServiceRequest(null!, requestEventArgs.Object);

        // Assert
        // No exceptions should be thrown
    }
}
