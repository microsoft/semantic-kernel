// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.TextToAudio;

/// <summary>
/// Unit tests for <see cref="OpenAITextToAudioExecutionSettings"/> class.
/// </summary>
public sealed class OpenAITextToAudioExecutionSettingsTests
{
    [Fact]
    public void ItReturnsNullWhenSettingsAreNull()
    {
        Assert.Null(OpenAITextToAudioExecutionSettings.FromExecutionSettings(null));
    }

    [Fact]
    public void ItReturnsValidOpenAITextToAudioExecutionSettings()
    {
        // Arrange
        var textToAudioSettings = new OpenAITextToAudioExecutionSettings("voice")
        {
            ModelId = "model_id",
            ResponseFormat = "mp3",
            Speed = 1.0f
        };

        // Act
        var settings = OpenAITextToAudioExecutionSettings.FromExecutionSettings(textToAudioSettings);

        // Assert
        Assert.Same(textToAudioSettings, settings);
    }

    [Fact]
    public void ItCreatesOpenAIAudioToTextExecutionSettingsFromJson()
    {
        // Arrange
        var json = @"{
            ""model_id"": ""model_id"",
            ""voice"": ""voice"",
            ""response_format"": ""mp3"",
            ""speed"": 1.2
        }";

        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(json);

        // Act
        var settings = OpenAITextToAudioExecutionSettings.FromExecutionSettings(executionSettings);

        // Assert
        Assert.NotNull(settings);
        Assert.Equal("model_id", settings.ModelId);
        Assert.Equal("voice", settings.Voice);
        Assert.Equal("mp3", settings.ResponseFormat);
        Assert.Equal(1.2f, settings.Speed);
    }
}
