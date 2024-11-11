// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
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
        OpenAIAssistantDefinition definition =
            new("gpt-anything")
            {
                Temperature = 0.5F,
                ExecutionOptions =
                    new()
                    {
                        AdditionalInstructions = "test",
                    },
            };

        // Act
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null, null);

        // Assert
        Assert.NotNull(options);
        Assert.Null(options.InstructionsOverride);
        Assert.Null(options.Temperature);
        Assert.Null(options.NucleusSamplingFactor);
        Assert.Equal("test", options.AdditionalInstructions);
        Assert.Empty(options.Metadata);
    }

    /// <summary>
    /// Verify run options generation with equivalent <see cref="OpenAIAssistantInvocationOptions"/>.
    /// </summary>
    [Fact]
    public void AssistantRunOptionsFactoryExecutionOptionsEquivalentTest()
    {
        // Arrange
        OpenAIAssistantDefinition definition =
            new("gpt-anything")
            {
                Temperature = 0.5F,
            };

        OpenAIAssistantInvocationOptions invocationOptions =
            new()
            {
                Temperature = 0.5F,
            };

        // Act
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, "test", invocationOptions);

        // Assert
        Assert.NotNull(options);
        Assert.Equal("test", options.InstructionsOverride);
        Assert.Null(options.Temperature);
        Assert.Null(options.NucleusSamplingFactor);
    }

    /// <summary>
    /// Verify run options generation with <see cref="OpenAIAssistantInvocationOptions"/> override.
    /// </summary>
    [Fact]
    public void AssistantRunOptionsFactoryExecutionOptionsOverrideTest()
    {
        // Arrange
        OpenAIAssistantDefinition definition =
            new("gpt-anything")
            {
                Temperature = 0.5F,
                ExecutionOptions =
                    new()
                    {
                        AdditionalInstructions = "test1",
                        TruncationMessageCount = 5,
                    },
            };

        OpenAIAssistantInvocationOptions invocationOptions =
            new()
            {
                AdditionalInstructions = "test2",
                Temperature = 0.9F,
                TruncationMessageCount = 8,
                EnableJsonResponse = true,
            };

        // Act
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null, invocationOptions);

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
        OpenAIAssistantDefinition definition =
            new("gpt-anything")
            {
                Temperature = 0.5F,
                ExecutionOptions =
                    new()
                    {
                        TruncationMessageCount = 5,
                    },
            };

        OpenAIAssistantInvocationOptions invocationOptions =
            new()
            {
                Metadata = new Dictionary<string, string>
                {
                    { "key1", "value" },
                    { "key2", null! },
                },
            };

        // Act
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null, invocationOptions);

        // Assert
        Assert.Equal(2, options.Metadata.Count);
        Assert.Equal("value", options.Metadata["key1"]);
        Assert.Equal(string.Empty, options.Metadata["key2"]);
    }
}
