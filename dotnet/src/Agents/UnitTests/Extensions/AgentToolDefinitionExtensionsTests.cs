// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Extensions;

/// <summary>
/// Unit testing of <see cref="AgentToolDefinitionExtensions"/>.
/// </summary>
public class AgentToolDefinitionExtensionsTests
{
    /// <summary>
    /// Verify GetOption.
    /// </summary>
    [Fact]
    public void VerifyGetOption()
    {
        // Arrange
        var agentToolDefinition = new AgentToolDefinition()
        {
            Type = "function",
            Id = "MyPlugin.Function1",
            Options = new Dictionary<string, object?>()
            {
                { "null", null },
                { "string", "string" },
                { "int", 1 },
                { "array", new string[] { "1", "2", "3" } },
            }
        };

        // Act & Assert
        Assert.Null(agentToolDefinition.GetOption<string>("null"));
        Assert.Equal("string", agentToolDefinition.GetOption<string>("string"));
        Assert.Equal(1, agentToolDefinition.GetOption<int>("int"));
        Assert.Equal(new string[] { "1", "2", "3" }, agentToolDefinition.GetOption<string[]>("array"));
        Assert.Throws<InvalidCastException>(() => agentToolDefinition.GetOption<string[]>("string"));
        Assert.Throws<ArgumentNullException>(() => agentToolDefinition.GetOption<string>(null!));
    }
}
