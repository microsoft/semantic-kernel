// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIAssistantInvocationSettings"/>.
/// </summary>
public class OpenAIAssistantInvocationSettingsTests
{
    /// <summary>
    /// Verify initial state.
    /// </summary>
    [Fact]
    public void OpenAIAssistantInvocationSettingsInitialState()
    {
        OpenAIAssistantInvocationSettings settings = new();

        Assert.Null(settings.ModelName);
        Assert.Null(settings.Metadata);
        Assert.Null(settings.Temperature);
        Assert.Null(settings.TopP);
        Assert.Null(settings.ParallelToolCallsEnabled);
        Assert.Null(settings.MaxCompletionTokens);
        Assert.Null(settings.MaxPromptTokens);
        Assert.Null(settings.TruncationMessageCount);
        Assert.Null(settings.EnableJsonResponse);
        Assert.False(settings.EnableCodeInterpreter);
        Assert.False(settings.EnableFileSearch);
    }

    /// <summary>
    /// Verify initialization.
    /// </summary>
    [Fact]
    public void OpenAIAssistantInvocationSettingsAssignment()
    {
        OpenAIAssistantInvocationSettings settings =
            new()
            {
                ModelName = "testmodel",
                Metadata = new Dictionary<string, string>() { { "a", "1" } },
                MaxCompletionTokens = 1000,
                MaxPromptTokens = 1000,
                ParallelToolCallsEnabled = false,
                TruncationMessageCount = 12,
                Temperature = 2,
                TopP = 0,
                EnableCodeInterpreter = true,
                EnableJsonResponse = true,
                EnableFileSearch = true,
            };

        Assert.Equal("testmodel", settings.ModelName);
        Assert.Equal(2, settings.Temperature);
        Assert.Equal(0, settings.TopP);
        Assert.Equal(1000, settings.MaxCompletionTokens);
        Assert.Equal(1000, settings.MaxPromptTokens);
        Assert.Equal(12, settings.TruncationMessageCount);
        Assert.False(settings.ParallelToolCallsEnabled);
        Assert.Single(settings.Metadata);
        Assert.True(settings.EnableCodeInterpreter);
        Assert.True(settings.EnableJsonResponse);
        Assert.True(settings.EnableFileSearch);
    }
}
