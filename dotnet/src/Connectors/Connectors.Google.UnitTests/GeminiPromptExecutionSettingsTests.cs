// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Google;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests;

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
        Assert.Null(executionSettings.AudioTimestamp);
        Assert.Null(executionSettings.ResponseMimeType);
        Assert.Null(executionSettings.ResponseSchema);
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
            AudioTimestamp = true,
            ResponseMimeType = "application/json",
            StopSequences = ["foo", "bar"],
            MaxTokens = 128,
            SafetySettings =
            [
                new(GeminiSafetyCategory.Harassment, GeminiSafetyThreshold.BlockOnlyHigh)
            ]
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
            ExtensionData = new Dictionary<string, object>
            {
                { "max_tokens", 1000 },
                { "temperature", 0 },
                { "audio_timestamp", true },
                { "response_mimetype", "application/json" },
                { "response_schema", JsonSerializer.Serialize(new { }) }
            }
        };

        // Act
        GeminiPromptExecutionSettings executionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(1000, executionSettings.MaxTokens);
        Assert.Equal(0, executionSettings.Temperature);
        Assert.Equal("application/json", executionSettings.ResponseMimeType);
        Assert.NotNull(executionSettings.ResponseSchema);
        Assert.Equal(typeof(JsonElement), executionSettings.ResponseSchema.GetType());
        Assert.True(executionSettings.AudioTimestamp);
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
                          "audio_timestamp": true,
                          "safety_settings": [
                            {
                              "category": "{{category.Label}}",
                              "threshold": "{{threshold.Label}}"
                            }
                          ],
                          "thinking_config": {
                            "thinking_budget": 1000
                          }
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
        Assert.Equal(["foo", "bar"], executionSettings.StopSequences);
        Assert.Equal(128, executionSettings.MaxTokens);
        Assert.True(executionSettings.AudioTimestamp);
        Assert.Single(executionSettings.SafetySettings!, settings =>
            settings.Category.Equals(category) &&
            settings.Threshold.Equals(threshold));

        Assert.Equal(1000, executionSettings.ThinkingConfig?.ThinkingBudget);
    }

    [Fact]
    public void PromptExecutionSettingsCloneWorksAsExpected()
    {
        // Arrange
        var category = GeminiSafetyCategory.Harassment;
        var threshold = GeminiSafetyThreshold.BlockOnlyHigh;
        string json = $$"""
                        {
                          "model_id": "gemini-pro",
                          "temperature": 0.7,
                          "top_p": 0.7,
                          "top_k": 25,
                          "candidate_count": 2,
                          "audio_timestamp": true,
                          "stop_sequences": [ "foo", "bar" ],
                          "max_tokens": 128,
                          "safety_settings": [
                            {
                              "category": "{{category.Label}}",
                              "threshold": "{{threshold.Label}}"
                            }
                          ],
                          "thinking_config": {
                            "thinking_budget": 1000
                          }
                        }
                        """;
        var executionSettings = JsonSerializer.Deserialize<GeminiPromptExecutionSettings>(json);

        // Act
        var clone = executionSettings!.Clone() as GeminiPromptExecutionSettings;

        // Assert
        Assert.NotNull(clone);
        Assert.Equal(executionSettings.ModelId, clone.ModelId);
        Assert.Equal(executionSettings.Temperature, clone.Temperature);
        Assert.Equivalent(executionSettings.ExtensionData, clone.ExtensionData);
        Assert.Equivalent(executionSettings.StopSequences, clone.StopSequences);
        Assert.Equivalent(executionSettings.SafetySettings, clone.SafetySettings);
        Assert.Equal(executionSettings.AudioTimestamp, clone.AudioTimestamp);
        Assert.Equivalent(executionSettings.ThinkingConfig, clone.ThinkingConfig);
    }

    [Fact]
    public void PromptExecutionSettingsFreezeWorksAsExpected()
    {
        // Arrange
        var category = GeminiSafetyCategory.Harassment;
        var threshold = GeminiSafetyThreshold.BlockOnlyHigh;
        string json = $$"""
                        {
                          "model_id": "gemini-pro",
                          "temperature": 0.7,
                          "top_p": 0.7,
                          "top_k": 25,
                          "candidate_count": 2,
                          "audio_timestamp": true,
                          "stop_sequences": [ "foo", "bar" ],
                          "max_tokens": 128,
                          "safety_settings": [
                            {
                              "category": "{{category.Label}}",
                              "threshold": "{{threshold.Label}}"
                            }
                          ],
                          "thinking_config": {
                            "thinking_budget": 1000
                          }
                        }
                        """;
        var executionSettings = JsonSerializer.Deserialize<GeminiPromptExecutionSettings>(json);

        // Act
        executionSettings!.Freeze();

        // Assert
        Assert.True(executionSettings.IsFrozen);
        Assert.Throws<InvalidOperationException>(() => executionSettings.ModelId = "gemini-ultra");
        Assert.Throws<InvalidOperationException>(() => executionSettings.CandidateCount = 5);
        Assert.Throws<InvalidOperationException>(() => executionSettings.Temperature = 0.5);
        Assert.Throws<InvalidOperationException>(() => executionSettings.AudioTimestamp = false);
        Assert.Throws<NotSupportedException>(() => executionSettings.StopSequences!.Add("baz"));
        Assert.Throws<NotSupportedException>(() => executionSettings.SafetySettings!.Add(new GeminiSafetySetting(GeminiSafetyCategory.Toxicity, GeminiSafetyThreshold.Unspecified)));
        Assert.Throws<InvalidOperationException>(() => executionSettings.ThinkingConfig = new GeminiThinkingConfig { ThinkingBudget = 1 });
    }
}
