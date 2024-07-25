// Copyright (c) Microsoft. All rights reserved.
using System.Text;
using System.Text.Json;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Extensions;
using Connectors.Amazon.Models.AI21;
using Connectors.Amazon.Models.Amazon;
using Connectors.Amazon.Models.Anthropic;
using Connectors.Amazon.Models.Cohere;
using Connectors.Amazon.Models.Meta;
using Connectors.Amazon.Models.Mistral;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;
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
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();

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

        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.InvokeModelWithResponseStreamAsync(It.IsAny<InvokeModelWithResponseStreamRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new InvokeModelWithResponseStreamResponse()
            {
                Body = new ResponseStream(new MemoryStream()),
                ContentType = "application/json"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();

        // Act
        List<StreamingTextContent> result = new();
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
    /// Checks that the prompt execution settings are correctly registered for the text generation call with Amazon Titan.
    /// </summary>
    [Fact]
    public async Task TitanGetTextContentsAsyncShouldReturnTextContentsAsyncWithPromptExecutionSettingsAsync()
    {
        // Arrange
        string modelId = "amazon.titan-text-lite-v1";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new PromptExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.1f },
                { "topP", 0.95f },
                { "maxTokenCount", 256 },
                { "stopSequences", new List<string> { "</end>" } }
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
        var result = await service.GetTextContentsAsync(prompt, executionSettings).ConfigureAwait(true);

        // Assert
        InvokeModelRequest invokeModelRequest = new();
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
            Assert.Equal(executionSettings.ExtensionData["temperature"], (float)temperatureProperty.GetDouble());
        }

        if (textGenerationConfig.TryGetProperty("topP", out var topPProperty))
        {
            Assert.Equal(executionSettings.ExtensionData["topP"], (float)topPProperty.GetDouble());
        }

        if (textGenerationConfig.TryGetProperty("maxTokenCount", out var maxTokenCountProperty))
        {
            Assert.Equal(executionSettings.ExtensionData["maxTokenCount"], maxTokenCountProperty.GetInt32());
        }

        if (textGenerationConfig.TryGetProperty("stopSequences", out var stopSequencesProperty))
        {
            var stopSequences = stopSequencesProperty.EnumerateArray().Select(e => e.GetString()).ToList();
            Assert.Equal(executionSettings.ExtensionData["stopSequences"], stopSequences);
        }
    }

    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the text generation call with AI21 Labs Jamba.
    /// </summary>
    [Fact]
    public async Task AI21JambaGetTextContentsAsyncShouldReturnTextContentsAsyncWithPromptExecutionSettingsAsync()
    {
        // Arrange
        string modelId = "ai21.jamba-instruct-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new PromptExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.8 },
                { "top_p", 0.95 },
                { "max_tokens", 256 },
                { "stop", new List<string> { "</end>" } }
            }
        };
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new AI21JambaResponse.AI21TextResponse
                {
                    Id = "my-request-id",
                    Choices = new List<AI21JambaResponse.AI21TextResponse.Choice>
                    {
                        new() {
                            Index = 0,
                            Message = new AI21JambaResponse.AI21TextResponse.Message
                            {
                                Role = "assistant",
                                Content = "Hello! This is a mock AI21 response."
                            },
                            FinishReason = "stop"
                        }
                    },
                    Use = new AI21JambaResponse.AI21TextResponse.Usage
                    {
                        PromptTokens = 10,
                        CompletionTokens = 15,
                        TotalTokens = 25
                    }
                }))),
                ContentType = "application/json"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        var prompt = "Write a greeting.";

        // Act
        var result = await service.GetTextContentsAsync(prompt, executionSettings).ConfigureAwait(true);

        // Assert
        InvokeModelRequest invokeModelRequest = new();
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "InvokeModelAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is InvokeModelRequest);
        if (invocation != null)
        {
            invokeModelRequest = (InvokeModelRequest)invocation.Arguments[0];
        }
        Assert.Single(result);
        Assert.Equal("Hello! This is a mock AI21 response.", result[0].Text);
        Assert.NotNull(invokeModelRequest);

        using var requestBodyStream = invokeModelRequest.Body;
        var requestBodyJson = await JsonDocument.ParseAsync(requestBodyStream).ConfigureAwait(true);
        var requestBodyRoot = requestBodyJson.RootElement;
        Assert.True(requestBodyRoot.TryGetProperty("temperature", out var temperatureProperty));
        Assert.Equal(executionSettings.ExtensionData["temperature"], temperatureProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("top_p", out var topPProperty));
        Assert.Equal(executionSettings.ExtensionData["top_p"], topPProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("max_tokens", out var maxTokensProperty));
        Assert.Equal(executionSettings.ExtensionData["max_tokens"], maxTokensProperty.GetInt32());

        Assert.True(requestBodyRoot.TryGetProperty("stop", out var stopProperty));
        var stopSequences = stopProperty.EnumerateArray().Select(e => e.GetString()).ToList();
        Assert.Equal(executionSettings.ExtensionData["stop"], stopSequences);
    }

    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the text generation call with Anthropic Claude.
    /// </summary>
    [Fact]
    public async Task ClaudeGetTextContentsAsyncShouldReturnTextContentsAsyncWithPromptExecutionSettingsAsync()
    {
        // Arrange
        string modelId = "anthropic.claude-text-generation.model-id-only-needs-proper-prefix";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new PromptExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.8 },
                { "top_p", 0.95 },
                { "max_tokens_to_sample", 256 },
                { "stop_sequences", new List<string> { "</end>" } }
            }
        };
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new ClaudeResponse
                {
                    Completion = "Hello! This is a mock Claude response.",
                    StopReason = "stop_sequence",
                    Stop = "</end>"
                }))),
                ContentType = "application/json"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        var prompt = "Write a greeting.\n\nHuman: \n\nAssistant:";

        // Act
        var result = await service.GetTextContentsAsync(prompt, executionSettings).ConfigureAwait(true);

        // Assert
        InvokeModelRequest invokeModelRequest = new();
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "InvokeModelAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is InvokeModelRequest);
        if (invocation != null)
        {
            invokeModelRequest = (InvokeModelRequest)invocation.Arguments[0];
        }
        Assert.Single(result);
        Assert.Equal("Hello! This is a mock Claude response.", result[0].Text);
        Assert.NotNull(invokeModelRequest);

        using var requestBodyStream = invokeModelRequest.Body;
        var requestBodyJson = await JsonDocument.ParseAsync(requestBodyStream).ConfigureAwait(true);
        var requestBodyRoot = requestBodyJson.RootElement;
        Assert.True(requestBodyRoot.TryGetProperty("temperature", out var temperatureProperty));
        Assert.Equal(executionSettings.ExtensionData["temperature"], temperatureProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("top_p", out var topPProperty));
        Assert.Equal(executionSettings.ExtensionData["top_p"], topPProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("max_tokens_to_sample", out var maxTokensToSampleProperty));
        Assert.Equal(executionSettings.ExtensionData["max_tokens_to_sample"], maxTokensToSampleProperty.GetInt32());

        Assert.True(requestBodyRoot.TryGetProperty("stop_sequences", out var stopSequencesProperty));
        var stopSequences = stopSequencesProperty.EnumerateArray().Select(e => e.GetString()).ToList();
        Assert.Equal(executionSettings.ExtensionData["stop_sequences"], stopSequences);
    }

    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the text generation call with Cohere Command.
    /// </summary>
    [Fact]
    public async Task CohereCommandGetTextContentsAsyncShouldReturnReturnTextContentsAsyncWithPromptExecutionSettingsAsync()
    {
        // Arrange
        string modelId = "cohere.command-text-generation";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new PromptExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.8 },
                { "p", 0.95 },
                { "max_tokens", 256 },
                { "stop_sequences", new List<string> { "</end>" } }
            }
        };
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new CommandTextResponse
                {
                    Id = "my-request-id",
                    Prompt = "Write a greeting.",
                    Generations = new List<CommandTextResponse.Generation>
                    {
                        new() {
                            Id = "generation-id",
                            Text = "Hello! This is a mock Cohere Command response.",
                            FinishReason = "COMPLETE",
                            IsFinished = true
                        }
                    }
                }))),
                ContentType = "application/json"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        var prompt = "Write a greeting.";

        // Act
        var result = await service.GetTextContentsAsync(prompt, executionSettings).ConfigureAwait(true);

        // Assert
        InvokeModelRequest invokeModelRequest = new();
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "InvokeModelAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is InvokeModelRequest);
        if (invocation != null)
        {
            invokeModelRequest = (InvokeModelRequest)invocation.Arguments[0];
        }
        Assert.Single(result);
        Assert.Equal("Hello! This is a mock Cohere Command response.", result[0].Text);
        Assert.NotNull(invokeModelRequest);

        using var requestBodyStream = invokeModelRequest.Body;
        var requestBodyJson = await JsonDocument.ParseAsync(requestBodyStream).ConfigureAwait(true);
        var requestBodyRoot = requestBodyJson.RootElement;
        Assert.True(requestBodyRoot.TryGetProperty("temperature", out var temperatureProperty));
        Assert.Equal(executionSettings.ExtensionData["temperature"], temperatureProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("p", out var topPProperty));
        Assert.Equal(executionSettings.ExtensionData["p"], topPProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("max_tokens", out var maxTokensProperty));
        Assert.Equal(executionSettings.ExtensionData["max_tokens"], maxTokensProperty.GetInt32());

        Assert.True(requestBodyRoot.TryGetProperty("stop_sequences", out var stopSequencesProperty));
        var stopSequences = stopSequencesProperty.EnumerateArray().Select(e => e.GetString()).ToList();
        Assert.Equal(executionSettings.ExtensionData["stop_sequences"], stopSequences);
    }
    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the text generation call with Meta Llama3.
    /// </summary>
    [Fact]
    public async Task LlamaGetTextContentsAsyncShouldReturnTextContentsAsyncWithPromptExecutionSettingsAsync()
    {
        // Arrange
        string modelId = "meta.llama3-text-generation";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new PromptExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.8 },
                { "top_p", 0.95 },
                { "max_gen_len", 256 }
            }
        };
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new LlamaTextResponse
                {
                    Generation = "Hello! This is a mock Llama response.",
                    PromptTokenCount = 10,
                    GenerationTokenCount = 15,
                    StopReason = "stop"
                }))),
                ContentType = "application/json"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        var prompt = "Write a greeting.";

        // Act
        var result = await service.GetTextContentsAsync(prompt, executionSettings).ConfigureAwait(true);

        // Assert
        InvokeModelRequest invokeModelRequest = new();
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "InvokeModelAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is InvokeModelRequest);
        if (invocation != null)
        {
            invokeModelRequest = (InvokeModelRequest)invocation.Arguments[0];
        }
        Assert.Single(result);
        Assert.Equal("Hello! This is a mock Llama response.", result[0].Text);
        Assert.NotNull(invokeModelRequest);

        using var requestBodyStream = invokeModelRequest.Body;
        var requestBodyJson = await JsonDocument.ParseAsync(requestBodyStream).ConfigureAwait(true);
        var requestBodyRoot = requestBodyJson.RootElement;
        Assert.True(requestBodyRoot.TryGetProperty("temperature", out var temperatureProperty));
        Assert.Equal(executionSettings.ExtensionData["temperature"], temperatureProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("top_p", out var topPProperty));
        Assert.Equal(executionSettings.ExtensionData["top_p"], topPProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("max_gen_len", out var maxGenLenProperty));
        Assert.Equal(executionSettings.ExtensionData["max_gen_len"], maxGenLenProperty.GetInt32());
    }
    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the text generation call with Mistral.
    /// </summary>
    [Fact]
    public async Task MistralGetTextContentsAsyncShouldReturnTextContentsAsyncWithPromptExecutionSettingsAsync()
    {
        // Arrange
        string modelId = "mistral.mistral-text-generation";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new PromptExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.8 },
                { "top_p", 0.95 },
                { "max_tokens", 256 },
                { "stop", new List<string> { "</end>" } }
            }
        };
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new MistralRequest.MistralTextResponse
                {
                    Outputs = new List<MistralRequest.MistralTextResponse.Output>
                    {
                        new() {
                            Text = "Hello! This is a mock Mistral response.",
                            StopReason = "stop_sequence"
                        }
                    }
                }))),
                ContentType = "application/json"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        var prompt = "Write a greeting.";

        // Act
        var result = await service.GetTextContentsAsync(prompt, executionSettings).ConfigureAwait(true);

        // Assert
        InvokeModelRequest invokeModelRequest = new();
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "InvokeModelAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is InvokeModelRequest);
        if (invocation != null)
        {
            invokeModelRequest = (InvokeModelRequest)invocation.Arguments[0];
        }
        Assert.Single(result);
        Assert.Equal("Hello! This is a mock Mistral response.", result[0].Text);
        Assert.NotNull(invokeModelRequest);

        using var requestBodyStream = invokeModelRequest.Body;
        var requestBodyJson = await JsonDocument.ParseAsync(requestBodyStream).ConfigureAwait(true);
        var requestBodyRoot = requestBodyJson.RootElement;
        Assert.True(requestBodyRoot.TryGetProperty("temperature", out var temperatureProperty));
        Assert.Equal(executionSettings.ExtensionData["temperature"], temperatureProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("top_p", out var topPProperty));
        Assert.Equal(executionSettings.ExtensionData["top_p"], topPProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("max_tokens", out var maxTokensProperty));
        Assert.Equal(executionSettings.ExtensionData["max_tokens"], maxTokensProperty.GetInt32());

        Assert.True(requestBodyRoot.TryGetProperty("stop", out var stopSequencesProperty));
        var stopSequences = stopSequencesProperty.EnumerateArray().Select(e => e.GetString()).ToList();
        Assert.Equal(executionSettings.ExtensionData["stop"], stopSequences);
    }
}
