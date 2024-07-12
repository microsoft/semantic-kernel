// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Models.Mistral;
using Connectors.Amazon.Services;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.Connectors.Amazon.Services;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;
namespace Connectors.Amazon.UnitTests.Services;

public class BedrockChatCompletionServiceTests
{
    [Fact]
    public void AttributesShouldContainModelId()
    {
        // Arrange
        string modelId = "amazon.titan-embed-text-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var service = new BedrockChatCompletionService(modelId, mockBedrockApi.Object);

        // Act & Assert
        Assert.Equal(modelId, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public async Task GetChatMessageContentsAsync_ShouldReturnChatMessageContents()
    {
        // Arrange
        string modelId = "amazon.titan-embed-text-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new ConverseResponse
            {
                Output = new ConverseOutput
                {
                    Message = new Message
                    {
                        Role = ConversationRole.Assistant,
                        Content = new List<ContentBlock> { new ContentBlock { Text = "Hello, world!" } }
                    }
                },
                Metrics = new ConverseMetrics(), // Required property
                StopReason = StopReason.Max_tokens, // Required property
                Usage = new TokenUsage() // Required property
            });
        var service = new BedrockChatCompletionService(modelId, mockBedrockApi.Object);
        var chatHistory = new ChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);

        // Assert
        Assert.Single(result);
        Assert.Equal(AuthorRole.Assistant, result[0].Role);
        Assert.Single(result[0].Items);
        Assert.Equal("Hello, world!", result[0].Items[0].ToString());
    }
}
