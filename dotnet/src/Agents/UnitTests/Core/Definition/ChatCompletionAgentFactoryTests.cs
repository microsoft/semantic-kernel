// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Definition;

/// <summary>
/// Unit tests for <see cref="ChatCompletionAgentFactory"/>.
/// </summary>
public class ChatCompletionAgentFactoryTests
{
    /// <summary>
    /// Verify can create an instance of <see cref="Agent"/> using <see cref="ChatCompletionAgentFactory"/>
    /// </summary>
    [Fact]
    public async Task VerifyCanCreateChatCompletionAgentAsync()
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
                Id = "gpt-4o-mini"
            }
        };
        ChatCompletionAgentFactory factory = new();
        Kernel kernel = new();

        // Act
        var agent = await factory.CreateAsync(kernel, agentDefinition);

        // Assert
        Assert.NotNull(agent);
        Assert.Equal(agentDefinition.Name, agent.Name);
        Assert.Equal(agentDefinition.Description, agent.Description);
        Assert.Equal(agentDefinition.Instructions, agent.Instructions);
        Assert.Equal(kernel, agent.Kernel);
    }
}
