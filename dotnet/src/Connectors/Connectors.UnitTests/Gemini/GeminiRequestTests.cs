#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Collections.Generic;
using Microsoft.SemanticKernel.Connectors.Gemini;
using Microsoft.SemanticKernel.Connectors.Gemini.Settings;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Gemini;

public class GeminiRequestTests
{
    [Fact]
    public void FromPromptExecutionSettingsReturnsGeminiRequestWithConfiguration()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            Temperature = 1.5,
            MaxTokens = 10,
            TopP = 0.9,
        };

        // Act
        var request = GeminiRequest.FromPromptExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.Configuration);
        Assert.Equal(executionSettings.Temperature, request.Configuration.Temperature);
        Assert.Equal(executionSettings.MaxTokens, request.Configuration.MaxOutputTokens);
        Assert.Equal(executionSettings.TopP, request.Configuration.TopP);
    }

    [Fact]
    public void FromPromptExecutionSettingsReturnsGeminiRequestWithSafetySettings()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings
        {
            SafetySettings = new List<GeminiSafetySetting>
            {
                new("test-cat", "test-th")
            }
        };

        // Act
        var request = GeminiRequest.FromPromptExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.NotNull(request.SafetySettings);
        Assert.Equal(executionSettings.SafetySettings[0].Category, request.SafetySettings[0].Category);
        Assert.Equal(executionSettings.SafetySettings[0].Threshold, request.SafetySettings[0].Threshold);
    }

    [Fact]
    public void FromPromptExecutionSettingsReturnsGeminiRequestWithPrompt()
    {
        // Arrange
        var prompt = "prompt-example";
        var executionSettings = new GeminiPromptExecutionSettings();

        // Act
        var request = GeminiRequest.FromPromptExecutionSettings(prompt, executionSettings);

        // Assert
        Assert.Equal(prompt, request.Contents[0].Parts[0].Text);
    }
}
