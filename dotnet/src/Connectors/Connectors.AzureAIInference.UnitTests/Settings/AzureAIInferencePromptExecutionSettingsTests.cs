// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureAIInference;
using Xunit;

namespace SemanticKernel.Connectors.AzureAIInference.UnitTests.Settings;

public sealed class AzureAIInferencePromptExecutionSettingsTests
{
    [Fact]
    public void ItCreatesAzureAIInferenceExecutionSettingsWithCorrectDefaults()
    {
        // Arrange
        // Act
        AzureAIInferencePromptExecutionSettings executionSettings = AzureAIInferencePromptExecutionSettings.FromExecutionSettings(null);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Null(executionSettings.Temperature);
        Assert.Null(executionSettings.FrequencyPenalty);
        Assert.Null(executionSettings.PresencePenalty);
        Assert.Null(executionSettings.NucleusSamplingFactor);
        Assert.Null(executionSettings.ResponseFormat);
        Assert.Null(executionSettings.Seed);
        Assert.Null(executionSettings.MaxTokens);
        Assert.Null(executionSettings.Tools);
        Assert.Null(executionSettings.StopSequences);
        Assert.Empty(executionSettings.ExtensionData!);
    }

    [Fact]
    public void ItUsesExistingAzureAIInferenceExecutionSettings()
    {
        // Arrange
        AzureAIInferencePromptExecutionSettings actualSettings = new()
        {
            Temperature = 0.7f,
            NucleusSamplingFactor = 0.7f,
            FrequencyPenalty = 0.7f,
            PresencePenalty = 0.7f,
            StopSequences = ["foo", "bar"],
            MaxTokens = 128
        };

        // Act
        AzureAIInferencePromptExecutionSettings executionSettings = AzureAIInferencePromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(actualSettings, executionSettings);
        Assert.Equal(128, executionSettings.MaxTokens);
    }

    [Fact]
    public void ItCanUseAzureAIInferenceExecutionSettings()
    {
        // Arrange
        PromptExecutionSettings actualSettings = new()
        {
            ExtensionData = new Dictionary<string, object>() {
                { "max_tokens", 1000 },
                { "temperature", 0 }
            }
        };

        // Act
        AzureAIInferencePromptExecutionSettings executionSettings = AzureAIInferencePromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal(1000, executionSettings.MaxTokens);
        Assert.Equal(0, executionSettings.Temperature);
    }

    [Fact]
    public void ItCreatesAzureAIInferenceExecutionSettingsFromExtraPropertiesSnakeCase()
    {
        // Arrange
        PromptExecutionSettings actualSettings = new()
        {
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.7 },
                { "top_p", 0.7 },
                { "frequency_penalty", 0.7 },
                { "presence_penalty", 0.7 },
                { "stop", new [] { "foo", "bar" } },
                { "max_tokens", 128 },
                { "seed", 123456 },
            }
        };

        // Act
        AzureAIInferencePromptExecutionSettings executionSettings = AzureAIInferencePromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        AssertExecutionSettings(executionSettings);
    }

    [Fact]
    public void ItCreatesAzureAIInferenceExecutionSettingsFromExtraPropertiesAsStrings()
    {
        // Arrange
        PromptExecutionSettings actualSettings = new()
        {
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.7 },
                { "top_p", "0.7" },
                { "frequency_penalty", "0.7" },
                { "presence_penalty", "0.7" },
                { "stop", new [] { "foo", "bar" } },
                { "max_tokens", "128" },
                { "response_format", "json" },
                { "seed", 123456 },
            }
        };

        // Act
        AzureAIInferencePromptExecutionSettings executionSettings = AzureAIInferencePromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        AssertExecutionSettings(executionSettings);
    }

    [Fact]
    public void ItCreatesAzureAIInferenceExecutionSettingsFromJsonSnakeCase()
    {
        // Arrange
        var json = """
            {
              "temperature": 0.7,
              "top_p": 0.7,
              "frequency_penalty": 0.7,
              "presence_penalty": 0.7,
              "stop": [ "foo", "bar" ],
              "max_tokens": 128,
              "response_format": "text",
              "seed": 123456
            }
            """;
        var actualSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(json);

        // Act
        AzureAIInferencePromptExecutionSettings executionSettings = AzureAIInferencePromptExecutionSettings.FromExecutionSettings(actualSettings);

        // Assert
        AssertExecutionSettings(executionSettings);
    }

    [Fact]
    public void PromptExecutionSettingsCloneWorksAsExpected()
    {
        // Arrange
        string configPayload = """
        {
            "max_tokens": 60,
            "temperature": 0.5,
            "top_p": 0.0,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0
        }
        """;
        var executionSettings = JsonSerializer.Deserialize<AzureAIInferencePromptExecutionSettings>(configPayload);

        // Act
        var clone = executionSettings!.Clone();

        // Assert
        Assert.NotNull(clone);
        Assert.Equal(executionSettings.ModelId, clone.ModelId);
        Assert.Equivalent(executionSettings.ExtensionData, clone.ExtensionData);
    }

    [Fact]
    public void PromptExecutionSettingsFreezeWorksAsExpected()
    {
        // Arrange
        string configPayload = """
        {
            "max_tokens": 60,
            "temperature": 0.5,
            "top_p": 0.0,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
            "response_format": "json",
            "stop": [ "DONE" ]
        }
        """;
        var executionSettings = JsonSerializer.Deserialize<AzureAIInferencePromptExecutionSettings>(configPayload)!;
        executionSettings.ExtensionData = new Dictionary<string, object>() { { "new", 5 } };

        // Act
        executionSettings!.Freeze();

        // Assert
        Assert.True(executionSettings.IsFrozen);
        Assert.Throws<InvalidOperationException>(() => executionSettings.ModelId = "new-model");
        Assert.Throws<InvalidOperationException>(() => executionSettings.Temperature = 1);
        Assert.Throws<InvalidOperationException>(() => executionSettings.FrequencyPenalty = 1);
        Assert.Throws<InvalidOperationException>(() => executionSettings.PresencePenalty = 1);
        Assert.Throws<InvalidOperationException>(() => executionSettings.NucleusSamplingFactor = 1);
        Assert.Throws<InvalidOperationException>(() => executionSettings.MaxTokens = 100);
        Assert.Throws<InvalidOperationException>(() => executionSettings.ResponseFormat = "text");
        Assert.Throws<NotSupportedException>(() => executionSettings.StopSequences?.Add("STOP"));
        Assert.Throws<NotSupportedException>(() => executionSettings.ExtensionData["new"] = 6);

        executionSettings!.Freeze(); // idempotent
        Assert.True(executionSettings.IsFrozen);
    }

    [Fact]
    public void FromExecutionSettingsWithDataDoesNotIncludeEmptyStopSequences()
    {
        // Arrange
        PromptExecutionSettings settings = new AzureAIInferencePromptExecutionSettings { StopSequences = [] };

        // Act
        var executionSettings = AzureAIInferencePromptExecutionSettings.FromExecutionSettings(settings);

        // Assert
        Assert.NotNull(executionSettings.StopSequences);
        Assert.Empty(executionSettings.StopSequences);
    }

    private static void AssertExecutionSettings(AzureAIInferencePromptExecutionSettings executionSettings)
    {
        Assert.NotNull(executionSettings);
        Assert.Equal(0.7f, executionSettings.Temperature);
        Assert.Equal(0.7f, executionSettings.NucleusSamplingFactor);
        Assert.Equal(0.7f, executionSettings.FrequencyPenalty);
        Assert.Equal(0.7f, executionSettings.PresencePenalty);
        Assert.Equal(["foo", "bar"], executionSettings.StopSequences);
        Assert.Equal(128, executionSettings.MaxTokens);
        Assert.Equal(123456, executionSettings.Seed);
    }
}
