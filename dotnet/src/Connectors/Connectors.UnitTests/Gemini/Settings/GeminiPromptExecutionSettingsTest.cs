#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Gemini.Settings;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Gemini.Settings;

public class GeminiPromptExecutionSettingsTest
{
    [Fact]
    public void ItCreatesGeminiExecutionSettingsWithCorrectDefaults()
    {
        // Arrange
        // Act
        GeminiPromptExecutionSettings executionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(null);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Null(executionSettings.Temperature);
        Assert.Null(executionSettings.TopP);
        Assert.Null(executionSettings.TopK);
        Assert.Null(executionSettings.StopSequences);
        Assert.Null(executionSettings.CandidateCount);
        Assert.Null(executionSettings.SafetySettings);
        Assert.Equal(GeminiPromptExecutionSettings.DefaultTextMaxTokens, executionSettings.MaxTokens);
    }

    [Fact]
    public void ItUsesExistingGeminiExecutionSettings()
    {
        // Arrange
        GeminiPromptExecutionSettings actualSettings = new()
        {
            Temperature = 0.7,
            TopP = 0.7,
            TopK = 20,
            CandidateCount = 3,
            StopSequences = new[] { "foo", "bar" },
            MaxTokens = 128,
            SafetySettings = new List<GeminiSafetySetting>() { new(category: "foo", threshold: "bar") }
        };

        // Act
        GeminiPromptExecutionSettings executionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(actualSettings, executionSettings);
    }

    [Fact]
    public void ItCreatesGeminiExecutionSettingsFromExtensionDataSnakeCase()
    {
        // Arrange
        PromptExecutionSettings actualSettings = new()
        {
            ExtensionData = new()
            {
                { "max_tokens", 1000 },
                { "temperature", 0 }
            }
        };

        // Act
        GeminiPromptExecutionSettings executionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(1000, executionSettings.MaxTokens);
        Assert.Equal(0, executionSettings.Temperature);
    }

    [Fact]
    public void ItCreatesGeminiExecutionSettingsFromJsonSnakeCase()
    {
        // Arrange
        string json = """
                      {
                        "temperature": 0.7,
                        "top_p": 0.7,
                        "top_k": 25,
                        "candidate_count": 2,
                        "stop_sequences": [ "foo", "bar" ],
                        "max_tokens": 128,
                        "safety_settings": [
                          {
                            "category": "foo",
                            "threshold": "bar"
                          }
                        ]
                      }
                      """;
        var actualSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(json);

        // Act
        GeminiPromptExecutionSettings executionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(0.7, executionSettings.Temperature);
        Assert.Equal(0.7, executionSettings.TopP);
        Assert.Equal(25, executionSettings.TopK);
        Assert.Equal(2, executionSettings.CandidateCount);
        Assert.Equal(new[] { "foo", "bar" }, executionSettings.StopSequences);
        Assert.Equal(128, executionSettings.MaxTokens);
        Assert.Single(executionSettings.SafetySettings!, settings =>
            settings.Category.Equals("foo", System.StringComparison.Ordinal) &&
            settings.Threshold.Equals("bar", System.StringComparison.Ordinal));
    }
}
