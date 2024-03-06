// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// Unit tests of OpenAIPromptExecutionSettings
/// </summary>
public class OpenAIPromptExecutionSettingsTests
{
    [Fact]
    public void ItCreatesOpenAIExecutionSettingsWithCorrectDefaults()
    {
        // Arrange
        // Act
        OpenAIPromptExecutionSettings executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(null, 128);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(1, executionSettings.Temperature);
        Assert.Equal(1, executionSettings.TopP);
        Assert.Equal(0, executionSettings.FrequencyPenalty);
        Assert.Equal(0, executionSettings.PresencePenalty);
        Assert.Equal(1, executionSettings.ResultsPerPrompt);
        Assert.Null(executionSettings.StopSequences);
        Assert.Null(executionSettings.TokenSelectionBiases);
        Assert.Equal(128, executionSettings.MaxTokens);
    }

    [Fact]
    public void ItUsesExistingOpenAIExecutionSettings()
    {
        // Arrange
        OpenAIPromptExecutionSettings actualSettings = new()
        {
            Temperature = 0.7,
            TopP = 0.7,
            FrequencyPenalty = 0.7,
            PresencePenalty = 0.7,
            ResultsPerPrompt = 2,
            StopSequences = new string[] { "foo", "bar" },
            ChatSystemPrompt = "chat system prompt",
            MaxTokens = 128,
            TokenSelectionBiases = new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } },
        };

        // Act
        OpenAIPromptExecutionSettings executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(actualSettings, executionSettings);
    }

    [Fact]
    public void ItCanUseOpenAIExecutionSettings()
    {
        // Arrange
        PromptExecutionSettings actualSettings = new()
        {
            ExtensionData = new Dictionary<string, object>() {
                { "max_tokens", 1000 },
                { "temperature", 0 }
            }
        };

        // Act
        OpenAIPromptExecutionSettings executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(actualSettings, null);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(1000, executionSettings.MaxTokens);
        Assert.Equal(0, executionSettings.Temperature);
    }

    [Fact]
    public void ItCreatesOpenAIExecutionSettingsFromExtraPropertiesSnakeCase()
    {
        // Arrange
        PromptExecutionSettings actualSettings = new()
        {
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.7 },
                { "top_p", 0.7 },
                { "frequency_penalty", 0.7 },
                { "presence_penalty", 0.7 },
                { "results_per_prompt", 2 },
                { "stop_sequences", new [] { "foo", "bar" } },
                { "chat_system_prompt", "chat system prompt" },
                { "max_tokens", 128 },
                { "token_selection_biases", new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } } },
                { "seed", 123456 },
            }
        };

        // Act
        OpenAIPromptExecutionSettings executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(actualSettings, null);

        // Assert
        AssertExecutionSettings(executionSettings);
        Assert.Equal(executionSettings.Seed, 123456);
    }

    [Fact]
    public void ItCreatesOpenAIExecutionSettingsFromExtraPropertiesAsStrings()
    {
        // Arrange
        PromptExecutionSettings actualSettings = new()
        {
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", "0.7" },
                { "top_p", "0.7" },
                { "frequency_penalty", "0.7" },
                { "presence_penalty", "0.7" },
                { "results_per_prompt", "2" },
                { "stop_sequences", new [] { "foo", "bar" } },
                { "chat_system_prompt", "chat system prompt" },
                { "max_tokens", "128" },
                { "token_selection_biases", new Dictionary<string, string>() { { "1", "2" }, { "3", "4" } } }
            }
        };

        // Act
        OpenAIPromptExecutionSettings executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(actualSettings, null);

        // Assert
        AssertExecutionSettings(executionSettings);
    }

    [Fact]
    public void ItCreatesOpenAIExecutionSettingsFromJsonSnakeCase()
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
  ""max_tokens"": 128
}";
        var actualSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(json);

        // Act
        OpenAIPromptExecutionSettings executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        AssertExecutionSettings(executionSettings);
    }

    [Theory]
    [InlineData("", "Assistant is a large language model.")]
    [InlineData("System prompt", "System prompt")]
    public void ItUsesCorrectChatSystemPrompt(string chatSystemPrompt, string expectedChatSystemPrompt)
    {
        // Arrange & Act
        var settings = new OpenAIPromptExecutionSettings { ChatSystemPrompt = chatSystemPrompt };

        // Assert
        Assert.Equal(expectedChatSystemPrompt, settings.ChatSystemPrompt);
    }

    [Fact]
    public void PromptExecutionSettingsCloneWorksAsExpected()
    {
        // Arrange
        string configPayload = @"{
            ""max_tokens"": 60,
            ""temperature"": 0.5,
            ""top_p"": 0.0,
            ""presence_penalty"": 0.0,
            ""frequency_penalty"": 0.0
        }";
        var executionSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(configPayload);

        // Act
        var clone = executionSettings!.Clone();

        // Assert
        Assert.NotNull(clone);
        Assert.Equal(executionSettings.ModelId, clone.ModelId);
        Assert.Equivalent(executionSettings.ExtensionData, clone.ExtensionData);
    }

    [Fact]
    public void PromptExecutionSettingsFreezeWorksAsExpected()
    {
        // Arrange
        string configPayload = @"{
            ""max_tokens"": 60,
            ""temperature"": 0.5,
            ""top_p"": 0.0,
            ""presence_penalty"": 0.0,
            ""frequency_penalty"": 0.0
        }";
        var executionSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(configPayload);

        // Act
        executionSettings!.Freeze();

        // Assert
        Assert.True(executionSettings.IsFrozen);
        Assert.Throws<InvalidOperationException>(() => executionSettings.ModelId = "gpt-4");
        Assert.Throws<InvalidOperationException>(() => executionSettings.ResultsPerPrompt = 2);
        Assert.Throws<InvalidOperationException>(() => executionSettings.Temperature = 1);
    }

    private static void AssertExecutionSettings(OpenAIPromptExecutionSettings executionSettings)
    {
        Assert.NotNull(executionSettings);
        Assert.Equal(0.7, executionSettings.Temperature);
        Assert.Equal(0.7, executionSettings.TopP);
        Assert.Equal(0.7, executionSettings.FrequencyPenalty);
        Assert.Equal(0.7, executionSettings.PresencePenalty);
        Assert.Equal(2, executionSettings.ResultsPerPrompt);
        Assert.Equal(new string[] { "foo", "bar" }, executionSettings.StopSequences);
        Assert.Equal("chat system prompt", executionSettings.ChatSystemPrompt);
        Assert.Equal(new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } }, executionSettings.TokenSelectionBiases);
        Assert.Equal(128, executionSettings.MaxTokens);
    }
}
