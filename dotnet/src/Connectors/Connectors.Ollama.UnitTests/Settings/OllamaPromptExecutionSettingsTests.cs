// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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

    [Fact]
    public void PromptExecutionSettingsCloneWorksAsExpected()
    {
        // Arrange
        string configPayload = """
        {
            "temperature": 0.5,
            "top_p": 0.9,
            "top_k": 100,
            "num_predict": 50,
            "stop": ["stop me"]
        }
        """;
        var executionSettings = JsonSerializer.Deserialize<OllamaPromptExecutionSettings>(configPayload);

        // Act
        var clone = executionSettings!.Clone();

        // Assert
        Assert.NotNull(clone);
        Assert.IsType<OllamaPromptExecutionSettings>(clone);
        var ollamaClone = (OllamaPromptExecutionSettings)clone;
        Assert.Equal(executionSettings.ModelId, ollamaClone.ModelId);
        Assert.Equal(executionSettings.Temperature, ollamaClone.Temperature);
        Assert.Equal(executionSettings.TopP, ollamaClone.TopP);
        Assert.Equal(executionSettings.TopK, ollamaClone.TopK);
        Assert.Equal(executionSettings.NumPredict, ollamaClone.NumPredict);
        Assert.Equal(executionSettings.Stop, ollamaClone.Stop);
        Assert.Equivalent(executionSettings.ExtensionData, ollamaClone.ExtensionData);
    }

    [Fact]
    public void ClonePreservesAllOllamaSpecificSettings()
    {
        // Arrange
        var testSettings = new OllamaPromptExecutionSettings
        {
            Temperature = 0.7f,
            TopP = 0.85f,
            TopK = 50,
            NumPredict = 100,
            Stop = ["END", "STOP"],
            ModelId = "llama2"
        };

        // Act
        var result = (OllamaPromptExecutionSettings)testSettings.Clone();

        // Assert
        Assert.NotNull(result);
        Assert.NotSame(testSettings, result);
        Assert.Equal(testSettings.Temperature, result.Temperature);
        Assert.Equal(testSettings.TopP, result.TopP);
        Assert.Equal(testSettings.TopK, result.TopK);
        Assert.Equal(testSettings.NumPredict, result.NumPredict);
        Assert.Equal(testSettings.ModelId, result.ModelId);
        Assert.NotSame(testSettings.Stop, result.Stop);
        Assert.Equal(testSettings.Stop, result.Stop);
    }

    [Fact]
    public void CloneReturnsOllamaPromptExecutionSettingsType()
    {
        // This test verifies the exact issue from the bug report
        // Arrange
        var testSettings = new OllamaPromptExecutionSettings
        {
            Temperature = 0.7f,
            TopP = 0.9f,
            ServiceId = "test-service"
        };

        // Act
        var cloned = testSettings.Clone();

        // Assert - Should not throw InvalidCastException
        var result = (OllamaPromptExecutionSettings)cloned;
        Assert.NotNull(result);
        Assert.Equal(testSettings.Temperature, result.Temperature);
        Assert.Equal(testSettings.TopP, result.TopP);
        Assert.Equal(testSettings.ServiceId, result.ServiceId);
    }

    [Fact]
    public void ClonePreservesServiceId()
    {
        // Arrange
        var testSettings = new OllamaPromptExecutionSettings
        {
            ServiceId = "my-ollama-service",
            ModelId = "llama2",
            Temperature = 0.8f
        };

        // Act
        var cloned = (OllamaPromptExecutionSettings)testSettings.Clone();

        // Assert
        Assert.Equal(testSettings.ServiceId, cloned.ServiceId);
        Assert.Equal(testSettings.ModelId, cloned.ModelId);
        Assert.Equal(testSettings.Temperature, cloned.Temperature);
    }

    [Fact]
    public void PromptExecutionSettingsFreezeWorksAsExpected()
    {
        // Arrange
        var executionSettings = new OllamaPromptExecutionSettings
        {
            Temperature = 0.5f,
            TopP = 0.9f,
            TopK = 100,
            NumPredict = 50,
            Stop = ["STOP"]
        };

        // Act
        executionSettings.Freeze();

        // Assert
        Assert.True(executionSettings.IsFrozen);
        Assert.Throws<InvalidOperationException>(() => executionSettings.Temperature = 1);
        Assert.Throws<InvalidOperationException>(() => executionSettings.TopP = 1);
        Assert.Throws<InvalidOperationException>(() => executionSettings.TopK = 1);
        Assert.Throws<InvalidOperationException>(() => executionSettings.NumPredict = 1);
        Assert.Throws<NotSupportedException>(() => executionSettings.Stop?.Add("END"));

        executionSettings.Freeze(); // idempotent
        Assert.True(executionSettings.IsFrozen);
    }
}
