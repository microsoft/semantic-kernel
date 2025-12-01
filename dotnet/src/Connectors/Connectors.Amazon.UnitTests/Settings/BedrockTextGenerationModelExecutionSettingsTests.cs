// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Endpoints;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Amazon.UnitTests;

/// <summary>
/// Unit tests for prompt execution settings configurations with different Bedrock Models.
/// </summary>
public class BedrockTextGenerationModelExecutionSettingsTests
{
    /// <summary>
    /// Checks that the prompt execution settings extension data overrides the properties when both are set because the property actually should get from the ExtensionData behind the scenes.
    /// </summary>
    [Fact]
    public async Task ExecutionSettingsExtensionDataOverridesPropertiesAsync()
    {
        // Arrange
        MemoryStream? requestedBody = null;
        string modelId = "meta.llama3-text-generation";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonLlama3ExecutionSettings()
        {
            Temperature = -10.0f,
            TopP = -2.0f,
            MaxGenLen = 2,
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.8f },
                { "top_p", 0.95f },
                { "max_gen_len", 256 }
            }
        };
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .Callback<InvokeModelRequest, CancellationToken>((request, cancellationToken) =>
            {
                // Copy the MemoryStream from the request body to avoid (disposal during assertion)
                if (request.Body != null)
                {
                    requestedBody = new MemoryStream();
                    request.Body.CopyTo(requestedBody);
                    requestedBody.Position = 0; // Reset position to the beginning
                    request.Body.Position = 0; // Reset position to the beginning
                }
            })
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new LlamaResponse
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
        InvokeModelRequest? invokeModelRequest = null;
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

        Assert.NotNull(requestedBody);
        using var requestBodyStream = requestedBody;
        var requestBodyJson = await JsonDocument.ParseAsync(requestBodyStream).ConfigureAwait(true);
        var requestBodyRoot = requestBodyJson.RootElement;

        Assert.True(requestBodyRoot.TryGetProperty("temperature", out var temperatureProperty));
        Assert.NotEqual(executionSettings.Temperature, (float)temperatureProperty.GetDouble());
        Assert.Equal(executionSettings.ExtensionData["temperature"], (float)temperatureProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("top_p", out var topPProperty));
        Assert.NotEqual(executionSettings.TopP, (float)topPProperty.GetDouble());
        Assert.Equal(executionSettings.ExtensionData["top_p"], (float)topPProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("max_gen_len", out var maxGenLenProperty));
        Assert.NotEqual(executionSettings.MaxGenLen, maxGenLenProperty.GetInt32());
        Assert.Equal(executionSettings.ExtensionData["max_gen_len"], maxGenLenProperty.GetInt32());
    }

    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the text generation call with Amazon Titan. Inserts execution settings data both ways to test.
    /// </summary>
    [Fact]
    public async Task TitanExecutionSettingsExtensionDataSetsProperlyAsync()
    {
        // Arrange
        MemoryStream? requestedBody = null;
        string modelId = "amazon.titan-text-lite-v1";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonTitanExecutionSettings()
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
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .Callback<InvokeModelRequest, CancellationToken>((request, cancellationToken) =>
            {
                // Copy the MemoryStream from the request body to avoid (disposal during assertion)
                if (request.Body != null)
                {
                    requestedBody = new MemoryStream();
                    request.Body.CopyTo(requestedBody);
                    requestedBody.Position = 0; // Reset position to the beginning
                    request.Body.Position = 0; // Reset position to the beginning
                }
            })
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new TitanTextResponse
                {
                    InputTextTokenCount = 5,
                    Results =
                    [
                        new() {
                            TokenCount = 10,
                            OutputText = "This is a mock output.",
                            CompletionReason = "stop"
                        }
                    ]
                }))),
                ContentType = "application/json"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        var prompt = "Write a greeting.";

        // Act
        var result = await service.GetTextContentsAsync(prompt, executionSettings).ConfigureAwait(true);

        // Assert
        InvokeModelRequest? invokeModelRequest = null;
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

        Assert.NotNull(requestedBody);
        using var requestBodyStream = requestedBody;
        var requestBodyJson = await JsonDocument.ParseAsync(requestBodyStream).ConfigureAwait(true);
        var requestBodyRoot = requestBodyJson.RootElement;
        Assert.True(requestBodyRoot.TryGetProperty("textGenerationConfig", out var textGenerationConfig));

        // Check temperature
        Assert.True(textGenerationConfig.TryGetProperty("temperature", out var temperatureProperty));
        Assert.Equal(executionSettings.ExtensionData.TryGetValue("temperature", out var extensionTemperature) ? extensionTemperature : executionSettings.Temperature, (float)temperatureProperty.GetDouble());

        // Check top_p
        Assert.True(textGenerationConfig.TryGetProperty("topP", out var topPProperty));
        Assert.Equal(executionSettings.ExtensionData.TryGetValue("topP", out var extensionTopP) ? extensionTopP : executionSettings.TopP, (float)topPProperty.GetDouble());

        // Check max_token_count
        Assert.True(textGenerationConfig.TryGetProperty("maxTokenCount", out var maxTokenCountProperty));
        Assert.Equal(executionSettings.ExtensionData.TryGetValue("maxTokenCount", out var extensionMaxTokenCount) ? extensionMaxTokenCount : executionSettings.MaxTokenCount, maxTokenCountProperty.GetInt32());

        // Check stop_sequences
        Assert.True(textGenerationConfig.TryGetProperty("stopSequences", out var stopSequencesProperty));
        var stopSequences = stopSequencesProperty.EnumerateArray().Select(e => e.GetString()).ToList();
        Assert.Equal(executionSettings.ExtensionData.TryGetValue("stopSequences", out var extensionStopSequences) ? extensionStopSequences : executionSettings.StopSequences, stopSequences);
    }

    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the text generation call with Amazon Titan. Inserts execution settings data both ways to test.
    /// </summary>
    [Fact]
    public async Task TitanExecutionSettingsPropertySetsProperlyAsync()
    {
        // Arrange
        MemoryStream? requestedBody = null;
        string modelId = "amazon.titan-text-lite-v1";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonTitanExecutionSettings()
        {
            Temperature = 0.1f,
            TopP = 0.95f,
            MaxTokenCount = 256,
            StopSequences = ["</end>"],
            ModelId = modelId,
        };
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .Callback<InvokeModelRequest, CancellationToken>((request, cancellationToken) =>
            {
                // Copy the MemoryStream from the request body to avoid (disposal during assertion)
                if (request.Body != null)
                {
                    requestedBody = new MemoryStream();
                    request.Body.CopyTo(requestedBody);
                    requestedBody.Position = 0; // Reset position to the beginning
                    request.Body.Position = 0; // Reset position to the beginning
                }
            })
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new TitanTextResponse
                {
                    InputTextTokenCount = 5,
                    Results =
                    [
                        new() {
                            TokenCount = 10,
                            OutputText = "This is a mock output.",
                            CompletionReason = "stop"
                        }
                    ]
                }))),
                ContentType = "application/json"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        var prompt = "Write a greeting.";

        // Act
        var result = await service.GetTextContentsAsync(prompt, executionSettings).ConfigureAwait(true);

        // Assert
        InvokeModelRequest? invokeModelRequest = null;
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

        Assert.NotNull(requestedBody);
        using var requestBodyStream = requestedBody;
        var requestBodyJson = await JsonDocument.ParseAsync(requestBodyStream).ConfigureAwait(true);
        var requestBodyRoot = requestBodyJson.RootElement;
        Assert.True(requestBodyRoot.TryGetProperty("textGenerationConfig", out var textGenerationConfig));

        // Check temperature
        Assert.True(textGenerationConfig.TryGetProperty("temperature", out var temperatureProperty));
        Assert.Equal(executionSettings.Temperature, (float)temperatureProperty.GetDouble());

        // Check top_p
        Assert.True(textGenerationConfig.TryGetProperty("topP", out var topPProperty));
        Assert.Equal(executionSettings.TopP, (float)topPProperty.GetDouble());

        // Check max_token_count
        Assert.True(textGenerationConfig.TryGetProperty("maxTokenCount", out var maxTokenCountProperty));
        Assert.Equal(executionSettings.MaxTokenCount, maxTokenCountProperty.GetInt32());

        // Check stop_sequences
        Assert.True(textGenerationConfig.TryGetProperty("stopSequences", out var stopSequencesProperty));
        var stopSequences = stopSequencesProperty.EnumerateArray().Select(e => e.GetString()).ToList();
        Assert.Equal(executionSettings.StopSequences, stopSequences!);
    }

    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the text generation call with AI21 Labs Jamba. Inserts execution settings data both ways to test.
    /// </summary>
    [Fact]
    public async Task JambaExecutionSettingsExtensionDataSetsProperlyAsync()
    {
        // Arrange
        MemoryStream? requestedBody = null;
        string modelId = "ai21.jamba-instruct-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonJambaExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.8f },
                { "top_p", 0.95f },
                { "max_tokens", 256 },
                { "stop", new List<string> { "</end>" } },
                { "n", 1 },
                { "frequency_penalty", 0.0 },
                { "presence_penalty", 0.0 }
            }
        };
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .Callback<InvokeModelRequest, CancellationToken>((request, cancellationToken) =>
            {
                // Copy the MemoryStream from the request body to avoid (disposal during assertion)
                if (request.Body != null)
                {
                    requestedBody = new MemoryStream();
                    request.Body.CopyTo(requestedBody);
                    requestedBody.Position = 0; // Reset position to the beginning
                    request.Body.Position = 0; // Reset position to the beginning
                }
            })
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new AI21JambaResponse.AI21TextResponse
                {
                    Id = "my-request-id",
                    Choices =
                    [
                        new() {
                            Index = 0,
                            Message = new AI21JambaResponse.Message
                            {
                                Role = "assistant",
                                Content = "Hello! This is a mock AI21 response."
                            },
                            FinishReason = "stop"
                        }
                    ],
                    Usage = new AI21JambaResponse.JambaUsage
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
        InvokeModelRequest? invokeModelRequest = null;
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

        Assert.NotNull(requestedBody);
        using var requestBodyStream = requestedBody;
        var requestBodyJson = await JsonDocument.ParseAsync(requestBodyStream).ConfigureAwait(true);
        var requestBodyRoot = requestBodyJson.RootElement;

        // Check temperature
        Assert.True(requestBodyRoot.TryGetProperty("temperature", out var temperatureProperty));
        Assert.Equal(executionSettings.ExtensionData.TryGetValue("temperature", out var extensionTemperature) ? extensionTemperature : executionSettings.Temperature, (float)temperatureProperty.GetDouble());

        // Check top_p
        Assert.True(requestBodyRoot.TryGetProperty("top_p", out var topPProperty));
        Assert.Equal(executionSettings.ExtensionData.TryGetValue("top_p", out var extensionTopP) ? extensionTopP : executionSettings.TopP, (float)topPProperty.GetDouble());

        // Check max_tokens
        Assert.True(requestBodyRoot.TryGetProperty("max_tokens", out var maxTokensProperty));
        Assert.Equal(executionSettings.ExtensionData.TryGetValue("max_tokens", out var extensionMaxTokens) ? extensionMaxTokens : executionSettings.MaxTokens, maxTokensProperty.GetInt32());

        // Check stop
        Assert.True(requestBodyRoot.TryGetProperty("stop", out var stopProperty));
        var stopSequences = stopProperty.EnumerateArray().Select(e => e.GetString()).ToList();
        Assert.Equal(executionSettings.ExtensionData.TryGetValue("stop", out var extensionStop) ? extensionStop : executionSettings.Stop, stopSequences);

        // Check number_of_responses
        Assert.True(requestBodyRoot.TryGetProperty("n", out var numberResponsesProperty));
        Assert.Equal(executionSettings.ExtensionData.TryGetValue("n", out var extensionNumberResponses) ? extensionNumberResponses : executionSettings.NumberOfResponses, numberResponsesProperty.GetInt32());

        // Check frequency_penalty
        Assert.True(requestBodyRoot.TryGetProperty("frequency_penalty", out var frequencyPenaltyProperty));
        Assert.Equal(executionSettings.ExtensionData.TryGetValue("frequency_penalty", out var extensionFrequencyPenalty) ? extensionFrequencyPenalty : executionSettings.FrequencyPenalty, frequencyPenaltyProperty.GetDouble());

        // Check presence_penalty
        Assert.True(requestBodyRoot.TryGetProperty("presence_penalty", out var presencePenaltyProperty));
        Assert.Equal(executionSettings.ExtensionData.TryGetValue("presence_penalty", out var extensionPresencePenalty) ? extensionPresencePenalty : executionSettings.PresencePenalty, presencePenaltyProperty.GetDouble());
    }

    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the text generation call with AI21 Labs Jamba. Inserts execution settings data both ways to test.
    /// </summary>
    [Fact]
    public async Task JambaExecutionSettingsPropertySetsProperlyAsync()
    {
        // Arrange
        MemoryStream? requestedBody = null;
        string modelId = "ai21.jamba-instruct-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonJambaExecutionSettings()
        {
            Temperature = 0.8f,
            TopP = 0.95f,
            MaxTokens = 256,
            Stop = ["</end>"],
            NumberOfResponses = 1,
            FrequencyPenalty = 0.0,
            PresencePenalty = 0.0,
            ModelId = modelId
        };
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .Callback<InvokeModelRequest, CancellationToken>((request, cancellationToken) =>
            {
                // Copy the MemoryStream from the request body to avoid (disposal during assertion)
                if (request.Body != null)
                {
                    requestedBody = new MemoryStream();
                    request.Body.CopyTo(requestedBody);
                    requestedBody.Position = 0; // Reset position to the beginning
                    request.Body.Position = 0; // Reset position to the beginning
                }
            })
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new AI21JambaResponse.AI21TextResponse
                {
                    Id = "my-request-id",
                    Choices =
                    [
                        new() {
                            Index = 0,
                            Message = new AI21JambaResponse.Message
                            {
                                Role = "assistant",
                                Content = "Hello! This is a mock AI21 response."
                            },
                            FinishReason = "stop"
                        }
                    ],
                    Usage = new AI21JambaResponse.JambaUsage
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
        InvokeModelRequest? invokeModelRequest = null;
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

        Assert.NotNull(requestedBody);
        using var requestBodyStream = requestedBody;
        var requestBodyJson = await JsonDocument.ParseAsync(requestBodyStream).ConfigureAwait(true);
        var requestBodyRoot = requestBodyJson.RootElement;

        // Check temperature
        Assert.True(requestBodyRoot.TryGetProperty("temperature", out var temperatureProperty));
        Assert.Equal(executionSettings.Temperature, (float)temperatureProperty.GetDouble());

        // Check top_p
        Assert.True(requestBodyRoot.TryGetProperty("top_p", out var topPProperty));
        Assert.Equal(executionSettings.TopP, (float)topPProperty.GetDouble());

        // Check max_tokens
        Assert.True(requestBodyRoot.TryGetProperty("max_tokens", out var maxTokensProperty));
        Assert.Equal(executionSettings.MaxTokens, maxTokensProperty.GetInt32());

        // Check stop
        Assert.True(requestBodyRoot.TryGetProperty("stop", out var stopProperty));
        var stopSequences = stopProperty.EnumerateArray().Select(e => e.GetString()).ToList();
        Assert.Equal(executionSettings.Stop, stopSequences!);

        // Check number_of_responses
        Assert.True(requestBodyRoot.TryGetProperty("n", out var numberResponsesProperty));
        Assert.Equal(executionSettings.NumberOfResponses, numberResponsesProperty.GetInt32());

        // Check frequency_penalty
        Assert.True(requestBodyRoot.TryGetProperty("frequency_penalty", out var frequencyPenaltyProperty));
        Assert.Equal(executionSettings.FrequencyPenalty, frequencyPenaltyProperty.GetDouble());

        // Check presence_penalty
        Assert.True(requestBodyRoot.TryGetProperty("presence_penalty", out var presencePenaltyProperty));
        Assert.Equal(executionSettings.PresencePenalty, presencePenaltyProperty.GetDouble());
    }

    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the text generation call with AI21 Labs Jamba. Inserts execution settings data both ways to test.
    /// </summary>
    [Fact]
    public async Task JurassicExecutionSettingsExtensionDataSetsProperlyAsync()
    {
        // Arrange
        MemoryStream? requestedBody = null;
        string modelId = "ai21.j2-ultra-v1";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonJurassicExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.8f },
                { "topP", 0.95f },
                { "maxTokens", 256 },
                { "stopSequences", new List<string> { "</end>" } }
            }
        };
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .Callback<InvokeModelRequest, CancellationToken>((request, cancellationToken) =>
            {
                // Copy the MemoryStream from the request body to avoid (disposal during assertion)
                if (request.Body != null)
                {
                    requestedBody = new MemoryStream();
                    request.Body.CopyTo(requestedBody);
                    requestedBody.Position = 0; // Reset position to the beginning
                    request.Body.Position = 0; // Reset position to the beginning
                }
            })
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new AI21JurassicResponse
                {
                    Id = 10000000000,
                    Completions =
                    [
                        new()
                        {
                            Data = new AI21JurassicResponse.JurassicData
                            {
                                Text = "Hello! This is a mock AI21 response."
                            }
                        }
                    ]
                })))
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        var prompt = "Write a greeting.";

        // Act
        var result = await service.GetTextContentsAsync(prompt, executionSettings).ConfigureAwait(true);

        // Assert
        InvokeModelRequest? invokeModelRequest = null;
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

        Assert.NotNull(requestedBody);
        using var requestBodyStream = requestedBody;
        var requestBodyJson = await JsonDocument.ParseAsync(requestBodyStream).ConfigureAwait(true);
        var requestBodyRoot = requestBodyJson.RootElement;

        // Check temperature
        Assert.True(requestBodyRoot.TryGetProperty("temperature", out var temperatureProperty));
        Assert.Equal(executionSettings.ExtensionData.TryGetValue("temperature", out var extensionTemperature) ? extensionTemperature : executionSettings.Temperature, (float)temperatureProperty.GetDouble());

        // Check top_p
        Assert.True(requestBodyRoot.TryGetProperty("topP", out var topPProperty));
        Assert.Equal(executionSettings.ExtensionData.TryGetValue("topP", out var extensionTopP) ? extensionTopP : executionSettings.TopP, (float)topPProperty.GetDouble());

        // Check max_tokens
        Assert.True(requestBodyRoot.TryGetProperty("maxTokens", out var maxTokensProperty));
        Assert.Equal(executionSettings.ExtensionData.TryGetValue("maxTokens", out var extensionMaxTokens) ? extensionMaxTokens : executionSettings.MaxTokens, maxTokensProperty.GetInt32());

        // Check stop
        Assert.True(requestBodyRoot.TryGetProperty("stopSequences", out var stopProperty));
        var stopSequences = stopProperty.EnumerateArray().Select(e => e.GetString()).ToList();
        Assert.Equal(executionSettings.ExtensionData.TryGetValue("stopSequences", out var extensionStop) ? extensionStop : executionSettings.StopSequences, stopSequences);
    }

    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the text generation call with Anthropic Claude.
    /// </summary>
    [Fact]
    public async Task ClaudeExecutionSettingsSetsExtensionDataAsync()
    {
        // Arrange
        MemoryStream? requestedBody = null;
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
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .Callback<InvokeModelRequest, CancellationToken>((request, cancellationToken) =>
            {
                // Copy the MemoryStream from the request body to avoid (disposal during assertion)
                if (request.Body != null)
                {
                    requestedBody = new MemoryStream();
                    request.Body.CopyTo(requestedBody);
                    requestedBody.Position = 0; // Reset position to the beginning
                    request.Body.Position = 0; // Reset position to the beginning
                }
            })
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

        Assert.NotNull(requestedBody);
        using var requestBodyStream = requestedBody;
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
    public async Task CommandExecutionSettingsSetsExtensionDataAsync()
    {
        // Arrange
        MemoryStream? requestedBody = null;
        string modelId = "cohere.command-text-generation";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonCommandExecutionSettings()
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
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .Callback<InvokeModelRequest, CancellationToken>((request, cancellationToken) =>
            {
                // Copy the MemoryStream from the request body to avoid (disposal during assertion)
                if (request.Body != null)
                {
                    requestedBody = new MemoryStream();
                    request.Body.CopyTo(requestedBody);
                    requestedBody.Position = 0; // Reset position to the beginning
                    request.Body.Position = 0; // Reset position to the beginning
                }
            })
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new CommandResponse
                {
                    Id = "my-request-id",
                    Prompt = "Write a greeting.",
                    Generations =
                    [
                        new() {
                            Id = "generation-id",
                            Text = "Hello! This is a mock Cohere Command response.",
                            FinishReason = "COMPLETE",
                            IsFinished = true
                        }
                    ]
                }))),
                ContentType = "application/json"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        var prompt = "Write a greeting.";

        // Act
        var result = await service.GetTextContentsAsync(prompt, executionSettings).ConfigureAwait(true);

        // Assert
        InvokeModelRequest? invokeModelRequest = null;
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

        Assert.NotNull(requestedBody);
        using var requestBodyStream = requestedBody;
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
    /// Checks that the prompt execution settings are correctly registered for the text generation call with Cohere Command.
    /// </summary>
    [Fact]
    public async Task CommandExecutionSettingsPropertySetsProperlyAsync()
    {
        // Arrange
        MemoryStream? requestedBody = null;
        string modelId = "cohere.command-text-generation";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonCommandExecutionSettings()
        {
            Temperature = 0.8,
            TopP = 0.95,
            MaxTokens = 256,
            StopSequences = ["</end>"],
            ModelId = modelId
        };
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .Callback<InvokeModelRequest, CancellationToken>((request, cancellationToken) =>
            {
                // Copy the MemoryStream from the request body to avoid (disposal during assertion)
                if (request.Body != null)
                {
                    requestedBody = new MemoryStream();
                    request.Body.CopyTo(requestedBody);
                    requestedBody.Position = 0; // Reset position to the beginning
                    request.Body.Position = 0; // Reset position to the beginning
                }
            })
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new CommandResponse
                {
                    Id = "my-request-id",
                    Prompt = "Write a greeting.",
                    Generations =
                    [
                        new() {
                            Id = "generation-id",
                            Text = "Hello! This is a mock Cohere Command response.",
                            FinishReason = "COMPLETE",
                            IsFinished = true
                        }
                    ]
                }))),
                ContentType = "application/json"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        var prompt = "Write a greeting.";

        // Act
        var result = await service.GetTextContentsAsync(prompt, executionSettings).ConfigureAwait(true);

        // Assert
        InvokeModelRequest? invokeModelRequest = null;
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

        Assert.NotNull(requestedBody);
        using var requestBodyStream = requestedBody;
        var requestBodyJson = await JsonDocument.ParseAsync(requestBodyStream).ConfigureAwait(true);
        var requestBodyRoot = requestBodyJson.RootElement;

        Assert.True(requestBodyRoot.TryGetProperty("temperature", out var temperatureProperty));
        Assert.Equal(executionSettings.Temperature, temperatureProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("p", out var topPProperty));
        Assert.Equal(executionSettings.TopP, topPProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("max_tokens", out var maxTokensProperty));
        Assert.Equal(executionSettings.MaxTokens, maxTokensProperty.GetInt32());

        Assert.True(requestBodyRoot.TryGetProperty("stop_sequences", out var stopSequencesProperty));
        var stopSequences = stopSequencesProperty.EnumerateArray().Select(e => e.GetString()).ToList();
        Assert.Equal(executionSettings.StopSequences, stopSequences!);
    }

    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the text generation call with Mistral.
    /// </summary>
    [Fact]
    public async Task MistralExecutionSettingsSetExtensionDataAsync()
    {
        // Arrange
        MemoryStream? requestedBody = null;
        string modelId = "mistral.mistral-text-generation";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonMistralExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.8f },
                { "top_p", 0.95f },
                { "max_tokens", 256 }
            }
        };
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .Callback<InvokeModelRequest, CancellationToken>((request, cancellationToken) =>
            {
                // Copy the MemoryStream from the request body to avoid (disposal during assertion)
                if (request.Body != null)
                {
                    requestedBody = new MemoryStream();
                    request.Body.CopyTo(requestedBody);
                    requestedBody.Position = 0; // Reset position to the beginning
                    request.Body.Position = 0; // Reset position to the beginning
                }
            })
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new MistralResponse
                {
                    Outputs =
                    [
                        new() {
                            Text = "Hello! This is a mock Mistral response.",
                            StopReason = "stop_sequence"
                        }
                    ]
                }))),
                ContentType = "application/json"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        var prompt = "Write a greeting.";

        // Act
        var result = await service.GetTextContentsAsync(prompt, executionSettings).ConfigureAwait(true);

        // Assert
        InvokeModelRequest? invokeModelRequest = null;
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

        Assert.NotNull(requestedBody);
        using var requestBodyStream = requestedBody;
        var requestBodyJson = await JsonDocument.ParseAsync(requestBodyStream).ConfigureAwait(true);
        var requestBodyRoot = requestBodyJson.RootElement;

        Assert.True(requestBodyRoot.TryGetProperty("temperature", out var temperatureProperty));
        Assert.Equal(executionSettings.ExtensionData["temperature"], (float)temperatureProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("top_p", out var topPProperty));
        Assert.Equal(executionSettings.ExtensionData["top_p"], (float)topPProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("max_tokens", out var maxTokensProperty));
        Assert.Equal(executionSettings.ExtensionData["max_tokens"], maxTokensProperty.GetInt32());
    }

    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the text generation call with Mistral.
    /// </summary>
    [Fact]
    public async Task MistralExecutionSettingsPropertiesSetAsync()
    {
        // Arrange
        MemoryStream? requestedBody = null;
        string modelId = "mistral.mistral-text-generation";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonMistralExecutionSettings()
        {
            Temperature = 0.8f,
            TopP = 0.95f,
            MaxTokens = 256,
            ModelId = modelId,
        };
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<InvokeModelRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.InvokeModelAsync(It.IsAny<InvokeModelRequest>(), It.IsAny<CancellationToken>()))
            .Callback<InvokeModelRequest, CancellationToken>((request, cancellationToken) =>
            {
                // Copy the MemoryStream from the request body to avoid (disposal during assertion)
                if (request.Body != null)
                {
                    requestedBody = new MemoryStream();
                    request.Body.CopyTo(requestedBody);
                    requestedBody.Position = 0; // Reset position to the beginning
                    request.Body.Position = 0; // Reset position to the beginning
                }
            })
            .ReturnsAsync(new InvokeModelResponse
            {
                Body = new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new MistralResponse
                {
                    Outputs =
                    [
                        new() {
                            Text = "Hello! This is a mock Mistral response.",
                            StopReason = "stop_sequence"
                        }
                    ]
                }))),
                ContentType = "application/json"
            });
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();
        var prompt = "Write a greeting.";

        // Act
        var result = await service.GetTextContentsAsync(prompt, executionSettings).ConfigureAwait(true);

        // Assert
        InvokeModelRequest? invokeModelRequest = null;
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

        Assert.NotNull(requestedBody);
        using var requestBodyStream = requestedBody;
        var requestBodyJson = await JsonDocument.ParseAsync(requestBodyStream).ConfigureAwait(true);
        var requestBodyRoot = requestBodyJson.RootElement;

        Assert.True(requestBodyRoot.TryGetProperty("temperature", out var temperatureProperty));
        Assert.Equal(executionSettings.Temperature, (float)temperatureProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("top_p", out var topPProperty));
        Assert.Equal(executionSettings.TopP, (float)topPProperty.GetDouble());

        Assert.True(requestBodyRoot.TryGetProperty("max_tokens", out var maxTokensProperty));
        Assert.Equal(executionSettings.MaxTokens, maxTokensProperty.GetInt32());
    }
}
