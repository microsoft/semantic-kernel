// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Ollama;
using Xunit;

namespace SemanticKernel.Connectors.Ollama.UnitTests;

/// <summary>
/// Unit tests of <see cref="OllamaPromptExecutionSettings"/>.
/// </summary>
public class OllamaPromptExecutionSettingsTests
{
    [Fact]
    public void FromExecutionSettingsWhenAlreadyOllamaShouldReturnSameAsync()
    {
        // Arrange
        var executionSettings = new OllamaPromptExecutionSettings();

        // Act
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);

        // Assert
        Assert.Same(executionSettings, ollamaExecutionSettings);
    }

    [Fact]
    public void FromExecutionSettingsWhenNullShouldReturnDefaultAsync()
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
                                    "stop": "stop me",
                                    "temperature": 0.5,
                                    "top_p": 0.9,
                                    "top_k": 100
                                }
                                """;

        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(jsonSettings);
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);

        Assert.Equal("stop me", ollamaExecutionSettings.Stop);
        Assert.Equal(0.5f, ollamaExecutionSettings.Temperature);
        Assert.Equal(0.9f, ollamaExecutionSettings.TopP!.Value, 0.1f);
        Assert.Equal(100, ollamaExecutionSettings.TopK);
    }
}
