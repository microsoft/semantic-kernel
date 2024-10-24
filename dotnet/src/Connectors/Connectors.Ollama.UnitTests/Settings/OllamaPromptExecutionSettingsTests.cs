// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Ollama;
using Xunit;

namespace SemanticKernel.Connectors.Ollama.UnitTests.Settings;

/// <summary>
/// Unit tests of <see cref="OllamaPromptExecutionSettings"/>.
/// </summary>
public class OllamaPromptExecutionSettingsTests
{
    [Fact]
    public void FromExecutionSettingsWhenNullShouldReturnDefault()
    {
        // Arrange
        OllamaPromptExecutionSettings? executionSettings = null;

        // Act
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);

        // Assert
        Assert.Null(ollamaExecutionSettings.Stop);
        Assert.Null(ollamaExecutionSettings.Temperature);
        Assert.Null(ollamaExecutionSettings.TopP);
        Assert.Null(ollamaExecutionSettings.TopK);
    }

    [Fact]
    public void FromExecutionSettingsWhenSerializedHasPropertiesShouldPopulateSpecialized()
    {
        string jsonSettings = """
                                {
                                    "stop": ["stop me"],
                                    "temperature": 0.5,
                                    "top_p": 0.9,
                                    "top_k": 100
                                }
                                """;

        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(jsonSettings);
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);

        Assert.Equal("stop me", ollamaExecutionSettings.Stop?.FirstOrDefault());
        Assert.Equal(0.5f, ollamaExecutionSettings.Temperature);
        Assert.Equal(0.9f, ollamaExecutionSettings.TopP!.Value, 0.1f);
        Assert.Equal(100, ollamaExecutionSettings.TopK);
    }

    [Theory]
    [InlineData("auto")]
    [InlineData("none")]
    [InlineData("required")]
    public void SupportedAutoFunctionChoiceBehaviorWorksAsExpected(string choice)
    {
        // Arrange
        string configPayload = """
        {
            "model_id": "llama3.2",
            "service_id": "service-1",
            "function_choice_behavior": {
                "type": "<type>",
                "functions": ["p1.f1"]
            }
        }
        """;

        // Act & Assert
        var exception = Record.Exception(() =>
        {
            _ = JsonSerializer.Deserialize<OllamaPromptExecutionSettings>(configPayload.Replace("<type>", choice));
            _ = new OllamaPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        });

        Assert.Null(exception);
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
        var result = OllamaPromptExecutionSettings.FromExecutionSettings(originalExecutionSettings);

        // Assert
        Assert.Equal(functionChoiceBehavior, result.FunctionChoiceBehavior);
    }

    [Fact]
    public void PromptExecutionSettingsCloneWorksAsExpected()
    {
        // Arrange
        string configPayload = """
        {
            "stop": ["stop me"],
            "temperature": 0.5,
            "top_p": 0.9,
            "top_k": 100
        }
        """;
        var executionSettings = JsonSerializer.Deserialize<OllamaPromptExecutionSettings>(configPayload);

        // Act
        var settings = executionSettings!.Clone();

        // Assert
        Assert.NotNull(settings);
        Assert.IsType<OllamaPromptExecutionSettings>(settings);
        var clone = (OllamaPromptExecutionSettings)settings;
        Assert.Equal(executionSettings.ModelId, clone.ModelId);
        Assert.Equivalent(executionSettings.ExtensionData, clone.ExtensionData);
        Assert.Equal(executionSettings.Temperature, clone.Temperature);
        Assert.Equal(executionSettings.TopP!.Value, clone.TopP!.Value, 0.1f);
        Assert.Equal(executionSettings.TopK, clone.TopK);
    }

    [Fact]
    public void ItUsesExistingOllamaExecutionSettings()
    {
        // Arrange
        OllamaPromptExecutionSettings actualSettings = new()
        {
            Temperature = 0.7f,
            TopP = 0.7f,
            Stop = ["foo", "bar"],
        };

        // Act
        OllamaPromptExecutionSettings executionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(actualSettings, executionSettings);
    }

    [Fact]
    public void ItCreatesOpenAIExecutionSettingsWithCorrectDefaults()
    {
        // Arrange
        // Act
        OllamaPromptExecutionSettings executionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(null);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Null(executionSettings.Temperature);
        Assert.Null(executionSettings.TopP);
        Assert.Null(executionSettings.TopK);
        Assert.Null(executionSettings.Stop);
        Assert.Null(executionSettings.FunctionChoiceBehavior);
        Assert.Null(executionSettings.ExtensionData);
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
            "stop": [ "DONE" ]
        }
        """;
        var executionSettings = JsonSerializer.Deserialize<OllamaPromptExecutionSettings>(configPayload);

        // Act
        executionSettings!.Freeze();

        // Assert
        Assert.True(executionSettings.IsFrozen);
        Assert.Throws<InvalidOperationException>(() => executionSettings.ModelId = "gpt-4");
        Assert.Throws<InvalidOperationException>(() => executionSettings.Temperature = 1);
        Assert.Throws<InvalidOperationException>(() => executionSettings.TopP = 1);
        Assert.Throws<NotSupportedException>(() => executionSettings.Stop?.Add("STOP"));

        executionSettings!.Freeze(); // idempotent
        Assert.True(executionSettings.IsFrozen);
    }
}
