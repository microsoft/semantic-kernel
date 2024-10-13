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
﻿// Copyright (c) Microsoft. All rights reserved.
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
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
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
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
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null);

        // Assert
        Assert.NotNull(options);
        Assert.Null(options.Temperature);
        Assert.Null(options.NucleusSamplingFactor);
        Assert.Equal("test", options.AdditionalInstructions);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null, null);

        // Assert
        Assert.NotNull(options);
        Assert.Null(options.InstructionsOverride);
        Assert.Null(options.Temperature);
        Assert.Null(options.NucleusSamplingFactor);
        Assert.Equal("test", options.AdditionalInstructions);
            };

        // Act
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null);

        // Assert
        Assert.NotNull(options);
        Assert.Null(options.Temperature);
        Assert.Null(options.NucleusSamplingFactor);
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
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, "test", invocationOptions);

        // Assert
        Assert.NotNull(options);
        Assert.Equal("test", options.InstructionsOverride);
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
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, invocationOptions);

        // Assert
        Assert.NotNull(options);
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
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, "test", invocationOptions);

        // Assert
        Assert.NotNull(options);
        Assert.Equal("test", options.InstructionsOverride);
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
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, invocationOptions);
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, invocationOptions);
=======
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null, invocationOptions);
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, invocationOptions);
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null, invocationOptions);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null, invocationOptions);
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, invocationOptions);
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null, invocationOptions);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null, invocationOptions);
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, invocationOptions);
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null, invocationOptions);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

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
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, invocationOptions);
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, invocationOptions);
=======
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null, invocationOptions);
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, invocationOptions);
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null, invocationOptions);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null, invocationOptions);
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, invocationOptions);
        RunCreationOptions options = AssistantRunOptionsFactory.GenerateOptions(definition, null, invocationOptions);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

        // Assert
        Assert.Equal(2, options.Metadata.Count);
        Assert.Equal("value", options.Metadata["key1"]);
        Assert.Equal(string.Empty, options.Metadata["key2"]);
    }
}
