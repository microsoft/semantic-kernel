// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Xunit;

namespace SemanticKernel.Connectors.HuggingFace.UnitTests.Core;

public class HuggingFacePromptExecutionSettingsTests
{
    [Fact]
    public void FromExecutionSettingsWhenAlreadyHuggingFaceShouldReturnSame()
    {
        // Arrange
        var executionSettings = new HuggingFacePromptExecutionSettings();

        // Act
        var huggingFaceExecutionSettings = HuggingFacePromptExecutionSettings.FromExecutionSettings(executionSettings);

        // Assert
        Assert.Same(executionSettings, huggingFaceExecutionSettings);
    }

    [Fact]
    public void FromExecutionSettingsWhenNullShouldReturnDefault()
    {
        // Arrange
        HuggingFacePromptExecutionSettings? executionSettings = null;

        // Act
        var huggingFaceExecutionSettings = HuggingFacePromptExecutionSettings.FromExecutionSettings(executionSettings);

        // Assert
        Assert.NotNull(huggingFaceExecutionSettings);
    }

    [Fact]
    public void FromExecutionSettingsWhenSerializedHasPropertiesShouldPopulateSpecialized()
    {
        string jsonSettings = """
                                {
                                    "temperature": 0.5,
                                    "top_k": 50,
                                    "max_tokens": 100,
                                    "max_time": 10.0,
                                    "top_p": 0.9,
                                    "repetition_penalty": 1.0,
                                    "use_cache": true,
                                    "results_per_prompt": 1,
                                    "wait_for_model": false
                                }
                                """;

        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(jsonSettings);
        var huggingFaceExecutionSettings = HuggingFacePromptExecutionSettings.FromExecutionSettings(executionSettings);

        Assert.Equal(0.5, huggingFaceExecutionSettings.Temperature);
        Assert.Equal(50, huggingFaceExecutionSettings.TopK);
        Assert.Equal(100, huggingFaceExecutionSettings.MaxTokens);
        Assert.Equal(10.0f, huggingFaceExecutionSettings.MaxTime);
        Assert.Equal(0.9f, huggingFaceExecutionSettings.TopP);
        Assert.Equal(1.0f, huggingFaceExecutionSettings.RepetitionPenalty);
        Assert.True(huggingFaceExecutionSettings.UseCache);
        Assert.Equal(1, huggingFaceExecutionSettings.ResultsPerPrompt);
        Assert.False(huggingFaceExecutionSettings.WaitForModel);
    }
}
