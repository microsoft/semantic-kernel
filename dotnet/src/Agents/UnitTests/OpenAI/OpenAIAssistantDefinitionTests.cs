// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIAssistantDefinition"/>.
/// </summary>
public class OpenAIAssistantDefinitionTests
{
    /// <summary>
    /// Verify initial state.
    /// </summary>
    [Fact]
    public void VerifyOpenAIAssistantDefinitionInitialState()
    {
        OpenAIAssistantDefinition definition = new();

        Assert.Equal(string.Empty, definition.Id);
        Assert.Equal(string.Empty, definition.ModelId);
        Assert.Null(definition.Name);
        Assert.Null(definition.Instructions);
        Assert.Null(definition.Description);
        Assert.Null(definition.Metadata);
        Assert.Null(definition.ExecutionOptions);
        Assert.Null(definition.Temperature);
        Assert.Null(definition.TopP);
        Assert.Null(definition.VectorStoreId);
        Assert.Null(definition.CodeInterpreterFileIds);
        Assert.False(definition.EnableCodeInterpreter);
        Assert.False(definition.EnableJsonResponse);
    }

    /// <summary>
    /// Verify initialization.
    /// </summary>
    [Fact]
    public void VerifyOpenAIAssistantDefinitionAssignment()
    {
        OpenAIAssistantDefinition definition =
            new()
            {
                Id = "testid",
                Name = "testname",
                ModelId = "testmodel",
                Instructions = "testinstructions",
                Description = "testdescription",
                VectorStoreId = "#vs",
                Metadata = new Dictionary<string, string>() { { "a", "1" } },
                Temperature = 2,
                TopP = 0,
                ExecutionOptions =
                    new()
                    {
                        MaxCompletionTokens = 1000,
                        MaxPromptTokens = 1000,
                        ParallelToolCallsEnabled = false,
                        TruncationMessageCount = 12,
                    },
                CodeInterpreterFileIds = ["file1"],
                EnableCodeInterpreter = true,
                EnableJsonResponse = true,
            };

        Assert.Equal("testid", definition.Id);
        Assert.Equal("testname", definition.Name);
        Assert.Equal("testmodel", definition.ModelId);
        Assert.Equal("testinstructions", definition.Instructions);
        Assert.Equal("testdescription", definition.Description);
        Assert.Equal("#vs", definition.VectorStoreId);
        Assert.Equal(2, definition.Temperature);
        Assert.Equal(0, definition.TopP);
        Assert.NotNull(definition.ExecutionOptions);
        Assert.Equal(1000, definition.ExecutionOptions.MaxCompletionTokens);
        Assert.Equal(1000, definition.ExecutionOptions.MaxPromptTokens);
        Assert.Equal(12, definition.ExecutionOptions.TruncationMessageCount);
        Assert.False(definition.ExecutionOptions.ParallelToolCallsEnabled);
        Assert.Single(definition.Metadata);
        Assert.Single(definition.CodeInterpreterFileIds);
        Assert.True(definition.EnableCodeInterpreter);
        Assert.True(definition.EnableJsonResponse);
    }
}
