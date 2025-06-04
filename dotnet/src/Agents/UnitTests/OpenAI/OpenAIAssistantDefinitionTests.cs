// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel.Agents.OpenAI;
using SemanticKernel.Agents.UnitTests.Test;
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
        // Arrange
        OpenAIAssistantDefinition definition = new("testmodel");

        // Assert
        Assert.Equal(string.Empty, definition.Id);
        Assert.Equal("testmodel", definition.ModelId);
        Assert.Null(definition.Name);
        Assert.Null(definition.Instructions);
        Assert.Null(definition.Description);
        Assert.Null(definition.Metadata);
        Assert.Null(definition.ExecutionOptions);
        Assert.Null(definition.Temperature);
        Assert.Null(definition.TopP);
        Assert.False(definition.EnableFileSearch);
        Assert.Null(definition.VectorStoreId);
        Assert.Null(definition.CodeInterpreterFileIds);
        Assert.False(definition.EnableCodeInterpreter);
        Assert.False(definition.EnableJsonResponse);

        // Act and Assert
        ValidateSerialization(definition);
    }

    /// <summary>
    /// Verify initialization.
    /// </summary>
    [Fact]
    public void VerifyOpenAIAssistantDefinitionAssignment()
    {
        // Arrange
        OpenAIAssistantDefinition definition =
            new("testmodel")
            {
                Id = "testid",
                Name = "testname",
                Instructions = "testinstructions",
                Description = "testdescription",
                EnableFileSearch = true,
                VectorStoreId = "#vs",
                Metadata = new Dictionary<string, string>() { { "a", "1" } },
                Temperature = 2,
                TopP = 0,
                ExecutionOptions =
                    new()
                    {
                        AdditionalInstructions = "test instructions",
                        MaxCompletionTokens = 1000,
                        MaxPromptTokens = 1000,
                        ParallelToolCallsEnabled = false,
                        TruncationMessageCount = 12,
                    },
                CodeInterpreterFileIds = ["file1"],
                EnableCodeInterpreter = true,
                EnableJsonResponse = true,
            };

        // Assert
        Assert.Equal("testid", definition.Id);
        Assert.Equal("testname", definition.Name);
        Assert.Equal("testmodel", definition.ModelId);
        Assert.Equal("testinstructions", definition.Instructions);
        Assert.Equal("testdescription", definition.Description);
        Assert.True(definition.EnableFileSearch);
        Assert.Equal("#vs", definition.VectorStoreId);
        Assert.Equal(2, definition.Temperature);
        Assert.Equal(0, definition.TopP);
        Assert.NotNull(definition.ExecutionOptions);
        Assert.Equal("test instructions", definition.ExecutionOptions.AdditionalInstructions);
        Assert.Equal(1000, definition.ExecutionOptions.MaxCompletionTokens);
        Assert.Equal(1000, definition.ExecutionOptions.MaxPromptTokens);
        Assert.Equal(12, definition.ExecutionOptions.TruncationMessageCount);
        Assert.False(definition.ExecutionOptions.ParallelToolCallsEnabled);
        Assert.Single(definition.Metadata);
        Assert.Single(definition.CodeInterpreterFileIds);
        Assert.True(definition.EnableCodeInterpreter);
        Assert.True(definition.EnableJsonResponse);

        // Act and Assert
        ValidateSerialization(definition);
    }

    /// <summary>
    /// Verify TemplateFactoryFormat.
    /// </summary>
    [Fact]
    public void VerifyOpenAIAssistantDefinitionTemplateFactoryFormat()
    {
        // Arrange
        OpenAIAssistantDefinition definition = new("testmodel");

        // Assert
        Assert.Null(definition.TemplateFactoryFormat);

        // Act
        definition = new("testmodel")
        {
            Metadata = new Dictionary<string, string>() { { OpenAIAssistantAgent.TemplateMetadataKey, "testformat" } }
        };

        // Assert
        Assert.Equal("testformat", definition.TemplateFactoryFormat);
    }

    private static void ValidateSerialization(OpenAIAssistantDefinition source)
    {
        string json = JsonSerializer.Serialize(source);

        OpenAIAssistantDefinition? target = JsonSerializer.Deserialize<OpenAIAssistantDefinition>(json);

        Assert.NotNull(target);
        Assert.Equal(source.Id, target.Id);
        Assert.Equal(source.Name, target.Name);
        Assert.Equal(source.ModelId, target.ModelId);
        Assert.Equal(source.Instructions, target.Instructions);
        Assert.Equal(source.Description, target.Description);
        Assert.Equal(source.EnableFileSearch, target.EnableFileSearch);
        Assert.Equal(source.VectorStoreId, target.VectorStoreId);
        Assert.Equal(source.Temperature, target.Temperature);
        Assert.Equal(source.TopP, target.TopP);
        Assert.Equal(source.EnableFileSearch, target.EnableFileSearch);
        Assert.Equal(source.VectorStoreId, target.VectorStoreId);
        Assert.Equal(source.EnableCodeInterpreter, target.EnableCodeInterpreter);
        Assert.Equal(source.ExecutionOptions?.MaxCompletionTokens, target.ExecutionOptions?.MaxCompletionTokens);
        Assert.Equal(source.ExecutionOptions?.MaxPromptTokens, target.ExecutionOptions?.MaxPromptTokens);
        Assert.Equal(source.ExecutionOptions?.TruncationMessageCount, target.ExecutionOptions?.TruncationMessageCount);
        Assert.Equal(source.ExecutionOptions?.ParallelToolCallsEnabled, target.ExecutionOptions?.ParallelToolCallsEnabled);
        AssertCollection.Equal(source.CodeInterpreterFileIds, target.CodeInterpreterFileIds);
        AssertCollection.Equal(source.Metadata, target.Metadata);
    }
}
