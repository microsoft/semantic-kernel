// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Endpoints;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Amazon.UnitTests;

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
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();

        // Assert
        Assert.Equal(modelId, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    /// <summary>
    /// Checks that an invalid model ID cannot create a new service.
    /// </summary>
    [Fact]
    public void ShouldThrowExceptionForInvalidModelId()
    {
        // Arrange
        string invalidModelId = "invalid_model_id";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();

        // Act
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(invalidModelId, mockBedrockApi.Object).Build();

        // Assert
        Assert.Throws<KernelException>(() =>
            kernel.GetRequiredService<ITextGenerationService>());
    }

    /// <summary>
    /// Checks that an empty model ID cannot create a new service.
    /// </summary>
    [Fact]
    public void ShouldThrowExceptionForEmptyModelId()
    {
        // Arrange
        string emptyModelId = string.Empty;
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();

        // Act
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(emptyModelId, mockBedrockApi.Object).Build();

        // Assert
        Assert.Throws<KernelException>(() =>
            kernel.GetRequiredService<ITextGenerationService>());
    }

    /// <summary>
    /// Checks that an invalid BedrockRuntime object will throw an exception.
    /// </summary>
    [Fact]
    public async Task ShouldThrowExceptionForNullBedrockRuntimeAsync()
    {
        // Arrange
        string modelId = "mistral.mistral-text-lite-v1";
        IAmazonBedrockRuntime? nullBedrockRuntime = null;

        // Act & Assert
        await Assert.ThrowsAnyAsync<Exception>(async () =>
        {
            var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, nullBedrockRuntime).Build();
            var service = kernel.GetRequiredService<ITextGenerationService>();
            await service.GetTextContentsAsync("hi").ConfigureAwait(true);
        }).ConfigureAwait(true);
    }

    /// <summary>
    /// Checks that a null prompt will throw an exception.
    /// </summary>
    [Fact]
    public async Task ShouldThrowExceptionForNullPromptAsync()
    {
        // Arrange
        string modelId = "mistral.mistral-text-lite-v1";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        string? nullPrompt = null;

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentNullException>(() =>
            service.GetTextContentsAsync(nullPrompt!)).ConfigureAwait(true);
    }

    /// <summary>
    /// Checks that an empty prompt will throw an exception.
    /// </summary>
    [Fact]
    public async Task ShouldThrowForEmptyPromptAsync()
    {
        // Arrange
        string modelId = "mistral.mistral-text-lite-v1";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        string emptyPrompt = string.Empty;

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(() =>
            service.GetTextContentsAsync(emptyPrompt)).ConfigureAwait(true);
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
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new TitanTextResponse
                {
                    InputTextTokenCount = 5,
                    Results = new List<TitanTextResponse.Result>
                    {
                        new() {
                            TokenCount = 10,
                            OutputText = "This is a mock output.",
                            CompletionReason = "stop"
                        }
                    }
                }))),
                ContentType = "application/json"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        var prompt = "Write a greeting.";

        // Act
        var result = await service.GetTextContentsAsync(prompt).ConfigureAwait(true);

        // Assert
        Assert.Single(result);
        Assert.Equal("This is a mock output.", result[0].Text);
        Assert.NotNull(result[0].InnerContent);
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
        var content = this.GetTextResponseAsBytes("invoke_stream_binary_response.bin");

        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelWithResponseStreamRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
#pragma warning disable CA2000 // Dispose objects before losing scope
        mockBedrockApi.Setup(m => m.InvokeModelWithResponseStreamAsync(It.IsAny<InvokeModelWithResponseStreamRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new InvokeModelWithResponseStreamResponse()
            {
                Body = new ResponseStream(new MemoryStream(content)),
                ContentType = "application/json"
            });
#pragma warning restore CA2000 // Dispose objects before losing scope
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();

        // Act
        List<StreamingTextContent> result = new();
        var output = service.GetStreamingTextContentsAsync(prompt).ConfigureAwait(true);

        // Assert
        int iterations = 0;
        await foreach (var item in output)
        {
            iterations += 1;
            Assert.NotNull(item);
            Assert.NotNull(item.Text);
            Assert.NotNull(item.InnerContent);
            result.Add(item);
        }
        Assert.True(iterations > 0);
        Assert.Equal(iterations, result.Count);
        Assert.NotNull(result);
        Assert.NotNull(service.GetModelId());
    }

    /// <summary>
    /// Checks that an invalid InvokeModelResponse will throw an exception.
    /// </summary>
    [Fact]
    public async Task ShouldHandleInvalidInvokeModelResponseAsync()
    {
        // Arrange
        string modelId = "amazon.titan-text-premier-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = null, // Invalid response, missing body
                ContentType = "application/json"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(() =>
            service.GetTextContentsAsync("sample prompt")).ConfigureAwait(true);
    }

    /// <summary>
    /// Checks that an invalid JSON response format will throw an exception.
    /// </summary>
    [Fact]
    public async Task ShouldHandleInvalidResponseFormatAsync()
    {
        // Arrange
        string modelId = "amazon.titan-text-premier-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream("invalid_json"u8.ToArray()), // Invalid response format
                ContentType = "application/json"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();

        // Act & Assert
        await Assert.ThrowsAsync<JsonException>(() =>
            service.GetTextContentsAsync("sample prompt")).ConfigureAwait(true);
    }

    /// <summary>
    /// Checks that an invalid prompt execution settings will throw an exception.
    /// </summary>
    [Fact]
    public async Task ShouldThrowExceptionForInvalidPromptExecutionSettingsAsync()
    {
        // Arrange
        string modelId = "amazon.titan-text-premier-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        var invalidSettings = new AmazonTitanExecutionSettings()
        {
            Temperature = -1.0f,
            TopP = -0.5f,
            MaxTokenCount = -100
        };

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(() =>
            service.GetTextContentsAsync("sample prompt", invalidSettings)).ConfigureAwait(true);
    }

    private byte[] GetTextResponseAsBytes(string fileName)
    {
        return File.ReadAllBytes($"TestData/{fileName}");
    }
}
