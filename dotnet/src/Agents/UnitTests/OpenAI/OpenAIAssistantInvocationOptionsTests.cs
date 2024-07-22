// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIAssistantInvocationOptions"/>.
/// </summary>
public class OpenAIAssistantInvocationOptionsTests
{
    /// <summary>
    /// Verify initial state.
    /// </summary>
    [Fact]
    public void OpenAIAssistantInvocationOptionsInitialState()
    {
        OpenAIAssistantInvocationOptions options = new();

        Assert.Null(options.ModelName);
        Assert.Null(options.Metadata);
        Assert.Null(options.Temperature);
        Assert.Null(options.TopP);
        Assert.Null(options.ParallelToolCallsEnabled);
        Assert.Null(options.MaxCompletionTokens);
        Assert.Null(options.MaxPromptTokens);
        Assert.Null(options.TruncationMessageCount);
        Assert.Null(options.EnableJsonResponse);
        Assert.False(options.EnableCodeInterpreter);
        Assert.False(options.EnableFileSearch);
    }

    /// <summary>
    /// Verify initialization.
    /// </summary>
    [Fact]
    public void OpenAIAssistantInvocationOptionsAssignment()
    {
        OpenAIAssistantInvocationOptions options =
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

        Assert.Equal("testmodel", options.ModelName);
        Assert.Equal(2, options.Temperature);
        Assert.Equal(0, options.TopP);
        Assert.Equal(1000, options.MaxCompletionTokens);
        Assert.Equal(1000, options.MaxPromptTokens);
        Assert.Equal(12, options.TruncationMessageCount);
        Assert.False(options.ParallelToolCallsEnabled);
        Assert.Single(options.Metadata);
        Assert.True(options.EnableCodeInterpreter);
        Assert.True(options.EnableJsonResponse);
        Assert.True(options.EnableFileSearch);
    }
}
