// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using SemanticKernel.Agents.UnitTests.Test;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.AzureAI;

/// <summary>
/// Unit testing of <see cref="AzureAIInvocationOptions"/>.
/// </summary>
public class AzureAIAssistantInvocationOptionsTests
{
    /// <summary>
    /// Verify initial state.
    /// </summary>
    [Fact]
    public void OpenAIAssistantInvocationOptionsInitialState()
    {
        // Arrange
        AzureAIInvocationOptions options = new();

        // Assert
        Assert.Null(options.ModelName);
        Assert.Null(options.AdditionalInstructions);
        Assert.Null(options.AdditionalMessages);
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

        // Act and Assert
        ValidateSerialization(options);
    }

    /// <summary>
    /// Verify initialization.
    /// </summary>
    [Fact]
    public void OpenAIAssistantInvocationOptionsAssignment()
    {
        // Arrange
        AzureAIInvocationOptions options =
            new()
            {
                ModelName = "testmodel",
                AdditionalInstructions = "test instructions",
                AdditionalMessages = [
                    new ChatMessageContent(AuthorRole.User, "test message")
                ],
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

        // Assert
        Assert.Equal("testmodel", options.ModelName);
        Assert.Equal("test instructions", options.AdditionalInstructions);
        Assert.Single(options.AdditionalMessages);
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

        // Act and Assert
        ValidateSerialization(options);
    }

    private static void ValidateSerialization(AzureAIInvocationOptions source)
    {
        // Act
        string json = JsonSerializer.Serialize(source);

        AzureAIInvocationOptions? target = JsonSerializer.Deserialize<AzureAIInvocationOptions>(json);

        // Assert
        Assert.NotNull(target);
        Assert.Equal(source.AdditionalInstructions, target.AdditionalInstructions);
        Assert.Equivalent(source.AdditionalMessages, target.AdditionalMessages);
        Assert.Equal(source.ModelName, target.ModelName);
        Assert.Equal(source.Temperature, target.Temperature);
        Assert.Equal(source.TopP, target.TopP);
        Assert.Equal(source.MaxCompletionTokens, target.MaxCompletionTokens);
        Assert.Equal(source.MaxPromptTokens, target.MaxPromptTokens);
        Assert.Equal(source.TruncationMessageCount, target.TruncationMessageCount);
        Assert.Equal(source.EnableCodeInterpreter, target.EnableCodeInterpreter);
        Assert.Equal(source.EnableJsonResponse, target.EnableJsonResponse);
        Assert.Equal(source.EnableFileSearch, target.EnableFileSearch);
        AssertCollection.Equal(source.Metadata, target.Metadata);
    }
}
