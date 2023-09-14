// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
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
        OpenAIRequestSettings requestSettings = OpenAIRequestSettings.FromRequestSettings(actualSettings, null);

        // Assert
        Assert.NotNull(requestSettings);
        Assert.Equal(actualSettings, requestSettings);
    }

    [Fact]
    public void ItCreatesOpenAIRequestSettingsFromAnonymousTypeSnakeCase()
    {
        // Arrange
        var actualSettings = new
        {
            temperature = 0.7,
            top_p = 0.7,
            frequency_penalty = 0.7,
            presence_penalty = 0.7,
            results_per_prompt = 2,
            stop_sequences = new string[] { "foo", "bar" },
            chat_system_prompt = "chat system prompt",
            max_tokens = 128,
            service_id = "service",
            token_selection_biases = new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } },
        };

        // Act
        OpenAIRequestSettings requestSettings = OpenAIRequestSettings.FromRequestSettings(actualSettings, null);

        // Assert
        Assert.NotNull(requestSettings);
        Assert.Equal(actualSettings.temperature, requestSettings.Temperature);
        Assert.Equal(actualSettings.top_p, requestSettings.TopP);
        Assert.Equal(actualSettings.frequency_penalty, requestSettings.FrequencyPenalty);
        Assert.Equal(actualSettings.presence_penalty, requestSettings.PresencePenalty);
        Assert.Equal(actualSettings.results_per_prompt, requestSettings.ResultsPerPrompt);
        Assert.Equal(actualSettings.stop_sequences, requestSettings.StopSequences);
        Assert.Equal(actualSettings.chat_system_prompt, requestSettings.ChatSystemPrompt);
        Assert.Equal(actualSettings.token_selection_biases, requestSettings.TokenSelectionBiases);
        Assert.Equal(actualSettings.service_id, requestSettings.ServiceId);
        Assert.Equal(actualSettings.max_tokens, requestSettings.MaxTokens);
    }

    [Fact]
    public void ItCreatesOpenAIRequestSettingsFromAnonymousTypePascalCase()
    {
        // Arrange
        var actualSettings = new
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
        OpenAIRequestSettings requestSettings = OpenAIRequestSettings.FromRequestSettings(actualSettings, null);

        // Assert
        Assert.NotNull(requestSettings);
        Assert.Equal(actualSettings.Temperature, requestSettings.Temperature);
        Assert.Equal(actualSettings.TopP, requestSettings.TopP);
        Assert.Equal(actualSettings.FrequencyPenalty, requestSettings.FrequencyPenalty);
        Assert.Equal(actualSettings.PresencePenalty, requestSettings.PresencePenalty);
        Assert.Equal(actualSettings.ResultsPerPrompt, requestSettings.ResultsPerPrompt);
        Assert.Equal(actualSettings.StopSequences, requestSettings.StopSequences);
        Assert.Equal(actualSettings.ChatSystemPrompt, requestSettings.ChatSystemPrompt);
        Assert.Equal(actualSettings.TokenSelectionBiases, requestSettings.TokenSelectionBiases);
        Assert.Equal(actualSettings.ServiceId, requestSettings.ServiceId);
        Assert.Equal(actualSettings.MaxTokens, requestSettings.MaxTokens);
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
        JsonDocument document = JsonDocument.Parse(json);
        JsonElement actualSettings = document.RootElement;

        // Act
        OpenAIRequestSettings requestSettings = OpenAIRequestSettings.FromRequestSettings(actualSettings, null);

        // Assert
        Assert.NotNull(requestSettings);
        Assert.Equal(actualSettings.GetProperty("temperature").GetDouble(), requestSettings.Temperature);
        Assert.Equal(actualSettings.GetProperty("top_p").GetDouble(), requestSettings.TopP);
        Assert.Equal(actualSettings.GetProperty("frequency_penalty").GetDouble(), requestSettings.FrequencyPenalty);
        Assert.Equal(actualSettings.GetProperty("presence_penalty").GetDouble(), requestSettings.PresencePenalty);
        Assert.Equal(actualSettings.GetProperty("results_per_prompt").GetInt32(), requestSettings.ResultsPerPrompt);
        Assert.Equal(new string[] { "foo", "bar" }, requestSettings.StopSequences);
        Assert.Equal(actualSettings.GetProperty("chat_system_prompt").GetString(), requestSettings.ChatSystemPrompt);
        Assert.Equal(new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } }, requestSettings.TokenSelectionBiases);
        Assert.Equal(actualSettings.GetProperty("service_id").GetString(), requestSettings.ServiceId);
        Assert.Equal(actualSettings.GetProperty("max_tokens").GetInt32(), requestSettings.MaxTokens);
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
        JsonDocument document = JsonDocument.Parse(json);
        JsonElement actualSettings = document.RootElement;

        // Act
        OpenAIRequestSettings requestSettings = OpenAIRequestSettings.FromRequestSettings(actualSettings, null);

        // Assert
        Assert.NotNull(requestSettings);
        Assert.Equal(actualSettings.GetProperty("Temperature").GetDouble(), requestSettings.Temperature);
        Assert.Equal(actualSettings.GetProperty("TopP").GetDouble(), requestSettings.TopP);
        Assert.Equal(actualSettings.GetProperty("FrequencyPenalty").GetDouble(), requestSettings.FrequencyPenalty);
        Assert.Equal(actualSettings.GetProperty("PresencePenalty").GetDouble(), requestSettings.PresencePenalty);
        Assert.Equal(actualSettings.GetProperty("ResultsPerPrompt").GetInt32(), requestSettings.ResultsPerPrompt);
        Assert.Equal(new string[] { "foo", "bar" }, requestSettings.StopSequences);
        Assert.Equal(actualSettings.GetProperty("ChatSystemPrompt").GetString(), requestSettings.ChatSystemPrompt);
        Assert.Equal(new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } }, requestSettings.TokenSelectionBiases);
        Assert.Equal(actualSettings.GetProperty("ServiceId").GetString(), requestSettings.ServiceId);
        Assert.Equal(actualSettings.GetProperty("MaxTokens").GetInt32(), requestSettings.MaxTokens);
    }
}
