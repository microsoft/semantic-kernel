// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Azure.AI.OpenAI.Chat;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Settings;

/// <summary>
/// Unit tests for <see cref="OpenAIPromptExecutionSettingsTests"/> class.
/// </summary>
public class OpenAIPromptExecutionSettingsTests
{
    [Fact]
    public void ItCanCreateOpenAIPromptExecutionSettingsFromAzureOpenAIPromptExecutionSettings()
    {
        // Arrange
        AzureOpenAIPromptExecutionSettings originalSettings = new()
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
#pragma warning disable AOAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
            AzureChatDataSource = new AzureSearchChatDataSource
            {
                Endpoint = new Uri("https://test-host"),
                Authentication = DataSourceAuthentication.FromApiKey("api-key"),
                IndexName = "index-name"
            }
#pragma warning restore AOAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        };

        // Act
        OpenAIPromptExecutionSettings executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(originalSettings);

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
        var result = OpenAIPromptExecutionSettings.FromExecutionSettings(originalExecutionSettings);

        // Assert
        Assert.Equal(functionChoiceBehavior, result.FunctionChoiceBehavior);
    }

    [Fact]
    public void ItCanCreateAzureOpenAIPromptExecutionSettingsFromPromptExecutionSettings()
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
                { "token_selection_biases", new Dictionary<int, int>() { { 1, 2 }, { 3, 4 } } },
                { "max_tokens", 128 },
                { "logprobs", true },
                { "seed", 123456 },
                { "top_logprobs", 5 },
            }
        };

        // Act
        AzureOpenAIPromptExecutionSettings executionSettings = AzureOpenAIPromptExecutionSettings.FromExecutionSettings(originalSettings);

        // Assert
        AssertExecutionSettings(executionSettings);
    }

    [Fact]
    public void ItCanCreateAzureOpenAIPromptExecutionSettingsFromJson()
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
                "token_selection_biases":
                    {
                      "1": "2",
                      "3": "4"
                    },
                "max_tokens": 128,
                "logprobs": true,
                "seed": 123456,
                "top_logprobs": 5
            }
            """;

        // Act
        var originalSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(json);
        OpenAIPromptExecutionSettings executionSettings = AzureOpenAIPromptExecutionSettings.FromExecutionSettings(originalSettings);

        // Assert
        AssertExecutionSettings(executionSettings);
    }

    [Fact]
    public void ItCanCreateAzureOpenAIPromptExecutionSettingsFromPromptExecutionSettingsWithIncorrectTypes()
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
                { "token_selection_biases", new Dictionary<string, object>() { { "1", "2" }, { "3", "4" } } },
                { "max_tokens", "128" },
                { "logprobs", "true" },
                { "seed", "123456" },
                { "top_logprobs", "5" },
            }
        };

        // Act
        AzureOpenAIPromptExecutionSettings executionSettings = AzureOpenAIPromptExecutionSettings.FromExecutionSettings(originalSettings);

        // Assert
        AssertExecutionSettings(executionSettings);
    }

    [Theory]
    [InlineData("")]
    [InlineData("123")]
    [InlineData("Foo")]
    [InlineData(1)]
    [InlineData(1.0)]
    public void ItCannotCreateAzureOpenAIPromptExecutionSettingsWithInvalidBoolValues(object value)
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
        Assert.Throws<ArgumentException>(() => AzureOpenAIPromptExecutionSettings.FromExecutionSettings(originalSettings));
    }

    #region private
    private static void AssertExecutionSettings(OpenAIPromptExecutionSettings executionSettings)
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
    }
    #endregion
}
