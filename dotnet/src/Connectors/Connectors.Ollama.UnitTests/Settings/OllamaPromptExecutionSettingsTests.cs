// Copyright (c) Microsoft. All rights reserved.

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
    public void FromExecutionSettingsWhenAlreadyOllamaShouldReturnSame()
    {
        // Arrange
        var executionSettings = new OllamaPromptExecutionSettings();

        // Act
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);

        // Assert
        Assert.Same(executionSettings, ollamaExecutionSettings);
    }

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
                                    "top_k": 100,
                                    "num_predict": 50
                                }
                                """;

        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(jsonSettings);
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);

        Assert.Equal("stop me", ollamaExecutionSettings.Stop?.FirstOrDefault());
        Assert.Equal(0.5f, ollamaExecutionSettings.Temperature);
        Assert.Equal(0.9f, ollamaExecutionSettings.TopP!.Value, 0.1f);
        Assert.Equal(100, ollamaExecutionSettings.TopK);
        Assert.Equal(50, ollamaExecutionSettings.NumPredict);
    }

    [Fact]
    public void FromExecutionSettingsShouldRestoreFunctionChoiceBehavior()
    {
        // Arrange
        var functionChoiceBehavior = FunctionChoiceBehavior.Auto();

        var originalExecutionSettings = new PromptExecutionSettings
        {
            FunctionChoiceBehavior = functionChoiceBehavior
        };

        // Act
        var result = OllamaPromptExecutionSettings.FromExecutionSettings(originalExecutionSettings);

        // Assert
        Assert.Equal(functionChoiceBehavior, result.FunctionChoiceBehavior);
    }
}
