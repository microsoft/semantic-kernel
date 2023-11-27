// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// Unit tests of OpenAIPromptExecutionSettingsConverter
/// </summary>
public class OpenAIPromptExecutionSettingsConverterTests
{
    [Fact]
    public void ItDeserialisesOpenAIRequestSettingsWithCorrectDefaults()
    {
        // Arrange
        var json = "{}";

        // Act
        var executionSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(json);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(0, executionSettings.Temperature);
        Assert.Equal(0, executionSettings.TopP);
        Assert.Equal(0, executionSettings.FrequencyPenalty);
        Assert.Equal(0, executionSettings.PresencePenalty);
        Assert.Equal(1, executionSettings.ResultsPerPrompt);
        Assert.Equal(Array.Empty<string>(), executionSettings.StopSequences);
        Assert.Equal(new Dictionary<int, int>(), executionSettings.TokenSelectionBiases);
        Assert.Null(executionSettings.ServiceId);
        Assert.Null(executionSettings.MaxTokens);
    }

    [Fact]
    public void ItDeserialisesOpenAIRequestSettingsWithSnakeCaseNaming()
    {
        // Arrange
        var json = @"{
  ""temperature"": 0.7,
  ""top_p"": 0.7,
  ""frequency_penalty"": 0.7,
  ""presence_penalty"": 0.7,
  ""results_per_prompt"": 2,
  ""stop_sequences"": [ ""foo"", ""bar"" ],
  ""token_selection_biases"": { ""1"": 2, ""3"": 4 },
  ""service_id"": ""service"",
  ""max_tokens"": 128
}";

        // Act
        var executionSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(json);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(0.7, executionSettings.Temperature);
        Assert.Equal(0.7, executionSettings.TopP);
        Assert.Equal(0.7, executionSettings.FrequencyPenalty);
        Assert.Equal(0.7, executionSettings.PresencePenalty);
        Assert.Equal(2, executionSettings.ResultsPerPrompt);
        Assert.Equal(new string[] { "foo", "bar" }, executionSettings.StopSequences);
        Assert.Equal(new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } }, executionSettings.TokenSelectionBiases);
        Assert.Equal("service", executionSettings.ServiceId);
        Assert.Equal(128, executionSettings.MaxTokens);
    }

    [Fact]
    public void ItDeserialisesOpenAIRequestSettingsWithPascalCaseNaming()
    {
        // Arrange
        var json = @"{
  ""Temperature"": 0.7,
  ""TopP"": 0.7,
  ""FrequencyPenalty"": 0.7,
  ""PresencePenalty"": 0.7,
  ""ResultsPerPrompt"": 2,
  ""StopSequences"": [ ""foo"", ""bar"" ],
  ""TokenSelectionBiases"": { ""1"": 2, ""3"": 4 },
  ""ServiceId"": ""service"",
  ""MaxTokens"": 128
}";

        // Act
        var executionSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(json);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(0.7, executionSettings.Temperature);
        Assert.Equal(0.7, executionSettings.TopP);
        Assert.Equal(0.7, executionSettings.FrequencyPenalty);
        Assert.Equal(0.7, executionSettings.PresencePenalty);
        Assert.Equal(2, executionSettings.ResultsPerPrompt);
        Assert.Equal(new string[] { "foo", "bar" }, executionSettings.StopSequences);
        Assert.Equal(new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } }, executionSettings.TokenSelectionBiases);
        Assert.Equal("service", executionSettings.ServiceId);
        Assert.Equal(128, executionSettings.MaxTokens);
    }
}
