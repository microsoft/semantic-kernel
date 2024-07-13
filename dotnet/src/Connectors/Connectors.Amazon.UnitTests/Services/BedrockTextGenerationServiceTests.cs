// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.EventStreams.Internal;
using Connectors.Amazon.Models.Amazon;
using Connectors.Amazon.Services;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.Connectors.Amazon.Services;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using Xunit;
namespace Connectors.Amazon.UnitTests.Services;

public class BedrockTextGenerationServiceTests
{
    [Fact]
    public void AttributesShouldContainModelId()
    {
        // Arrange
        string modelId = "amazon.titan-text-premier-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var service = new BedrockTextGenerationService(modelId, mockBedrockApi.Object);

        // Act & Assert
        Assert.Equal(modelId, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public async Task GetTextContentsAsyncShouldReturnTextContents()
    {
        // Arrange
        string modelId = "amazon.titan-text-premier-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new TitanTextResponse
                {
                    InputTextTokenCount = 5,
                    Results = new List<TitanTextResponse.Result>
                    {
                        new TitanTextResponse.Result
                        {
                            TokenCount = 10,
                            OutputText = "Hello, world!",
                            CompletionReason = "stop"
                        }
                    }
                }))),
                ContentType = "application/json"
            });
        var service = new BedrockTextGenerationService(modelId, mockBedrockApi.Object);
        var prompt = "Write a greeting.";

        // Act
        var result = await service.GetTextContentsAsync(prompt).ConfigureAwait(true);

        // Assert
        Assert.Single(result);
        Assert.Equal("Hello, world!", result[0].Text);
    }

    [Fact]
    public async Task GetStreamingTextContentsAsyncShouldReturnStreamedTextContents()
    {
        // Arrange
        string modelId = "amazon.titan-text-premier-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var responseData = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new TitanTextResponse
        {
            InputTextTokenCount = 5,
            Results = new List<TitanTextResponse.Result>
            {
                new TitanTextResponse.Result
                {
                    TokenCount = 10,
                    OutputText = "Hello, world!",
                    CompletionReason = "stop"
                }
            }
        }));
        mockBedrockApi.Setup(m => m.InvokeModelWithResponseStreamAsync(It.IsAny<InvokeModelWithResponseStreamRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new InvokeModelWithResponseStreamResponse()
            {
                Body = new ResponseStream(new MemoryStream(responseData)),
                // Body = new ResponseStream(new MemoryStream(Encoding.UTF8.GetBytes("[{\"chunk\":{\"bytes\":\"eyJjb250ZW50IjoiSGVsbG8sIn0=\"}},{\"chunk\":{\"bytes\":\"eyJjb250ZW50IjoiIHdvcmxkISJ9fQ==\"}}]"))),
                ContentType = "application/json"
            });
        var service = new BedrockTextGenerationService(modelId, mockBedrockApi.Object);
        var prompt = "Write a greeting.";

        // Act
        var streamingContents = new List<StreamingTextContent>();
        var asyncEnumerator = service.GetStreamingTextContentsAsync(prompt).ConfigureAwait(true).GetAsyncEnumerator();
        try
        {
            while (await asyncEnumerator.MoveNextAsync())
            {
                streamingContents.Add(asyncEnumerator.Current);
            }
        }
        finally
        {
            await asyncEnumerator.DisposeAsync();
        }

        // Assert
        Assert.Equal(2, streamingContents.Count);
        Assert.Equal("Hello, ", streamingContents[0].Text);
        Assert.Equal(" world!", streamingContents[1].Text);
    }
}
