// Copyright (c) Microsoft. All rights reserved.
using System.Linq;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.AzureAI.Extensions;

/// <summary>
/// Unit tests for YamlAgentDefinitionExtensions
/// </summary>
public class AgentDefinitionExtensionsTests
{
    /// <summary>
    /// Verify GetAzureToolDefinitions
    /// </summary>
    [Fact]
    public void VerifyGetAzureToolDefinitions()
    {
        // Arrange
        AgentDefinition agentDefinition = new()
        {
            Tools = [
                new AgentToolDefinition()
                {
                    Id = "tool1",
                    Type = "code_interpreter",
                },
                new AgentToolDefinition()
                {
                    Id = "tool2",
                    Type = "file_search",
                },
            ]
        };

        // Act
        var toolDefinitions = agentDefinition.GetAzureToolDefinitions();

        // Assert
        Assert.NotNull(toolDefinitions);
        Assert.Equal(2, toolDefinitions.Count());
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
