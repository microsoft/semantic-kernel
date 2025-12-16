// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests.Settings;

/// <summary>
/// Unit tests for <see cref="AnthropicPromptExecutionSettings"/>.
/// </summary>
public sealed class AnthropicPromptExecutionSettingsTests
{
    #region Default Values Tests

    [Fact]
    public void ItCreatesAnthropicExecutionSettingsWithCorrectDefaults()
    {
        // Arrange & Act
        AnthropicPromptExecutionSettings executionSettings = AnthropicPromptExecutionSettings.FromExecutionSettings(null);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Null(executionSettings.Temperature);
        Assert.Null(executionSettings.TopP);
        Assert.Null(executionSettings.TopK);
        Assert.Null(executionSettings.MaxTokens);
        Assert.Null(executionSettings.StopSequences);
        Assert.Null(executionSettings.FunctionChoiceBehavior);
    }

    [Fact]
    public void ItCreatesNewInstanceWithDefaultConstructor()
    {
        // Arrange & Act
        var settings = new AnthropicPromptExecutionSettings();

        // Assert
        Assert.NotNull(settings);
        Assert.Null(settings.Temperature);
        Assert.Null(settings.TopP);
        Assert.Null(settings.TopK);
        Assert.Null(settings.MaxTokens);
        Assert.Null(settings.StopSequences);
        Assert.Null(settings.ModelId);
        Assert.Null(settings.ServiceId);
        Assert.False(settings.IsFrozen);
    }

    #endregion

    #region FromExecutionSettings Tests

    [Fact]
    public void ItUsesExistingAnthropicExecutionSettings()
    {
        // Arrange
        AnthropicPromptExecutionSettings actualSettings = new()
        {
            Temperature = 0.7,
            TopP = 0.9,
            TopK = 40,
            MaxTokens = 1024,
            StopSequences = ["stop1", "stop2"]
        };

        // Act
        AnthropicPromptExecutionSettings executionSettings = AnthropicPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Same(actualSettings, executionSettings);
    }

    [Fact]
    public void ItCreatesAnthropicExecutionSettingsFromExtensionDataSnakeCase()
    {
        // Arrange
        PromptExecutionSettings actualSettings = new()
        {
            ExtensionData = new Dictionary<string, object>
            {
                { "max_tokens", 2000 },
                { "temperature", 0.5 },
                { "top_p", 0.8 },
                { "top_k", 50 }
            }
        };

        // Act
        AnthropicPromptExecutionSettings executionSettings = AnthropicPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(2000, executionSettings.MaxTokens);
        Assert.Equal(0.5, executionSettings.Temperature);
        Assert.Equal(0.8, executionSettings.TopP);
        Assert.Equal(50, executionSettings.TopK);
    }

    [Fact]
    public void ItCreatesAnthropicExecutionSettingsFromJsonSnakeCase()
    {
        // Arrange
        string json = """
                      {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "max_tokens": 1024,
                        "stop_sequences": ["stop1", "stop2"]
                      }
                      """;
        var actualSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(json);

        // Act
        AnthropicPromptExecutionSettings executionSettings = AnthropicPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(0.7, executionSettings.Temperature);
        Assert.Equal(0.9, executionSettings.TopP);
        Assert.Equal(40, executionSettings.TopK);
        Assert.Equal(1024, executionSettings.MaxTokens);
        Assert.Equal(["stop1", "stop2"], executionSettings.StopSequences);
    }

    [Fact]
    public void ItPreservesFunctionChoiceBehaviorFromBaseSettings()
    {
        // Arrange
        var functionChoiceBehavior = FunctionChoiceBehavior.Auto();
        PromptExecutionSettings baseSettings = new()
        {
            FunctionChoiceBehavior = functionChoiceBehavior
        };

        // Act
        AnthropicPromptExecutionSettings executionSettings = AnthropicPromptExecutionSettings.FromExecutionSettings(baseSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Same(functionChoiceBehavior, executionSettings.FunctionChoiceBehavior);
    }

    [Fact]
    public void ItPreservesModelIdAndServiceIdFromBaseSettings()
    {
        // Arrange
        PromptExecutionSettings baseSettings = new()
        {
            ModelId = "claude-sonnet-4-20250514",
            ServiceId = "my-anthropic-service"
        };

        // Act
        AnthropicPromptExecutionSettings executionSettings = AnthropicPromptExecutionSettings.FromExecutionSettings(baseSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal("claude-sonnet-4-20250514", executionSettings.ModelId);
        Assert.Equal("my-anthropic-service", executionSettings.ServiceId);
    }

    [Fact]
    public void ItHandlesEmptyExtensionData()
    {
        // Arrange
        PromptExecutionSettings baseSettings = new()
        {
            ExtensionData = new Dictionary<string, object>()
        };

        // Act
        AnthropicPromptExecutionSettings executionSettings = AnthropicPromptExecutionSettings.FromExecutionSettings(baseSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Null(executionSettings.Temperature);
        Assert.Null(executionSettings.MaxTokens);
    }

    #endregion

    #region JSON Deserialization Tests

    [Fact]
    public void ItDeserializesFromJsonWithAllProperties()
    {
        // Arrange
        string json = """
                      {
                        "model_id": "claude-sonnet-4-20250514",
                        "service_id": "my-service",
                        "temperature": 0.8,
                        "top_p": 0.95,
                        "top_k": 50,
                        "max_tokens": 2048,
                        "stop_sequences": ["END", "STOP", "DONE"]
                      }
                      """;

        // Act
        var settings = JsonSerializer.Deserialize<AnthropicPromptExecutionSettings>(json);

        // Assert
        Assert.NotNull(settings);
        Assert.Equal("claude-sonnet-4-20250514", settings.ModelId);
        Assert.Equal("my-service", settings.ServiceId);
        Assert.Equal(0.8, settings.Temperature);
        Assert.Equal(0.95, settings.TopP);
        Assert.Equal(50, settings.TopK);
        Assert.Equal(2048, settings.MaxTokens);
        Assert.Equal(3, settings.StopSequences!.Count);
        Assert.Contains("END", settings.StopSequences);
        Assert.Contains("STOP", settings.StopSequences);
        Assert.Contains("DONE", settings.StopSequences);
    }

    [Fact]
    public void ItDeserializesFromJsonWithPartialProperties()
    {
        // Arrange
        string json = """
                      {
                        "temperature": 0.5,
                        "max_tokens": 1000
                      }
                      """;

        // Act
        var settings = JsonSerializer.Deserialize<AnthropicPromptExecutionSettings>(json);

        // Assert
        Assert.NotNull(settings);
        Assert.Equal(0.5, settings.Temperature);
        Assert.Equal(1000, settings.MaxTokens);
        Assert.Null(settings.TopP);
        Assert.Null(settings.TopK);
        Assert.Null(settings.StopSequences);
    }

    [Fact]
    public void ItDeserializesFromJsonWithNumbersAsStrings()
    {
        // Arrange - JsonNumberHandling.AllowReadingFromString should handle this
        string json = """
                      {
                        "temperature": "0.7",
                        "max_tokens": "1024",
                        "top_k": "40"
                      }
                      """;

        // Act
        var settings = JsonSerializer.Deserialize<AnthropicPromptExecutionSettings>(json);

        // Assert
        Assert.NotNull(settings);
        Assert.Equal(0.7, settings.Temperature);
        Assert.Equal(1024, settings.MaxTokens);
        Assert.Equal(40, settings.TopK);
    }

    [Fact]
    public void ItDeserializesEmptyStopSequencesArray()
    {
        // Arrange
        string json = """
                      {
                        "stop_sequences": []
                      }
                      """;

        // Act
        var settings = JsonSerializer.Deserialize<AnthropicPromptExecutionSettings>(json);

        // Assert
        Assert.NotNull(settings);
        Assert.NotNull(settings.StopSequences);
        Assert.Empty(settings.StopSequences);
    }

    #endregion

    #region Clone Tests

    [Fact]
    public void PromptExecutionSettingsCloneWorksAsExpected()
    {
        // Arrange
        string json = """
                      {
                        "model_id": "claude-sonnet-4-20250514",
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "max_tokens": 1024,
                        "stop_sequences": ["stop1", "stop2"]
                      }
                      """;
        var executionSettings = JsonSerializer.Deserialize<AnthropicPromptExecutionSettings>(json);

        // Act
        var clone = executionSettings!.Clone() as AnthropicPromptExecutionSettings;

        // Assert
        Assert.NotNull(clone);
        Assert.NotSame(executionSettings, clone);
        Assert.Equal(executionSettings.ModelId, clone.ModelId);
        Assert.Equal(executionSettings.Temperature, clone.Temperature);
        Assert.Equal(executionSettings.TopP, clone.TopP);
        Assert.Equal(executionSettings.TopK, clone.TopK);
        Assert.Equal(executionSettings.MaxTokens, clone.MaxTokens);
        Assert.Equivalent(executionSettings.StopSequences, clone.StopSequences);
    }

    [Fact]
    public void CloneCreatesDeepCopyOfStopSequences()
    {
        // Arrange
        var settings = new AnthropicPromptExecutionSettings
        {
            StopSequences = ["stop1", "stop2"]
        };

        // Act
        var clone = settings.Clone() as AnthropicPromptExecutionSettings;
        clone!.StopSequences!.Add("stop3");

        // Assert
        Assert.Equal(2, settings.StopSequences.Count);
        Assert.Equal(3, clone.StopSequences.Count);
    }

    [Fact]
    public void CloneCreatesDeepCopyOfExtensionData()
    {
        // Arrange
        var settings = new AnthropicPromptExecutionSettings
        {
            ExtensionData = new Dictionary<string, object>
            {
                { "custom_key", "custom_value" }
            }
        };

        // Act
        var clone = settings.Clone() as AnthropicPromptExecutionSettings;
        clone!.ExtensionData!["new_key"] = "new_value";

        // Assert
        Assert.Single(settings.ExtensionData);
        Assert.Equal(2, clone.ExtensionData.Count);
    }

    [Fact]
    public void ClonePreservesFunctionChoiceBehavior()
    {
        // Arrange
        var functionChoiceBehavior = FunctionChoiceBehavior.Required();
        var settings = new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = functionChoiceBehavior
        };

        // Act
        var clone = settings.Clone() as AnthropicPromptExecutionSettings;

        // Assert
        Assert.Same(functionChoiceBehavior, clone!.FunctionChoiceBehavior);
    }

    [Fact]
    public void CloneOfFrozenSettingsIsNotFrozen()
    {
        // Arrange
        var settings = new AnthropicPromptExecutionSettings
        {
            Temperature = 0.7
        };
        settings.Freeze();

        // Act
        var clone = settings.Clone() as AnthropicPromptExecutionSettings;

        // Assert
        Assert.True(settings.IsFrozen);
        Assert.False(clone!.IsFrozen);
        clone.Temperature = 0.5; // Should not throw
        Assert.Equal(0.5, clone.Temperature);
    }

    #endregion

    #region Freeze Tests

    [Fact]
    public void PromptExecutionSettingsFreezeWorksAsExpected()
    {
        // Arrange
        string json = """
                      {
                        "model_id": "claude-sonnet-4-20250514",
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "max_tokens": 1024,
                        "stop_sequences": ["stop1", "stop2"]
                      }
                      """;
        var executionSettings = JsonSerializer.Deserialize<AnthropicPromptExecutionSettings>(json);

        // Act
        executionSettings!.Freeze();

        // Assert
        Assert.True(executionSettings.IsFrozen);
        Assert.Throws<InvalidOperationException>(() => executionSettings.ModelId = "claude-opus-4-20250514");
        Assert.Throws<InvalidOperationException>(() => executionSettings.Temperature = 0.5);
        Assert.Throws<InvalidOperationException>(() => executionSettings.TopP = 0.5);
        Assert.Throws<InvalidOperationException>(() => executionSettings.TopK = 20);
        Assert.Throws<InvalidOperationException>(() => executionSettings.MaxTokens = 2048);
        Assert.Throws<NotSupportedException>(() => executionSettings.StopSequences!.Add("stop3"));
    }

    [Fact]
    public void FreezeIsIdempotent()
    {
        // Arrange
        var settings = new AnthropicPromptExecutionSettings
        {
            Temperature = 0.7
        };

        // Act
        settings.Freeze();
        settings.Freeze(); // Should not throw

        // Assert
        Assert.True(settings.IsFrozen);
    }

    [Fact]
    public void FreezePreventsFunctionChoiceBehaviorModification()
    {
        // Arrange
        var settings = new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };
        settings.Freeze();

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => settings.FunctionChoiceBehavior = FunctionChoiceBehavior.Required());
    }

    [Fact]
    public void FreezeWithNullStopSequencesDoesNotThrow()
    {
        // Arrange
        var settings = new AnthropicPromptExecutionSettings
        {
            Temperature = 0.7,
            StopSequences = null
        };

        // Act
        settings.Freeze();

        // Assert
        Assert.True(settings.IsFrozen);
        Assert.Null(settings.StopSequences);
    }

    #endregion

    #region Property Setter Tests

    [Fact]
    public void SettingTemperatureWorks()
    {
        // Arrange
        var settings = new AnthropicPromptExecutionSettings();

        // Act
        settings.Temperature = 0.5;

        // Assert
        Assert.Equal(0.5, settings.Temperature);
    }

    [Fact]
    public void SettingTopPWorks()
    {
        // Arrange
        var settings = new AnthropicPromptExecutionSettings();

        // Act
        settings.TopP = 0.9;

        // Assert
        Assert.Equal(0.9, settings.TopP);
    }

    [Fact]
    public void SettingTopKWorks()
    {
        // Arrange
        var settings = new AnthropicPromptExecutionSettings();

        // Act
        settings.TopK = 50;

        // Assert
        Assert.Equal(50, settings.TopK);
    }

    [Fact]
    public void SettingMaxTokensWorks()
    {
        // Arrange
        var settings = new AnthropicPromptExecutionSettings();

        // Act
        settings.MaxTokens = 4096;

        // Assert
        Assert.Equal(4096, settings.MaxTokens);
    }

    [Fact]
    public void SettingStopSequencesWorks()
    {
        // Arrange
        var settings = new AnthropicPromptExecutionSettings();

        // Act
        settings.StopSequences = ["END", "STOP"];

        // Assert
        Assert.Equal(2, settings.StopSequences!.Count);
        Assert.Contains("END", settings.StopSequences);
        Assert.Contains("STOP", settings.StopSequences);
    }

    #endregion
}
