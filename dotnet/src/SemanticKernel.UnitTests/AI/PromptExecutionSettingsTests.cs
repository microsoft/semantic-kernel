// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.AI;
public class PromptExecutionSettingsTests
{
    [Fact]
    public void PromptExecutionSettingsCloneWorksAsExpected()
    {
        // Arrange
        string configPayload = """
        {
            "model_id": "gpt-3",
            "service_id": "service-1",
            "max_tokens": 60,
            "temperature": 0.5,
            "top_p": 0.0,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
            "function_choice_behavior": {
                "type": "auto",
                "functions": ["p1.f1"]
            }
        }
        """;
        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(configPayload);

        // Act
        var clone = executionSettings!.Clone();

        // Assert
        Assert.NotNull(clone);
        Assert.Equal(executionSettings.ModelId, clone.ModelId);
        Assert.Equivalent(executionSettings.ExtensionData, clone.ExtensionData);
        Assert.Equivalent(executionSettings.FunctionChoiceBehavior, clone.FunctionChoiceBehavior);
        Assert.Equal(executionSettings.ServiceId, clone.ServiceId);
    }

    [Fact]
    public void PromptExecutionSettingsSerializationWorksAsExpected()
    {
        // Arrange
        string configPayload = """
        {
            "model_id": "gpt-3",
            "service_id": "service-1",
            "max_tokens": 60,
            "temperature": 0.5,
            "top_p": 0.0,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0
        }
        """;

        // Act
        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(configPayload);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal("gpt-3", executionSettings.ModelId);
        Assert.Equal("service-1", executionSettings.ServiceId);
        Assert.Equal(60, ((JsonElement)executionSettings.ExtensionData!["max_tokens"]).GetInt32());
        Assert.Equal(0.5, ((JsonElement)executionSettings.ExtensionData!["temperature"]).GetDouble());
        Assert.Equal(0.0, ((JsonElement)executionSettings.ExtensionData!["top_p"]).GetDouble());
        Assert.Equal(0.0, ((JsonElement)executionSettings.ExtensionData!["presence_penalty"]).GetDouble());
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
                "frequency_penalty": 0.0
            }
            """;
        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(configPayload);

        // Act
        executionSettings!.Freeze();

        // Assert
        Assert.True(executionSettings.IsFrozen);
        Assert.Throws<InvalidOperationException>(() => executionSettings.ModelId = "gpt-4");
        Assert.NotNull(executionSettings.ExtensionData);
        Assert.Throws<NotSupportedException>(() => executionSettings.ExtensionData.Add("results_per_prompt", 2));
        Assert.Throws<NotSupportedException>(() => executionSettings.ExtensionData["temperature"] = 1);
        Assert.Throws<InvalidOperationException>(() => executionSettings.FunctionChoiceBehavior = FunctionChoiceBehavior.Auto());

        executionSettings!.Freeze(); // idempotent
        Assert.True(executionSettings.IsFrozen);
    }
}
