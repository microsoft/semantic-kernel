// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests;

public sealed class AnthropicPromptExecutionSettingsTests
{
    [Fact]
    public void ItCreatesExecutionSettingsWithCorrectDefaults()
    {
        // Arrange
        // Act
        AnthropicPromptExecutionSettings executionSettings = AnthropicPromptExecutionSettings.FromExecutionSettings(null);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Null(executionSettings.Temperature);
        Assert.Null(executionSettings.TopP);
        Assert.Null(executionSettings.TopK);
        Assert.Null(executionSettings.StopSequences);
        Assert.Equal(AnthropicPromptExecutionSettings.DefaultTextMaxTokens, executionSettings.MaxTokens);
    }

    [Fact]
    public void ItUsesExistingExecutionSettings()
    {
        // Arrange
        AnthropicPromptExecutionSettings actualSettings = new()
        {
            Temperature = 0.7,
            TopP = 0.7f,
            TopK = 20,
            StopSequences = new[] { "foo", "bar" },
            MaxTokens = 128,
        };

        // Act
        AnthropicPromptExecutionSettings executionSettings = AnthropicPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(actualSettings, executionSettings);
    }

    [Fact]
    public void ItCreatesExecutionSettingsFromExtensionDataSnakeCase()
    {
        // Arrange
        PromptExecutionSettings actualSettings = new()
        {
            ExtensionData = new Dictionary<string, object>
            {
                { "max_tokens", 1000 },
                { "temperature", 0 }
            }
        };

        // Act
        AnthropicPromptExecutionSettings executionSettings = AnthropicPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(1000, executionSettings.MaxTokens);
        Assert.Equal(0, executionSettings.Temperature);
    }

    [Fact]
    public void ItCreatesExecutionSettingsFromJsonSnakeCase()
    {
        // Arrange
        string json = """
                      {
                        "temperature": 0.7,
                        "top_p": 0.7,
                        "top_k": 25,
                        "stop_sequences": [ "foo", "bar" ],
                        "max_tokens": 128
                      }
                      """;
        var actualSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(json);

        // Act
        AnthropicPromptExecutionSettings executionSettings = AnthropicPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(0.7, executionSettings.Temperature);
        Assert.Equal(0.7f, executionSettings.TopP);
        Assert.Equal(25, executionSettings.TopK);
        Assert.Equal(new[] { "foo", "bar" }, executionSettings.StopSequences);
        Assert.Equal(128, executionSettings.MaxTokens);
    }

    [Fact]
    public void PromptExecutionSettingsCloneWorksAsExpected()
    {
        // Arrange
        string json = """
                      {
                        "model_id": "claude-pro",
                        "temperature": 0.7,
                        "top_p": 0.7,
                        "top_k": 25,
                        "stop_sequences": [ "foo", "bar" ],
                        "max_tokens": 128
                      }
                      """;
        var executionSettings = JsonSerializer.Deserialize<AnthropicPromptExecutionSettings>(json);

        // Act
        var clone = executionSettings!.Clone() as AnthropicPromptExecutionSettings;

        // Assert
        Assert.NotNull(clone);
        Assert.Equal(executionSettings.ModelId, clone.ModelId);
        Assert.Equal(executionSettings.Temperature, clone.Temperature);
        Assert.Equivalent(executionSettings.ExtensionData, clone.ExtensionData);
        Assert.Equivalent(executionSettings.StopSequences, clone.StopSequences);
    }

    [Fact]
    public void PromptExecutionSettingsFreezeWorksAsExpected()
    {
        // Arrange
        string json = """
                      {
                        "model_id": "claude-pro",
                        "temperature": 0.7,
                        "top_p": 0.7,
                        "top_k": 25,
                        "stop_sequences": [ "foo", "bar" ],
                        "max_tokens": 128
                      }
                      """;
        var executionSettings = JsonSerializer.Deserialize<AnthropicPromptExecutionSettings>(json);

        // Act
        executionSettings!.Freeze();

        // Assert
        Assert.True(executionSettings.IsFrozen);
        Assert.Throws<InvalidOperationException>(() => executionSettings.ModelId = "claude");
        Assert.Throws<InvalidOperationException>(() => executionSettings.Temperature = 0.5);
        Assert.Throws<NotSupportedException>(() => executionSettings.StopSequences!.Add("baz"));
    }
}
