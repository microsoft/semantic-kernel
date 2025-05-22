// Copyright (c) Microsoft. All rights reserved.
using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Assistants;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI.Internal;

/// <summary>
/// Unit testing of <see cref="AssistantRunOptionsFactory"/>.
/// </summary>
public class AssistantRunOptionsFactoryTests
{
    /// <summary>
    /// Verify run options generation with null <see cref="OpenAIAssistantInvocationOptions"/>.
    /// </summary>
    [Fact]
    public void AssistantRunOptionsFactoryExecutionOptionsNullTest()
    {
        // Arrange
        RunCreationOptions defaultOptions =
            new()
            {
                ModelOverride = "gpt-anything",
                Temperature = 0.5F,
                AdditionalInstructions = "test",
            };

        // Act
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(defaultOptions, null, null, threadExtensionsContext: null);

        // Assert
        Assert.NotNull(options);
        Assert.Empty(options.AdditionalMessages);
        Assert.Null(options.InstructionsOverride);
        Assert.Null(options.NucleusSamplingFactor);
        Assert.Equal("test", options.AdditionalInstructions);
        Assert.Equal(0.5F, options.Temperature);
        Assert.Empty(options.Metadata);
    }

    /// <summary>
    /// Verify run options generation with equivalent <see cref="OpenAIAssistantInvocationOptions"/>.
    /// </summary>
    [Fact]
    public void AssistantRunOptionsFactoryExecutionOptionsEquivalentTest()
    {
        // Arrange
        RunCreationOptions defaultOptions =
            new()
            {
                ModelOverride = "gpt-anything",
                Temperature = 0.5F,
            };

        RunCreationOptions invocationOptions =
            new()
            {
                Temperature = 0.5F,
            };

        // Act
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(defaultOptions, "test", invocationOptions, threadExtensionsContext: null);

        // Assert
        Assert.NotNull(options);
        Assert.Null(options.NucleusSamplingFactor);
        Assert.Equal("test", options.InstructionsOverride);
        Assert.Equal(0.5F, options.Temperature);
    }

    /// <summary>
    /// Verify run options generation with <see cref="OpenAIAssistantInvocationOptions"/> override.
    /// </summary>
    [Fact]
    public void AssistantRunOptionsFactoryExecutionOptionsOverrideTest()
    {
        // Arrange
        RunCreationOptions defaultOptions =
            new()
            {
                ModelOverride = "gpt-anything",
                Temperature = 0.5F,
                TruncationStrategy = RunTruncationStrategy.CreateLastMessagesStrategy(5),
            };

        RunCreationOptions invocationOptions =
            new()
            {
                ModelOverride = "gpt-anything",
                AdditionalInstructions = "test2",
                Temperature = 0.9F,
                TruncationStrategy = RunTruncationStrategy.CreateLastMessagesStrategy(8),
                ResponseFormat = AssistantResponseFormat.JsonObject,
            };

        // Act
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(defaultOptions, null, invocationOptions, threadExtensionsContext: null);

        // Assert
        Assert.NotNull(options);
        Assert.Equal(0.9F, options.Temperature);
        Assert.Equal(8, options.TruncationStrategy.LastMessages);
        Assert.Equal("test2", options.AdditionalInstructions);
        Assert.Equal(AssistantResponseFormat.JsonObject, options.ResponseFormat);
        Assert.Null(options.NucleusSamplingFactor);
    }

    /// <summary>
    /// Verify run options generation with <see cref="OpenAIAssistantInvocationOptions"/> metadata.
    /// </summary>
    [Fact]
    public void AssistantRunOptionsFactoryExecutionOptionsMetadataTest()
    {
        // Arrange
        RunCreationOptions defaultOptions =
            new()
            {
                ModelOverride = "gpt-anything",
                Temperature = 0.5F,
                TruncationStrategy = RunTruncationStrategy.CreateLastMessagesStrategy(5),
            };

        RunCreationOptions invocationOptions =
            new()
            {
                Metadata =
                {
                    { "key1", "value" },
                    { "key2", null! },
                },
            };

        // Act
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(defaultOptions, null, invocationOptions, threadExtensionsContext: null);

        // Assert
        Assert.Equal(2, options.Metadata.Count);
        Assert.Equal("value", options.Metadata["key1"]);
        Assert.Equal(string.Empty, options.Metadata["key2"]);
    }

    /// <summary>
    /// Verify run options generation with <see cref="OpenAIAssistantInvocationOptions"/> metadata.
    /// </summary>
    [Fact]
    public void AssistantRunOptionsFactoryExecutionOptionsMessagesTest()
    {
        // Arrange
        RunCreationOptions defaultOptions =
            new()
            {
                ModelOverride = "gpt-anything",
            };

        ChatMessageContent message = new(AuthorRole.User, "test message");
        RunCreationOptions invocationOptions =
            new()
            {
                AdditionalMessages = { message.ToThreadInitializationMessage() },
            };

        // Act
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(defaultOptions, null, invocationOptions, threadExtensionsContext: null);

        // Assert
        Assert.Single(options.AdditionalMessages);
    }

    /// <summary>
    /// Verify run options generation with <see cref="OpenAIAssistantInvocationOptions"/> metadata.
    /// </summary>
    [Fact]
    public void AssistantRunOptionsFactoryExecutionOptionsMaxTokensTest()
    {
        // Arrange
        RunCreationOptions defaultOptions =
            new()
            {
                ModelOverride = "gpt-anything",
                Temperature = 0.5F,
                MaxOutputTokenCount = 4096,
                MaxInputTokenCount = 1024,
            };

        // Act
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(defaultOptions, null, null, threadExtensionsContext: null);

        // Assert
        Assert.Equal(1024, options.MaxInputTokenCount);
        Assert.Equal(4096, options.MaxOutputTokenCount);
    }

    /// <summary>
    /// Verify run options generation with <see cref="OpenAIAssistantInvocationOptions"/> metadata.
    /// </summary>
    [Fact]
    public void AssistantRunOptionsFactoryAdditionalInstructionsTest()
    {
        // Arrange
        RunCreationOptions defaultOptions =
            new()
            {
                ModelOverride = "gpt-anything",
                Temperature = 0.5F,
                MaxOutputTokenCount = 4096,
                MaxInputTokenCount = 1024,
                AdditionalInstructions = "DefaultInstructions"
            };

        RunCreationOptions invocationOptions =
            new()
            {
                AdditionalInstructions = "OverrideInstructions",
            };

        // Act
        RunCreationOptions optionsWithOverride = AssistantRunOptionsFactory.GenerateOptions(defaultOptions, null, invocationOptions, threadExtensionsContext: "Context");
        RunCreationOptions optionsWithoutOverride = AssistantRunOptionsFactory.GenerateOptions(defaultOptions, null, null, threadExtensionsContext: "Context");

        // Assert
        Assert.Equal($"OverrideInstructions{Environment.NewLine}{Environment.NewLine}Context", optionsWithOverride.AdditionalInstructions);
        Assert.Equal($"DefaultInstructions{Environment.NewLine}{Environment.NewLine}Context", optionsWithoutOverride.AdditionalInstructions);
    }
}
