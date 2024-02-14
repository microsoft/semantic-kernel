// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Settings;

public sealed class GeminiPromptExecutionSettingsTests
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
            SafetySettings = new List<GeminiSafetySetting>()
            {
                new(GeminiSafetyCategory.Harassment, GeminiSafetyThreshold.BlockOnlyHigh)
            }
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
            ExtensionData = new Dictionary<string, object>()
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
        var category = GeminiSafetyCategory.Harassment;
        var threshold = GeminiSafetyThreshold.BlockOnlyHigh;
        string json = $$"""
                        {
                          "temperature": 0.7,
                          "top_p": 0.7,
                          "top_k": 25,
                          "candidate_count": 2,
                          "stop_sequences": [ "foo", "bar" ],
                          "max_tokens": 128,
                          "safety_settings": [
                            {
                              "category": "{{category.Label}}",
                              "threshold": "{{threshold.Label}}"
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
            settings.Category.Equals(category) &&
            settings.Threshold.Equals(threshold));
    }
}
