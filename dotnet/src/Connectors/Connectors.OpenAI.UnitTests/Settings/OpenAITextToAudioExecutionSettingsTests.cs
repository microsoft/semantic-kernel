// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UniTests.Settings;

/// <summary>
/// Unit tests for <see cref="OpenAITextToAudioExecutionSettings"/> class.
/// </summary>
public sealed class OpenAITextToAudioExecutionSettingsTests
{
    [Fact]
    public void ItReturnsDefaultSettingsWhenSettingsAreNull()
    {
        Assert.NotNull(OpenAITextToAudioExecutionSettings.FromExecutionSettings(null));
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
        var json = """
        {
            "model_id": "model_id",
            "voice": "voice",
            "response_format": "mp3",
            "speed": 1.2
        }
        """;

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

    [Fact]
    public void ItClonesAllProperties()
    {
        var textToAudioSettings = new OpenAITextToAudioExecutionSettings()
        {
            ModelId = "some_model",
            ResponseFormat = "some_format",
            Speed = 3.14f,
            Voice = "something"
        };

        var clone = (OpenAITextToAudioExecutionSettings)textToAudioSettings.Clone();
        Assert.NotSame(textToAudioSettings, clone);

        Assert.Equal("some_model", clone.ModelId);
        Assert.Equal("some_format", clone.ResponseFormat);
        Assert.Equal(3.14f, clone.Speed);
        Assert.Equal("something", clone.Voice);
    }

    [Fact]
    public void ItFreezesAndPreventsMutation()
    {
        var textToAudioSettings = new OpenAITextToAudioExecutionSettings()
        {
            ModelId = "some_model",
            ResponseFormat = "some_format",
            Speed = 3.14f,
            Voice = "something"
        };

        textToAudioSettings.Freeze();
        Assert.True(textToAudioSettings.IsFrozen);

        Assert.Throws<InvalidOperationException>(() => textToAudioSettings.ModelId = "new_model");
        Assert.Throws<InvalidOperationException>(() => textToAudioSettings.ResponseFormat = "some_format");
        Assert.Throws<InvalidOperationException>(() => textToAudioSettings.Speed = 3.14f);
        Assert.Throws<InvalidOperationException>(() => textToAudioSettings.Voice = "something");

        textToAudioSettings.Freeze(); // idempotent
        Assert.True(textToAudioSettings.IsFrozen);
    }
}
