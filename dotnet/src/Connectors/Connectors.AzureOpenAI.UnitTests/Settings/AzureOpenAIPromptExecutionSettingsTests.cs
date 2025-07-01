// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.OpenAI;

#pragma warning disable CS0618 // Type or member is obsolete

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Settings;

/// <summary>
/// Unit tests for <see cref="AzureOpenAIPromptExecutionSettings"/> class.
/// </summary>
public class AzureOpenAIPromptExecutionSettingsTests
{
    [Fact]
    public void ItCreatesOpenAIExecutionSettingsWithCorrectDefaults()
    {
        // Arrange
        var maxTokensSettings = 128;

        // Act
        AzureOpenAIPromptExecutionSettings executionSettings = AzureOpenAIPromptExecutionSettings.FromExecutionSettings(null, maxTokensSettings);

        // Assert
        Assert.Null(executionSettings.Temperature);
        Assert.Null(executionSettings.TopP);
        Assert.Null(executionSettings.FrequencyPenalty);
        Assert.Null(executionSettings.PresencePenalty);
        Assert.Null(executionSettings.StopSequences);
        Assert.Null(executionSettings.TokenSelectionBiases);
        Assert.Null(executionSettings.TopLogprobs);
        Assert.Null(executionSettings.Logprobs);
        Assert.Null(executionSettings.AzureChatDataSource);
        Assert.Null(executionSettings.UserSecurityContext);
        Assert.False(executionSettings.SetNewMaxCompletionTokensEnabled);
        Assert.Equal(maxTokensSettings, executionSettings.MaxTokens);
        Assert.Null(executionSettings.Store);
        Assert.Null(executionSettings.Metadata);
    }

    [Fact]
    public void ItUsesExistingOpenAIExecutionSettings()
    {
        // Arrange
        AzureOpenAIPromptExecutionSettings actualSettings = new()
        {
            Temperature = 0.7,
            TopP = 0.7,
            FrequencyPenalty = 0.7,
            PresencePenalty = 0.7,
            StopSequences = new string[] { "foo", "bar" },
            ChatSystemPrompt = "chat system prompt",
            MaxTokens = 128,
            Logprobs = true,
            TopLogprobs = 5,
            TokenSelectionBiases = new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } },
            Seed = 123456,
            Store = true,
            Metadata = new Dictionary<string, string>() { { "foo", "bar" } },
            SetNewMaxCompletionTokensEnabled = true,
        };

        // Act
        AzureOpenAIPromptExecutionSettings executionSettings = AzureOpenAIPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.Equal(actualSettings, executionSettings);
        Assert.Equal(actualSettings, executionSettings);
        Assert.Equal(actualSettings.MaxTokens, executionSettings.MaxTokens);
        Assert.Equal(actualSettings.Logprobs, executionSettings.Logprobs);
        Assert.Equal(actualSettings.TopLogprobs, executionSettings.TopLogprobs);
        Assert.Equal(actualSettings.TokenSelectionBiases, executionSettings.TokenSelectionBiases);
        Assert.Equal(actualSettings.Seed, executionSettings.Seed);
        Assert.Equal(actualSettings.Store, executionSettings.Store);
        Assert.Equal(actualSettings.Metadata, executionSettings.Metadata);
        Assert.Equal(actualSettings.SetNewMaxCompletionTokensEnabled, executionSettings.SetNewMaxCompletionTokensEnabled);
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
        AzureOpenAIPromptExecutionSettings executionSettings = AzureOpenAIPromptExecutionSettings.FromExecutionSettings(actualSettings, null);

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
                { "stop_sequences", new [] { "foo", "bar" } },
                { "chat_system_prompt", "chat system prompt" },
                { "max_tokens", 128 },
                { "token_selection_biases", new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } } },
                { "seed", 123456 },
                { "logprobs", true },
                { "top_logprobs", 5 },
                { "store", true },
                { "metadata", new Dictionary<string, string>() { { "foo", "bar" } } }
            }
        };

        // Act
        AzureOpenAIPromptExecutionSettings executionSettings = AzureOpenAIPromptExecutionSettings.FromExecutionSettings(actualSettings, null);

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
                { "stop_sequences", new [] { "foo", "bar" } },
                { "chat_system_prompt", "chat system prompt" },
                { "max_tokens", "128" },
                { "token_selection_biases", new Dictionary<string, string>() { { "1", "2" }, { "3", "4" } } },
                { "seed", 123456 },
                { "logprobs", true },
                { "top_logprobs", 5 },
                { "store", true },
                { "metadata", new Dictionary<string, string>() { { "foo", "bar" } } }
            }
        };

        // Act
        AzureOpenAIPromptExecutionSettings executionSettings = AzureOpenAIPromptExecutionSettings.FromExecutionSettings(actualSettings, null);

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
              "stop_sequences": [ "foo", "bar" ],
              "chat_system_prompt": "chat system prompt",
              "token_selection_biases": { "1": 2, "3": 4 },
              "max_tokens": 128,
              "seed": 123456,
              "logprobs": true,
              "top_logprobs": 5,
              "store": true,
              "metadata": { "foo": "bar" }
            }
            """;
        var actualSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(json);

        // Act
        AzureOpenAIPromptExecutionSettings executionSettings = AzureOpenAIPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        AssertExecutionSettings(executionSettings);
    }

    [Theory]
    [InlineData("", "")]
    [InlineData("System prompt", "System prompt")]
    public void ItUsesCorrectChatSystemPrompt(string chatSystemPrompt, string expectedChatSystemPrompt)
    {
        // Arrange & Act
        var settings = new AzureOpenAIPromptExecutionSettings { ChatSystemPrompt = chatSystemPrompt };

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
        var executionSettings = JsonSerializer.Deserialize<AzureOpenAIPromptExecutionSettings>(configPayload);

        // Act
        var clone = executionSettings!.Clone();

        // Assert
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
            "store": true,
            "metadata": { "foo": "bar" }
        }
        """;
        var executionSettings = JsonSerializer.Deserialize<AzureOpenAIPromptExecutionSettings>(configPayload);

        // Act
        executionSettings!.Freeze();

        // Assert
        Assert.True(executionSettings.IsFrozen);
        Assert.Throws<InvalidOperationException>(() => executionSettings.ModelId = "gpt-4");
        Assert.Throws<InvalidOperationException>(() => executionSettings.Temperature = 1);
        Assert.Throws<InvalidOperationException>(() => executionSettings.TopP = 1);
        Assert.Throws<NotSupportedException>(() => executionSettings.StopSequences?.Add("STOP"));
        Assert.Throws<NotSupportedException>(() => executionSettings.TokenSelectionBiases?.Add(5, 6));
        Assert.Throws<InvalidOperationException>(() => executionSettings.Store = false);
        Assert.Throws<NotSupportedException>(() => executionSettings.Metadata?.Add("bar", "foo"));
        Assert.Throws<InvalidOperationException>(() => executionSettings.SetNewMaxCompletionTokensEnabled = true);
        Assert.Throws<InvalidOperationException>(() => executionSettings.UserSecurityContext = null);

        executionSettings!.Freeze(); // idempotent
        Assert.True(executionSettings.IsFrozen);
    }

    [Fact]
    public void FromExecutionSettingsWithDataDoesNotIncludeEmptyStopSequences()
    {
        // Arrange
        var executionSettings = new AzureOpenAIPromptExecutionSettings { StopSequences = [] };

        // Act
        var executionSettingsWithData = AzureOpenAIPromptExecutionSettings.FromExecutionSettingsWithData(executionSettings);

        // Assert
        Assert.Null(executionSettingsWithData.StopSequences);
    }

    [Fact]
    public void ItCanCreateAzureOpenAIPromptExecutionSettingsFromOpenAIPromptExecutionSettings()
    {
        // Arrange
        OpenAIPromptExecutionSettings originalSettings = new()
        {
            Temperature = 0.7,
            TopP = 0.7,
            FrequencyPenalty = 0.7,
            PresencePenalty = 0.7,
            StopSequences = new string[] { "foo", "bar" },
            ChatSystemPrompt = "chat system prompt",
            TokenSelectionBiases = new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } },
            MaxTokens = 128,
            Logprobs = true,
            Seed = 123456,
            TopLogprobs = 5,
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions,
            Store = true,
            Metadata = new Dictionary<string, string>() { { "foo", "bar" } }
        };

        // Act
        AzureOpenAIPromptExecutionSettings executionSettings = AzureOpenAIPromptExecutionSettings.FromExecutionSettings(originalSettings);

        // Assert
        AssertExecutionSettings(executionSettings);
    }

    [Fact]
    public void ItRestoresOriginalFunctionChoiceBehavior()
    {
        // Arrange
        var functionChoiceBehavior = FunctionChoiceBehavior.Auto();

        var originalExecutionSettings = new PromptExecutionSettings();
        originalExecutionSettings.FunctionChoiceBehavior = functionChoiceBehavior;

        // Act
        var result = AzureOpenAIPromptExecutionSettings.FromExecutionSettings(originalExecutionSettings);

        // Assert
        Assert.Equal(functionChoiceBehavior, result.FunctionChoiceBehavior);
    }

    private static void AssertExecutionSettings(AzureOpenAIPromptExecutionSettings executionSettings)
    {
        Assert.NotNull(executionSettings);
        Assert.Equal(0.7, executionSettings.Temperature);
        Assert.Equal(0.7, executionSettings.TopP);
        Assert.Equal(0.7, executionSettings.FrequencyPenalty);
        Assert.Equal(0.7, executionSettings.PresencePenalty);
        Assert.Equal(new string[] { "foo", "bar" }, executionSettings.StopSequences);
        Assert.Equal("chat system prompt", executionSettings.ChatSystemPrompt);
        Assert.Equal(new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } }, executionSettings.TokenSelectionBiases);
        Assert.Equal(128, executionSettings.MaxTokens);
        Assert.Equal(123456, executionSettings.Seed);
        Assert.Equal(true, executionSettings.Logprobs);
        Assert.Equal(5, executionSettings.TopLogprobs);
        Assert.Equal(true, executionSettings.Store);
        Assert.Equal(new Dictionary<string, string>() { { "foo", "bar" } }, executionSettings.Metadata);
    }
}
