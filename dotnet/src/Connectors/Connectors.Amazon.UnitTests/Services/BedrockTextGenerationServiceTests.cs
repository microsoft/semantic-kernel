// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
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
        string prompt = "Write a greeting.";
        List<PayloadPart> payloadParts = new List<PayloadPart>
        {
            new PayloadPart { Bytes = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(new JsonObject { { "outputText", "Hello" } })) },
            new PayloadPart { Bytes = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(new JsonObject { { "outputText", ", world!" } })) }
        };
        byte[] byteArray = payloadParts.SelectMany(p => p.Bytes.ToArray()).ToArray();
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.InvokeModelWithResponseStreamAsync(It.IsAny<InvokeModelWithResponseStreamRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new InvokeModelWithResponseStreamResponse
            {
                Body = new ResponseStream(new MemoryStream(byteArray)),
                ContentType = "application/json"
            });

        // var mockIoService = new Mock<AmazonIOService>();
        // mockIoService.Setup(m => m.GetInvokeModelRequestBody(prompt, null))
        //     .Returns(new { inputText = prompt, textGenerationConfig = new { temperature = 0.7, topP = 0.9, maxTokenCount = 512, stopSequences = new List<string>() } });
        // mockIoService.Setup(m => m.GetTextStreamOutput(It.IsAny<JsonNode>()))
        //     .Returns<JsonNode>(chunk => chunk?["outputText"]?.ToString() == null ? Enumerable.Empty<string>() : new[] { chunk["outputText"].ToString() });

        var service = new BedrockTextGenerationService(modelId);

        // Act
        List<StreamingTextContent> result = new List<StreamingTextContent>();
        var output = service.GetStreamingTextContentsAsync(prompt).ConfigureAwait(true);
        await foreach (var item in output)
        {
            result.Add(item);
        }

        // Assert
        Assert.Equal(2, result.Count);
        Assert.Equal("Hello, ", result[0].Text);
        Assert.Equal(" world!", result[1].Text);
    }
}
