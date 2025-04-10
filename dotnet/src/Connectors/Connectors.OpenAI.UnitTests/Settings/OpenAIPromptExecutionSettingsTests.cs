// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Settings;

/// <summary>
/// Unit tests of OpenAIPromptExecutionSettingsTests
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
        Assert.Null(executionSettings.Temperature);
        Assert.Null(executionSettings.TopP);
        Assert.Null(executionSettings.FrequencyPenalty);
        Assert.Null(executionSettings.PresencePenalty);
        Assert.Null(executionSettings.StopSequences);
        Assert.Null(executionSettings.TokenSelectionBiases);
        Assert.Null(executionSettings.TopLogprobs);
        Assert.Null(executionSettings.Logprobs);
        Assert.Equal(128, executionSettings.MaxTokens);
        Assert.Null(executionSettings.Store);
        Assert.Null(executionSettings.Metadata);
        Assert.Null(executionSettings.Seed);
        Assert.Null(executionSettings.ReasoningEffort);
        Assert.Null(executionSettings.ChatSystemPrompt);
        Assert.Null(executionSettings.ChatDeveloperPrompt);
        Assert.Null(executionSettings.Audio);
        Assert.Null(executionSettings.Modalities);
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
            StopSequences = ["foo", "bar"],
            ChatSystemPrompt = "chat system prompt",
            ChatDeveloperPrompt = "chat developer prompt",
            MaxTokens = 128,
            Logprobs = true,
            TopLogprobs = 5,
            TokenSelectionBiases = new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } },
            Seed = 123456,
            Store = true,
            Metadata = new Dictionary<string, string>() { { "foo", "bar" } },
            ReasoningEffort = "high",
            Audio = JsonSerializer.Deserialize<JsonElement>("{\"format\":\"mp3\", \"voice\": \"alloy\"}"),
            Modalities = new List<string> { "audio", "text" }
        };

        // Act
        OpenAIPromptExecutionSettings executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(actualSettings, executionSettings);
        Assert.Equal(actualSettings.MaxTokens, executionSettings.MaxTokens);
        Assert.Equal(actualSettings.Logprobs, executionSettings.Logprobs);
        Assert.Equal(actualSettings.TopLogprobs, executionSettings.TopLogprobs);
        Assert.Equal(actualSettings.TokenSelectionBiases, executionSettings.TokenSelectionBiases);
        Assert.Equal(actualSettings.Seed, executionSettings.Seed);
        Assert.Equal(actualSettings.Store, executionSettings.Store);
        Assert.Equal(actualSettings.Metadata, executionSettings.Metadata);
        Assert.Equal(actualSettings.ReasoningEffort, executionSettings.ReasoningEffort);
        Assert.Equal(actualSettings.ChatSystemPrompt, executionSettings.ChatSystemPrompt);
        Assert.Equal(actualSettings.ChatDeveloperPrompt, executionSettings.ChatDeveloperPrompt);
        Assert.Equal(actualSettings.Audio, executionSettings.Audio);
        Assert.Equal(actualSettings.Modalities, executionSettings.Modalities);
    }

    [Fact]
    public void ItCanUseOpenAIExecutionSettings()
    {
        // Arrange
        PromptExecutionSettings actualSettings = new()
        {
            ExtensionData = new Dictionary<string, object>() {
                { "max_tokens", 1000 },
                { "temperature", 0 },
                { "store", true },
                { "metadata", new Dictionary<string, string>() { { "foo", "bar" } } }
            }
        };

        // Act
        OpenAIPromptExecutionSettings executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(actualSettings, null);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(1000, executionSettings.MaxTokens);
        Assert.Equal(0, executionSettings.Temperature);
        Assert.True(executionSettings.Store);
        Assert.Equal(new Dictionary<string, string>() { { "foo", "bar" } }, executionSettings.Metadata);
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
                { "chat_developer_prompt", "chat developer prompt" },
                { "reasoning_effort", "high" },
                { "max_tokens", 128 },
                { "token_selection_biases", new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } } },
                { "seed", 123456 },
                { "logprobs", true },
                { "top_logprobs", 5 },
                { "store", true },
                { "audio", JsonSerializer.Deserialize<JsonElement>("{\"format\":\"mp3\", \"voice\": \"alloy\"}") },
                { "modalities", new [] { "audio", "text" } },
                { "metadata", new Dictionary<string, string>() { { "foo", "bar" } } }
            }
        };

        // Act
        OpenAIPromptExecutionSettings executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(actualSettings, null);

        // Assert
        AssertExecutionSettings(executionSettings);
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
                { "chat_developer_prompt", "chat developer prompt" },
                { "reasoning_effort", "high" },
                { "max_tokens", "128" },
                { "token_selection_biases", new Dictionary<string, string>() { { "1", "2" }, { "3", "4" } } },
                { "seed", 123456 },
                { "logprobs", true },
                { "top_logprobs", 5 },
                { "store", true },
                { "audio", new Dictionary<string, string>() { ["format"] = "mp3", ["voice"] = "alloy" } },
                { "modalities", new [] { "audio", "text" } },
                { "metadata", new Dictionary<string, string>() { { "foo", "bar" } } }
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
        var json = """
            {
              "temperature": 0.7,
              "top_p": 0.7,
              "frequency_penalty": 0.7,
              "presence_penalty": 0.7,
              "results_per_prompt": 2,
              "stop_sequences": [ "foo", "bar" ],
              "chat_system_prompt": "chat system prompt",
              "chat_developer_prompt": "chat developer prompt",
              "reasoning_effort": "high",
              "token_selection_biases": { "1": 2, "3": 4 },
              "max_tokens": 128,
              "seed": 123456,
              "logprobs": true,
              "top_logprobs": 5,
              "audio": { "format": "mp3", "voice": "alloy" },
              "modalities": ["audio", "text"],
              "store": true,
              "metadata": { "foo": "bar" }
            }
            """;
        var actualSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(json);

        // Act
        OpenAIPromptExecutionSettings executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        AssertExecutionSettings(executionSettings);
    }

    [Theory]
    [InlineData("", "")]
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
        string configPayload = """
        {
            "max_tokens": 60,
            "temperature": 0.5,
            "top_p": 0.0,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0
        }
        """;
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
        string configPayload = """
        {
            "max_tokens": 60,
            "temperature": 0.5,
            "top_p": 0.0,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
            "stop_sequences": [ "DONE" ],
            "token_selection_biases": { "1": 2, "3": 4 },
            "seed": 123456,
            "logprobs": true,
            "top_logprobs": 5,
            "store": true,
            "audio": { "format": "mp3", "voice": "alloy" },
            "modalities": ["audio", "text"],
            "metadata": { "foo": "bar" }
        }
        """;
        var executionSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(configPayload);

        // Act
        executionSettings!.Freeze();

        // Assert
        Assert.True(executionSettings.IsFrozen);
        Assert.Throws<InvalidOperationException>(() => executionSettings.ModelId = "gpt-4");
        Assert.Throws<InvalidOperationException>(() => executionSettings.Temperature = 1);
        Assert.Throws<InvalidOperationException>(() => executionSettings.TopP = 1);
        Assert.Throws<NotSupportedException>(() => executionSettings.StopSequences?.Add("STOP"));
        Assert.Throws<NotSupportedException>(() => executionSettings.TokenSelectionBiases?.Add(5, 6));
        Assert.Throws<InvalidOperationException>(() => executionSettings.Seed = 654321);
        Assert.Throws<InvalidOperationException>(() => executionSettings.Logprobs = false);
        Assert.Throws<InvalidOperationException>(() => executionSettings.TopLogprobs = 10);
        Assert.Throws<InvalidOperationException>(() => executionSettings.Store = false);
        Assert.Throws<NotSupportedException>(() => executionSettings.Metadata?.Add("bar", "baz"));
        Assert.Throws<InvalidOperationException>(() => executionSettings.Audio = new object());
        Assert.Throws<InvalidOperationException>(() => executionSettings.Modalities = new object());

        executionSettings!.Freeze(); // idempotent
        Assert.True(executionSettings.IsFrozen);
    }

    [Fact]
    public void FromExecutionSettingsWithDataDoesNotIncludeEmptyStopSequences()
    {
        // Arrange
        PromptExecutionSettings settings = new OpenAIPromptExecutionSettings { StopSequences = [] };

        // Act
        var executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(settings);

        // Assert
        Assert.NotNull(executionSettings.StopSequences);
        Assert.Empty(executionSettings.StopSequences);
    }

    [Fact]
    public void ItRestoresOriginalFunctionChoiceBehavior()
    {
        // Arrange
        var functionChoiceBehavior = FunctionChoiceBehavior.None();

        var originalExecutionSettings = new PromptExecutionSettings
        {
            FunctionChoiceBehavior = functionChoiceBehavior
        };

        // Act
        var result = OpenAIPromptExecutionSettings.FromExecutionSettings(originalExecutionSettings);

        // Assert
        Assert.Equal(functionChoiceBehavior, result.FunctionChoiceBehavior);
    }

    [Fact]
    public void ItCanCreateOpenAIPromptExecutionSettingsFromPromptExecutionSettings()
    {
        // Arrange
        PromptExecutionSettings originalSettings = new()
        {
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.7 },
                { "top_p", 0.7 },
                { "frequency_penalty", 0.7 },
                { "presence_penalty", 0.7 },
                { "stop_sequences", new string[] { "foo", "bar" } },
                { "chat_system_prompt", "chat system prompt" },
                { "chat_developer_prompt", "chat developer prompt" },
                { "reasoning_effort", "high" },
                { "token_selection_biases", new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } } },
                { "max_tokens", 128 },
                { "logprobs", true },
                { "seed", 123456 },
                { "store", true },
                { "top_logprobs", 5 },
                { "audio", JsonSerializer.Deserialize<JsonElement>("{\"format\":\"mp3\", \"voice\": \"alloy\"}") },
                { "modalities", new [] { "audio", "text" } },
                { "metadata", new Dictionary<string, string>() { { "foo", "bar" } } }
            }
        };

        // Act
        OpenAIPromptExecutionSettings executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(originalSettings);

        // Assert
        AssertExecutionSettings(executionSettings);
    }

    [Fact]
    public void ItCanCreateOpenAIPromptExecutionSettingsFromJson()
    {
        // Arrange
        var json =
            """
            {
                "temperature": 0.7,
                "top_p": 0.7,
                "frequency_penalty": 0.7,
                "presence_penalty": 0.7,
                "stop_sequences": [ "foo", "bar" ],
                "chat_system_prompt": "chat system prompt",
                "chat_developer_prompt": "chat developer prompt",
                "reasoning_effort": "high",
                "token_selection_biases":
                {
                    "1": "2",
                    "3": "4"
                },
                "max_tokens": 128,
                "logprobs": true,
                "seed": 123456,
                "store": true,
                "top_logprobs": 5,
                "audio":
                {
                    "format": "mp3",
                    "voice": "alloy"
                },
                "modalities": [ "audio", "text" ],
                "metadata":
                {
                    "foo": "bar"
                }
            }
            """;

        // Act
        var originalSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(json);
        OpenAIPromptExecutionSettings executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(originalSettings);

        // Assert
        AssertExecutionSettings(executionSettings);
    }

    [Fact]
    public void ItCanCreateOpenAIPromptExecutionSettingsFromPromptExecutionSettingsWithIncorrectTypes()
    {
        // Arrange
        PromptExecutionSettings originalSettings = new()
        {
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", "0.7" },
                { "top_p", "0.7" },
                { "frequency_penalty", "0.7" },
                { "presence_penalty", "0.7" },
                { "stop_sequences", new List<object> { "foo", "bar" } },
                { "chat_system_prompt", "chat system prompt" },
                { "chat_developer_prompt", "chat developer prompt" },
                { "reasoning_effort", "high" },
                { "token_selection_biases", new Dictionary<string, object>() { { "1", "2" }, { "3", "4" } } },
                { "max_tokens", "128" },
                { "logprobs", "true" },
                { "seed", "123456" },
                { "store", true },
                { "top_logprobs", "5" },
                { "audio", JsonSerializer.Deserialize<JsonElement>("{\"format\":\"mp3\", \"voice\": \"alloy\"}") },
                { "modalities", new [] { "audio", "text" } },
                { "metadata", new Dictionary<string, string>() { { "foo", "bar" } } }
            }
        };

        // Act
        OpenAIPromptExecutionSettings executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(originalSettings);

        // Assert
        AssertExecutionSettings(executionSettings);
    }

    [Theory]
    [InlineData("")]
    [InlineData("123")]
    [InlineData("Foo")]
    [InlineData(1)]
    [InlineData(1.0)]
    public void ItCannotCreateOpenAIPromptExecutionSettingsWithInvalidBoolValues(object value)
    {
        // Arrange
        PromptExecutionSettings originalSettings = new()
        {
            ExtensionData = new Dictionary<string, object>()
            {
                { "logprobs", value }
            }
        };

        // Act & Assert
        Assert.Throws<ArgumentException>(() => OpenAIPromptExecutionSettings.FromExecutionSettings(originalSettings));
    }

    private static void AssertExecutionSettings(OpenAIPromptExecutionSettings executionSettings)
    {
        Assert.NotNull(executionSettings);
        Assert.Equal(0.7, executionSettings.Temperature);
        Assert.Equal(0.7, executionSettings.TopP);
        Assert.Equal(0.7, executionSettings.FrequencyPenalty);
        Assert.Equal(0.7, executionSettings.PresencePenalty);
        Assert.Equal(new string[] { "foo", "bar" }, executionSettings.StopSequences);
        Assert.Equal("chat system prompt", executionSettings.ChatSystemPrompt);
        Assert.Equal("chat developer prompt", executionSettings.ChatDeveloperPrompt);
        Assert.Equal("high", executionSettings.ReasoningEffort!.ToString());
        Assert.Equal(new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } }, executionSettings.TokenSelectionBiases);
        Assert.Equal(128, executionSettings.MaxTokens);
        Assert.Equal(123456, executionSettings.Seed);
        Assert.Equal(true, executionSettings.Logprobs);
        Assert.Equal(5, executionSettings.TopLogprobs);
        Assert.Equal(true, executionSettings.Store);
        Assert.Equal(new Dictionary<string, string>() { { "foo", "bar" } }, executionSettings.Metadata);
        Assert.Equal("""{"format":"mp3","voice":"alloy"}""", JsonSerializer.Serialize(executionSettings.Audio));
        Assert.Equal("""["audio","text"]""", JsonSerializer.Serialize(executionSettings.Modalities));
    }
}
