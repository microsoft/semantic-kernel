// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Onnx;
using Xunit;

namespace SemanticKernel.Connectors.Onnx.UnitTests;

/// <summary>
/// Unit tests for <see cref="OnnxRuntimeGenAIPromptExecutionSettings"/>.
/// </summary>
public class OnnxRuntimeGenAIPromptExecutionSettingsTests
{
    [Fact]
    public void FromExecutionSettingsWhenAlreadyMistralShouldReturnSame()
    {
        // Arrange
        var executionSettings = new OnnxRuntimeGenAIPromptExecutionSettings();

        // Act
        var onnxExecutionSettings = OnnxRuntimeGenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);

        // Assert
        Assert.Same(executionSettings, onnxExecutionSettings);
    }

    [Fact]
    public void FromExecutionSettingsWhenNullShouldReturnDefaultSettings()
    {
        // Arrange
        PromptExecutionSettings? executionSettings = null;

        // Act
        var onnxExecutionSettings = OnnxRuntimeGenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);

        // Assert        
        Assert.Null(onnxExecutionSettings.TopK);
        Assert.Null(onnxExecutionSettings.TopP);
        Assert.Null(onnxExecutionSettings.Temperature);
        Assert.Null(onnxExecutionSettings.RepetitionPenalty);
        Assert.Null(onnxExecutionSettings.PastPresentShareBuffer);
        Assert.Null(onnxExecutionSettings.NumReturnSequences);
        Assert.Null(onnxExecutionSettings.NumBeams);
        Assert.Null(onnxExecutionSettings.NoRepeatNgramSize);
        Assert.Null(onnxExecutionSettings.MinTokens);
        Assert.Null(onnxExecutionSettings.MaxTokens);
        Assert.Null(onnxExecutionSettings.LengthPenalty);
        Assert.Null(onnxExecutionSettings.DiversityPenalty);
        Assert.Null(onnxExecutionSettings.EarlyStopping);
        Assert.Null(onnxExecutionSettings.DoSample);
    }

    [Fact]
    public void FromExecutionSettingsWhenSerializedHasPropertiesShouldPopulateSpecialized()
    {
        // Arrange
        string jsonSettings = """
                                {
                                    "top_k": 2,
                                    "top_p": 0.9,
                                    "temperature": 0.5,
                                    "repetition_penalty": 0.1,
                                    "past_present_share_buffer": true,
                                    "num_return_sequences": 200,
                                    "num_beams": 20,
                                    "no_repeat_ngram_size": 15,
                                    "min_tokens": 10,
                                    "max_tokens": 100,
                                    "length_penalty": 0.2,
                                    "diversity_penalty": 0.3,
                                    "early_stopping": false,
                                    "do_sample": true
                                }
                                """;

        // Act
        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(jsonSettings);
        var onnxExecutionSettings = OnnxRuntimeGenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);

        // Assert
        Assert.Equal(2, onnxExecutionSettings.TopK);
        Assert.Equal(0.9f, onnxExecutionSettings.TopP);
        Assert.Equal(0.5f, onnxExecutionSettings.Temperature);
        Assert.Equal(0.1f, onnxExecutionSettings.RepetitionPenalty);
        Assert.True(onnxExecutionSettings.PastPresentShareBuffer);
        Assert.Equal(200, onnxExecutionSettings.NumReturnSequences);
        Assert.Equal(20, onnxExecutionSettings.NumBeams);
        Assert.Equal(15, onnxExecutionSettings.NoRepeatNgramSize);
        Assert.Equal(10, onnxExecutionSettings.MinTokens);
        Assert.Equal(100, onnxExecutionSettings.MaxTokens);
        Assert.Equal(0.2f, onnxExecutionSettings.LengthPenalty);
        Assert.Equal(0.3f, onnxExecutionSettings.DiversityPenalty);
        Assert.False(onnxExecutionSettings.EarlyStopping);
        Assert.True(onnxExecutionSettings.DoSample);
    }

    [Fact]
    public void ItShouldCreateOnnxPromptExecutionSettingsFromCustomPromptExecutionSettings()
    {
        // Arrange
        var customExecutionSettings = new CustomPromptExecutionSettings() { ServiceId = "service-id", Temperature = 36.6f };

        // Act
        var onnxExecutionSettings = OnnxRuntimeGenAIPromptExecutionSettings.FromExecutionSettings(customExecutionSettings);

        // Assert
        Assert.Equal("service-id", onnxExecutionSettings.ServiceId);
        Assert.Equal(36.6f, onnxExecutionSettings.Temperature);
    }

    [Fact]
    public void ItShouldCreateOnnxPromptExecutionSettingsFromCustomPromptExecutionSettingsUsingJSOs()
    {
        // Arrange
        var jsos = new JsonSerializerOptions
        {
            TypeInfoResolver = CustomPromptExecutionSettingsJsonSerializerContext.Default
        };

        var customExecutionSettings = new CustomPromptExecutionSettings() { ServiceId = "service-id", Temperature = 36.6f };

        // Act
        var onnxExecutionSettings = OnnxRuntimeGenAIPromptExecutionSettings.FromExecutionSettings(customExecutionSettings, jsos);

        // Assert
        Assert.Equal("service-id", onnxExecutionSettings.ServiceId);
        Assert.Equal(36.6f, onnxExecutionSettings.Temperature);
    }
}
