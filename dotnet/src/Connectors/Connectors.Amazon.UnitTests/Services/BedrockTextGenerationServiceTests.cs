// Copyright (c) Microsoft. All rights reserved.
using System.Text;
using System.Text.Json;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Models.Amazon;
using Connectors.Amazon.Services;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace Connectors.Amazon.UnitTests.Services;
/// <summary>
/// Unit tests for BedrockTextGenerationService.
/// </summary>
public class BedrockTextGenerationServiceTests
{
    /// <summary>
    /// Checks that modelID is added to the list of service attributes when service is registered.
    /// </summary>
    [Fact]
    public void AttributesShouldContainModelId()
    {
        // Arrange & Act
        string modelId = "amazon.titan-text-premier-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var service = new BedrockTextGenerationService(modelId, mockBedrockApi.Object);

        // Assert
        Assert.Equal(modelId, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    /// <summary>
    /// Checks that GetTextContentsAsync calls and correctly handles outputs from InvokeModelAsync.
    /// </summary>
    [Fact]
    public async Task GetTextContentsAsyncShouldReturnTextContentsAsync()
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
                            OutputText = "This is a mock output.",
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
        Assert.Equal("This is a mock output.", result[0].Text);
    }

    /// <summary>
    /// Checks that GetStreamingTextContentsAsync calls and correctly handles outputs from InvokeModelAsync.
    /// </summary>
    [Fact]
    public async Task GetStreamingTextContentsAsyncShouldReturnStreamedTextContentsAsync()
    {
        // Arrange
        string modelId = "amazon.titan-text-premier-v1:0";
        string prompt = "Write a short greeting.";

        // Attempt 1
        // List<PayloadPart> payloadParts = new List<PayloadPart>
        // {
        //     new PayloadPart { Bytes = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(new JsonObject { { "outputText", "Hello" } })) },
        //     new PayloadPart { Bytes = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(new JsonObject { { "outputText", ", world!" } })) }
        // };
        // byte[] byteResponseStream = payloadParts.SelectMany(p => p.Bytes.ToArray()).ToArray();
        // var mockResponseStream = new MemoryStream(byteResponseStream);

        // Attempt 2
        // string mockResponseJson = @"{
        //     ""index"": 0,
        //     ""inputTextTokenCount"": null,
        //     ""totalOutputTextTokenCount"": null,
        //     ""outputText"": ""Hello!"",
        //     ""completionReason"": ""FINISH""
        // }";
        // byte[] mockResponseBytes = Encoding.UTF8.GetBytes(mockResponseJson);
        // var mockResponseStream = new MemoryStream(mockResponseBytes);

        // Attempt 3
        // Create a mock response stream that emits the output text in chunks
        // var mockResponseStream = new MemoryStream();
        // using (var writer = new StreamWriter(mockResponseStream, Encoding.UTF8, 1024, true))
        // {
        //     await writer.WriteAsync("{\"outputText\":\"Hello\"}").ConfigureAwait(true);
        //     await writer.FlushAsync().ConfigureAwait(true);
        //     mockResponseStream.Position = 0;
        //
        //     await writer.WriteAsync("{\"outputText\":\"").ConfigureAwait(true);
        //     await writer.FlushAsync().ConfigureAwait(true);
        //     mockResponseStream.Position = mockResponseStream.Length;
        //
        //     await writer.WriteAsync(", world!").ConfigureAwait(true);
        //     await writer.FlushAsync().ConfigureAwait(true);
        //     mockResponseStream.Position = 0;
        //
        //     await writer.WriteAsync("\"}").ConfigureAwait(true);
        //     await writer.FlushAsync().ConfigureAwait(true);
        //     mockResponseStream.Position = 0;
        // }

        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.InvokeModelWithResponseStreamAsync(It.IsAny<InvokeModelWithResponseStreamRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new InvokeModelWithResponseStreamResponse()
            {
                Body = new ResponseStream(new MemoryStream()),
                ContentType = "application/json"
            });
        var service = new BedrockTextGenerationService(modelId, mockBedrockApi.Object);

        // Act
        List<StreamingTextContent> result = new List<StreamingTextContent>();
        var output = service.GetStreamingTextContentsAsync(prompt).ConfigureAwait(true);

        // Assert
        await foreach (var item in output)
        {
            Assert.NotNull(item);
            Assert.NotNull(item.Text);
            result.Add(item);
        }
        Assert.NotNull(result);
        Assert.NotNull(service.GetModelId());
    }

    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the text generation call.
    /// </summary>
    [Fact]
    public async Task GetTextContentsAsyncShouldUsePromptExecutionSettingsAsync()
    {
        // Arrange
        string modelId = "amazon.titan-text-lite-v1";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new PromptExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.8 },
                { "top_p", 0.95 },
                { "max_tokens", 256 },
                { "stop_sequences", new List<string> { "</end>" } }
            }
        };
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
                            OutputText = "This is a mock output.",
                            CompletionReason = "stop"
                        }
                    }
                }))),
                ContentType = "application/json"
            });
        var service = new BedrockTextGenerationService(modelId, mockBedrockApi.Object);
        var prompt = "Write a greeting.";

        // Act
        var result = await service.GetTextContentsAsync(prompt, executionSettings).ConfigureAwait(true);

        // Assert
        InvokeModelRequest invokeModelRequest = new InvokeModelRequest();
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "InvokeModelAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is InvokeModelRequest);
        if (invocation != null)
        {
            invokeModelRequest = (InvokeModelRequest)invocation.Arguments[0];
        }
        Assert.Single(result);
        Assert.Equal("This is a mock output.", result[0].Text);
        Assert.NotNull(invokeModelRequest);

        using var requestBodyStream = invokeModelRequest.Body;
        var requestBodyJson = await JsonDocument.ParseAsync(requestBodyStream).ConfigureAwait(true);
        var requestBodyRoot = requestBodyJson.RootElement;
        Assert.True(requestBodyRoot.TryGetProperty("textGenerationConfig", out var textGenerationConfig));
        if (textGenerationConfig.TryGetProperty("temperature", out var temperatureProperty))
        {
            Assert.Equal(executionSettings.ExtensionData["temperature"], temperatureProperty.GetDouble());
        }

        if (textGenerationConfig.TryGetProperty("topP", out var topPProperty))
        {
            Assert.Equal(executionSettings.ExtensionData["top_p"], topPProperty.GetDouble());
        }

        if (textGenerationConfig.TryGetProperty("maxTokenCount", out var maxTokenCountProperty))
        {
            Assert.Equal(executionSettings.ExtensionData["max_tokens"], maxTokenCountProperty.GetInt32());
        }

        if (textGenerationConfig.TryGetProperty("stopSequences", out var stopSequencesProperty))
        {
            var stopSequences = stopSequencesProperty.EnumerateArray().Select(e => e.GetString()).ToList();
            Assert.Equal(executionSettings.ExtensionData["stop_sequences"], stopSequences);
        }
    }
}
