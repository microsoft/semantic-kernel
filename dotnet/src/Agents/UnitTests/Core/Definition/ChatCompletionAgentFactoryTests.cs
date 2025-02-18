// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Definition;

/// <summary>
/// Unit testing of <see cref="ChatCompletionAgentFactory"/>.
/// </summary>
public class ChatCompletionAgentFactoryTests
{
    /// <summary>
    /// Verify can create an instance of <see cref="ChatCompletionAgent"/>.
    /// </summary>
    [Fact]
    public void VerifyCanCreateChatCompletionAgent()
    {
        // Arrange
        AgentDefinition agentDefinition = new()
        {
            Type = ChatCompletionAgentFactory.ChatCompletionAgentType,
            Name = "ChatCompletionAgent",
            Description = "ChatCompletionAgent Description",
            Instructions = "ChatCompletionAgent Instructions",
            Model = new()
            {
                Id = "gpt-4o-mini",
                Options = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }
            }
        };
        ChatCompletionAgentFactory factory = new();
        Kernel kernel = new();

        // Act
        var result = factory.TryCreate(kernel, agentDefinition, out var agent);

        // Assert
        Assert.True(result);
        Assert.NotNull(agent);
        Assert.Equal(agentDefinition.Name, agent.Name);
        Assert.Equal(agentDefinition.Description, agent.Description);
        Assert.Equal(agentDefinition.Instructions, agent.Instructions);
        Assert.Equal(kernel, agent.Kernel);
    }
}
