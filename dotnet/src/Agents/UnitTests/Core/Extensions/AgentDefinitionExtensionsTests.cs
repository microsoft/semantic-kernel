// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Extensions;

/// <summary>
/// Unit tests for <see cref="AgentDefinitionExtensions"/>.
/// </summary>
public class AgentDefinitionExtensionsTests
{
    /// <summary>
    /// Verify GetDefaultKernelArguments
    /// </summary>
    [Fact]
    public void VerifyGetDefaultKernelArguments()
    {
        // Arrange
        Kernel kernel = new();
        AgentDefinition agentDefinition = new()
        {
            Inputs = new Dictionary<string, AgentInput>
            {
                ["Input1"] = new() { Name = "Input1", Required = false, Default = "Default1" },
                ["Input2"] = new() { Name = "Input2", Required = true, Default = "Default2" }
            },
        };

        // Act
        var defaultArgs = agentDefinition.GetDefaultKernelArguments(kernel);

        // Assert
        Assert.NotNull(defaultArgs);
        Assert.Equal(2, defaultArgs.Count);
        Assert.Equal("Default1", defaultArgs["Input1"]);
        Assert.Equal("Default2", defaultArgs["Input2"]);
    }

    /// <summary>
    /// Verify GetFirstToolDefinition
    /// </summary>
    [Fact]
    public void VerifyGetFirstToolDefinition()
    {
        // Arrange
        AgentDefinition agentDefinition = new()
        {
            Tools =
            [
                new AgentToolDefinition { Type = "code_interpreter", Id = "Tool1" },
                new AgentToolDefinition { Type = "file_search", Id = "Tool2" },
            ],
        };

        // Act & Assert
        Assert.NotNull(agentDefinition.GetFirstToolDefinition("code_interpreter"));
        Assert.NotNull(agentDefinition.GetFirstToolDefinition("file_search"));
        Assert.Null(agentDefinition.GetFirstToolDefinition("openai"));
    }

    /// <summary>
    /// Verify HasToolType
    /// </summary>
    [Fact]
    public void VerifyIsEnableCodeInterpreter()
    {
        // Arrange
        AgentDefinition agentDefinition = new()
        {
            Tools =
            [
                new AgentToolDefinition { Type = "code_interpreter", Id = "Tool1" },
            ],
        };

        // Act & Assert
        Assert.True(agentDefinition.HasToolType("code_interpreter"));
    }

    /// <summary>
    /// Verify IsEnableFileSearch
    /// </summary>
    [Fact]
    public void VerifyIsEnableFileSearch()
    {
        // Arrange
        AgentDefinition agentDefinition = new()
        {
            Tools =
            [
                new AgentToolDefinition { Type = "file_search", Id = "Tool2" },
            ],
        };

        // Act & Assert
        Assert.True(agentDefinition.HasToolType("file_search"));
    }
}
