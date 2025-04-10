// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI.Extensions;

/// <summary>
/// Unit tests for YamlAgentDefinitionExtensions
/// </summary>
public class AgentDefinitionExtensionsTests
{
    /// <summary>
    /// Verify CreateAssistantCreationOptions
    /// </summary>
    [Fact]
    public void VerifyCreateAssistantCreationOptions()
    {
        // Arrange
        AgentDefinition agentDefinition = new()
        {
            Type = OpenAIAssistantAgentFactory.OpenAIAssistantAgentType,
            Name = "OpenAIAssistantAgent",
            Description = "OpenAIAssistantAgent Description",
            Instructions = "OpenAIAssistantAgent Instructions",
            Model = new()
            {
                Id = "gpt-4o-mini"
            },
            Tools = [
                new AgentToolDefinition()
                {
                    Id = "tool1",
                    Type = "code_interpreter",
                },
            ]
        };

        // Act
        var creationOptions = agentDefinition.CreateAssistantCreationOptions();

        // Assert
        Assert.NotNull(creationOptions);
        Assert.Equal(agentDefinition.Name, creationOptions.Name);
        Assert.Equal(agentDefinition.Description, creationOptions.Description);
        Assert.Equal(agentDefinition.Instructions, creationOptions.Instructions);
        Assert.Single(creationOptions.Tools);
    }

    /// <summary>
    /// Verify GetCodeInterpreterFileIds
    /// </summary>
    [Fact]
    public void VerifyGetCodeInterpreterFileIds()
    {
        // Arrange
        var fileIds = new List<string>(["file1", "file2"]);
        var options = new Dictionary<string, object?>
        {
            { "file_ids", fileIds }
        };
        AgentDefinition agentDefinition = new()
        {
            Tools = [
                new AgentToolDefinition()
                {
                    Id = "tool1",
                    Type = "code_interpreter",
                    Options = options,
                },
            ]
        };

        // Act
        var interpreterFileIds = agentDefinition.GetCodeInterpreterFileIds();

        // Assert
        Assert.NotNull(interpreterFileIds);
        Assert.Equal(2, interpreterFileIds.Count);
    }

    /// <summary>
    /// Verify GetVectorStoreId
    /// </summary>
    [Fact]
    public void VerifyGetVectorStoreId()
    {
        // Arrange
        AgentDefinition agentDefinition = new()
        {
        };

        // Act
        var vectorId = agentDefinition.GetVectorStoreId();

        // Assert
        Assert.Null(vectorId);
    }

    /// <summary>
    /// Verify GetMetadata
    /// </summary>
    [Fact]
    public void VerifyGetMetadata()
    {
        // Arrange
        AgentDefinition agentDefinition = new()
        {
        };

        // Act
        var metadata = agentDefinition.GetMetadata();

        // Assert
        Assert.Null(metadata);
    }
}
