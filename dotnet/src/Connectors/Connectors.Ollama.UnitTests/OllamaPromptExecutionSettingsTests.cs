// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Ollama;
using Xunit;

namespace SemanticKernel.Connectors.Ollama.UnitTests;

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
        Assert.Equal(OllamaPromptExecutionSettings.DefaultTextMaxTokens, ollamaExecutionSettings.MaxTokens);
    }

    [Fact]
    public void FromExecutionSettingsWhenSerializedHasPropertiesShouldPopulateSpecialized()
    {
        string jsonSettings = """
                                {
                                    "max_tokens": 100
                                }
                                """;

        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(jsonSettings);
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(executionSettings);

        Assert.Equal(100, ollamaExecutionSettings.MaxTokens);
    }
}
