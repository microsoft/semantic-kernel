// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UniTests.Settings;

/// <summary>
/// Unit tests for <see cref="OpenAIAudioToTextExecutionSettings"/> class.
/// </summary>
public sealed class OpenAIAudioToTextExecutionSettingsTests
{
    [Fact]
    public void ItReturnsDefaultSettingsWhenSettingsAreNull()
    {
        Assert.NotNull(OpenAIAudioToTextExecutionSettings.FromExecutionSettings(null));
    }

    [Fact]
    public void ItReturnsValidOpenAIAudioToTextExecutionSettings()
    {
        // Arrange
        var audioToTextSettings = new OpenAIAudioToTextExecutionSettings("file.mp3")
        {
            ModelId = "model_id",
            Language = "en",
            Prompt = "prompt",
            ResponseFormat = "srt",
            Temperature = 0.2f
        };

        // Act
        var settings = OpenAIAudioToTextExecutionSettings.FromExecutionSettings(audioToTextSettings);

        // Assert
        Assert.Same(audioToTextSettings, settings);
    }

    [Fact]
    public void ItCreatesOpenAIAudioToTextExecutionSettingsFromJson()
    {
        // Arrange
        var json = """
        {
            "model_id": "model_id",
            "language": "en",
            "filename": "file.mp3",
            "prompt": "prompt",
            "response_format": "verbose_json",
            "temperature": 0.2
        }
        """;

        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(json);

        // Act
        var settings = OpenAIAudioToTextExecutionSettings.FromExecutionSettings(executionSettings);

        // Assert
        Assert.NotNull(settings);
        Assert.Equal("model_id", settings.ModelId);
        Assert.Equal("en", settings.Language);
        Assert.Equal("file.mp3", settings.Filename);
        Assert.Equal("prompt", settings.Prompt);
        Assert.Equal("verbose_json", settings.ResponseFormat);
        Assert.Equal(0.2f, settings.Temperature);
    }

    [Fact]
    public void ItClonesAllProperties()
    {
        var settings = new OpenAIAudioToTextExecutionSettings()
        {
            ModelId = "model_id",
            Language = "en",
            Prompt = "prompt",
            ResponseFormat = "json",
            Temperature = 0.2f,
            Filename = "something.mp3",
        };

        var clone = (OpenAIAudioToTextExecutionSettings)settings.Clone();
        Assert.NotSame(settings, clone);

        Assert.Equal("model_id", clone.ModelId);
        Assert.Equal("en", clone.Language);
        Assert.Equal("prompt", clone.Prompt);
        Assert.Equal("json", clone.ResponseFormat);
        Assert.Equal(0.2f, clone.Temperature);
        Assert.Equal("something.mp3", clone.Filename);
    }

    [Fact]
    public void ItFreezesAndPreventsMutation()
    {
        var settings = new OpenAIAudioToTextExecutionSettings()
        {
            ModelId = "model_id",
            Language = "en",
            Prompt = "prompt",
            ResponseFormat = "vtt",
            Temperature = 0.2f,
            Filename = "something.mp3",
        };

        settings.Freeze();
        Assert.True(settings.IsFrozen);

        Assert.Throws<InvalidOperationException>(() => settings.ModelId = "new_model");
        Assert.Throws<InvalidOperationException>(() => settings.Language = "some_format");
        Assert.Throws<InvalidOperationException>(() => settings.Prompt = "prompt");
        Assert.Throws<InvalidOperationException>(() => settings.ResponseFormat = "vtt");
        Assert.Throws<InvalidOperationException>(() => settings.Temperature = 0.2f);
        Assert.Throws<InvalidOperationException>(() => settings.Filename = "something");

        settings.Freeze(); // idempotent
        Assert.True(settings.IsFrozen);
    }
}
