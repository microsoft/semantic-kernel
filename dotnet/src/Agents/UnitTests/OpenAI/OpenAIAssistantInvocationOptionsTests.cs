// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Text.Json;
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
        // Arrange
        OpenAIAssistantInvocationOptions options = new();

        // Assert
        Assert.Null(options.ModelName);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Assert.Null(options.AdditionalInstructions);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        Assert.Null(options.AdditionalInstructions);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        Assert.Null(options.AdditionalInstructions);
=======
>>>>>>> Stashed changes
=======
        Assert.Null(options.AdditionalInstructions);
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        Assert.Null(options.AdditionalInstructions);
=======
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
        OpenAIAssistantInvocationOptions options =
            new()
            {
                ModelName = "testmodel",
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                AdditionalInstructions = "test instructions",
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                AdditionalInstructions = "test instructions",
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
                AdditionalInstructions = "test instructions",
=======
>>>>>>> Stashed changes
=======
                AdditionalInstructions = "test instructions",
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
                AdditionalInstructions = "test instructions",
=======
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Assert.Equal("test instructions", options.AdditionalInstructions);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        Assert.Equal("test instructions", options.AdditionalInstructions);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        Assert.Equal("test instructions", options.AdditionalInstructions);
=======
>>>>>>> Stashed changes
=======
        Assert.Equal("test instructions", options.AdditionalInstructions);
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        Assert.Equal("test instructions", options.AdditionalInstructions);
=======
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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

    private static void ValidateSerialization(OpenAIAssistantInvocationOptions source)
    {
        // Act
        string json = JsonSerializer.Serialize(source);

        OpenAIAssistantInvocationOptions? target = JsonSerializer.Deserialize<OpenAIAssistantInvocationOptions>(json);

        // Assert
        Assert.NotNull(target);
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
