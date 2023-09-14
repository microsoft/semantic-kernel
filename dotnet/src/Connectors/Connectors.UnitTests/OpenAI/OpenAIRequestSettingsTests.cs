// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Text;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// Unit tests of OpenAIRequestSettings
/// </summary>
public class OpenAIRequestSettingsTests
{
    [Fact]
    public void ItCreatesOpenAIRequestSettingsWithCorrectDefaults()
    {
        // Arrange
        // Act
        OpenAIRequestSettings requestSettings = OpenAIRequestSettings.FromRequestSettings(null, 128);

        // Assert
        Assert.NotNull(requestSettings);
        Assert.Equal(0, requestSettings.Temperature);
        Assert.Equal(0, requestSettings.TopP);
        Assert.Equal(0, requestSettings.FrequencyPenalty);
        Assert.Equal(0, requestSettings.PresencePenalty);
        Assert.Equal(1, requestSettings.ResultsPerPrompt);
        Assert.Equal(Array.Empty<string>(), requestSettings.StopSequences);
        Assert.Equal(new Dictionary<int, int>(), requestSettings.TokenSelectionBiases);
        Assert.Null(requestSettings.ServiceId);
        Assert.Equal(128, requestSettings.MaxTokens);
    }

    [Fact]
    public void ItUsesExistingOpenAIRequestSettings()
    {
        // Arrange
        OpenAIRequestSettings actualSettings = new()
        {
            Temperature = 0.7,
            TopP = 0.7,
            FrequencyPenalty = 0.7,
            PresencePenalty = 0.7,
            ResultsPerPrompt = 2,
            StopSequences = new string[] { "foo", "bar" },
            ChatSystemPrompt = "chat system prompt",
            MaxTokens = 128,
            ServiceId = "service",
            TokenSelectionBiases = new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } },
        };

        // Act
        OpenAIRequestSettings requestSettings = OpenAIRequestSettings.FromRequestSettings(actualSettings);

        // Assert
        Assert.NotNull(requestSettings);
        Assert.Equal(actualSettings, requestSettings);
    }

    [Fact]
    public void ItCanUseOpenAIRequestSettings()
    {
        // Arrange
        AIRequestSettings actualSettings = new()
        {
            ServiceId = "service",
        };

        // Act
        OpenAIRequestSettings requestSettings = OpenAIRequestSettings.FromRequestSettings(actualSettings, null);

        // Assert
        Assert.NotNull(requestSettings);
        Assert.Equal(actualSettings.ServiceId, requestSettings.ServiceId);
    }

    [Fact]
    public void ItCreatesOpenAIRequestSettingsFromExtraPropertiesSnakeCase()
    {
        // Arrange
        AIRequestSettings actualSettings = new()
        {
            ServiceId = "service",
            ExtraProperties = new Dictionary<string, object>()
            {
                { "temperature", 0.7 },
                { "top_p", 0.7 },
                { "frequency_penalty", 0.7 },
                { "presence_penalty", 0.7 },
                { "results_per_prompt", 2 },
                { "stop_sequences", new [] { "foo", "bar" } },
                { "chat_system_prompt", "chat system prompt" },
                { "max_tokens", 128 },
                { "service_id", "service" },
                { "token_selection_biases", new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } } }
            }
        };

        // Act
        OpenAIRequestSettings requestSettings = OpenAIRequestSettings.FromRequestSettings(actualSettings, null);

        // Assert
        AssertRequestSettings(requestSettings);
    }

    [Fact]
    public void ItCreatesOpenAIRequestSettingsFromExtraPropertiesPascalCase()
    {
        // Arrange
        AIRequestSettings actualSettings = new()
        {
            ServiceId = "service",
            ExtraProperties = new Dictionary<string, object>()
            {
                { "Temperature", 0.7 },
                { "TopP", 0.7 },
                { "FrequencyPenalty", 0.7 },
                { "PresencePenalty", 0.7 },
                { "ResultsPerPrompt", 2 },
                { "StopSequences", new[] { "foo", "bar" } },
                { "ChatSystemPrompt", "chat system prompt" },
                { "MaxTokens", 128 },
                { "ServiceId", "service" },
                { "TokenSelectionBiases", new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } } }
            }
        };

        // Act
        OpenAIRequestSettings requestSettings = OpenAIRequestSettings.FromRequestSettings(actualSettings);

        // Assert
        AssertRequestSettings(requestSettings);
    }

    [Fact]
    public void ItCreatesOpenAIRequestSettingsFromJsonSnakeCase()
    {
        // Arrange
        var json = @"{
  ""temperature"": 0.7,
  ""top_p"": 0.7,
  ""frequency_penalty"": 0.7,
  ""presence_penalty"": 0.7,
  ""results_per_prompt"": 2,
  ""stop_sequences"": [ ""foo"", ""bar"" ],
  ""chat_system_prompt"": ""chat system prompt"",
  ""token_selection_biases"": { ""1"": 2, ""3"": 4 },
  ""service_id"": ""service"",
  ""max_tokens"": 128
}";
        var actualSettings = Json.Deserialize<AIRequestSettings>(json);

        // Act
        OpenAIRequestSettings requestSettings = OpenAIRequestSettings.FromRequestSettings(actualSettings);

        // Assert
        AssertRequestSettings(requestSettings);
    }

    [Fact]
    public void ItCreatesOpenAIRequestSettingsFromJsonPascalCase()
    {
        // Arrange
        var json = @"{
  ""Temperature"": 0.7,
  ""TopP"": 0.7,
  ""FrequencyPenalty"": 0.7,
  ""PresencePenalty"": 0.7,
  ""ResultsPerPrompt"": 2,
  ""StopSequences"": [ ""foo"", ""bar"" ],
  ""ChatSystemPrompt"": ""chat system prompt"",
  ""TokenSelectionBiases"": { ""1"": 2, ""3"": 4 },
  ""ServiceId"": ""service"",
  ""MaxTokens"": 128
}";
        var actualSettings = Json.Deserialize<AIRequestSettings>(json);

        // Act
        OpenAIRequestSettings requestSettings = OpenAIRequestSettings.FromRequestSettings(actualSettings);

        // Assert
        AssertRequestSettings(requestSettings);
    }

    private static void AssertRequestSettings(OpenAIRequestSettings requestSettings)
    {
        Assert.NotNull(requestSettings);
        Assert.Equal(0.7, requestSettings.Temperature);
        Assert.Equal(0.7, requestSettings.TopP);
        Assert.Equal(0.7, requestSettings.FrequencyPenalty);
        Assert.Equal(0.7, requestSettings.PresencePenalty);
        Assert.Equal(2, requestSettings.ResultsPerPrompt);
        Assert.Equal(new string[] { "foo", "bar" }, requestSettings.StopSequences);
        Assert.Equal("chat system prompt", requestSettings.ChatSystemPrompt);
        Assert.Equal(new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } }, requestSettings.TokenSelectionBiases);
        Assert.Equal("service", requestSettings.ServiceId);
        Assert.Equal(128, requestSettings.MaxTokens);
    }
}
