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

        Assert.Null(definition.Id);
        Assert.Null(definition.Name);
        Assert.Null(definition.Model);
        Assert.Null(definition.Instructions);
        Assert.Null(definition.Description);
        Assert.Null(definition.Metadata);
        Assert.Null(definition.VectorStoreId);
        Assert.False(definition.EnableCodeInterpreter);
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
                Model = "testmodel",
                Instructions = "testinstructions",
                Description = "testdescription",
                VectorStoreId = "#vs",
                Metadata = new Dictionary<string, string>() { { "a", "1" } },
                EnableCodeInterpreter = true,
            };

        Assert.Equal("testid", definition.Id);
        Assert.Equal("testname", definition.Name);
        Assert.Equal("testmodel", definition.Model);
        Assert.Equal("testinstructions", definition.Instructions);
        Assert.Equal("testdescription", definition.Description);
        Assert.Equal("#vs", definition.VectorStoreId);
        Assert.Single(definition.Metadata);
        Assert.True(definition.EnableCodeInterpreter);
    }
}
