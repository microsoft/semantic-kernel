// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.AudioToText;

/// <summary>
/// Unit tests for <see cref="OpenAIAudioToTextExecutionSettings"/> class.
/// </summary>
public sealed class OpenAIAudioToTextExecutionSettingsTests
{
    [Fact]
    public void ItReturnsNullWhenSettingsAreNull()
    {
        Assert.Null(OpenAIAudioToTextExecutionSettings.FromExecutionSettings(null));
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
            ResponseFormat = "text",
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
        var json = @"{
            ""model_id"": ""model_id"",
            ""language"": ""en"",
            ""filename"": ""file.mp3"",
            ""prompt"": ""prompt"",
            ""response_format"": ""text"",
            ""temperature"": 0.2
        }";

        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(json);

        // Act
        var settings = OpenAIAudioToTextExecutionSettings.FromExecutionSettings(executionSettings);

        // Assert
        Assert.NotNull(settings);
        Assert.Equal("model_id", settings.ModelId);
        Assert.Equal("en", settings.Language);
        Assert.Equal("file.mp3", settings.Filename);
        Assert.Equal("prompt", settings.Prompt);
        Assert.Equal("text", settings.ResponseFormat);
        Assert.Equal(0.2f, settings.Temperature);
    }
}
