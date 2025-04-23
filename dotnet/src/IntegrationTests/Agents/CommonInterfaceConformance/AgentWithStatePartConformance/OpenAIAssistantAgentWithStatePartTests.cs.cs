// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Memory;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithStatePartConformance;

public class OpenAIAssistantAgentWithMemoryTests() : AgentWithStatePartTests<OpenAIAssistantAgentFixture>(() => new OpenAIAssistantAgentFixture())
{
    [Fact]
    public virtual async Task MemoryComponentCapturesMemoriesFromUserInputAsync()
    {
        // Arrange
        var agent = this.Fixture.Agent;
        var memoryComponent = new UserFactsMemoryComponent(this.Fixture.Agent.Kernel);

        var agentThread1 = new OpenAIAssistantAgentThread(this.Fixture.AssistantClient);
        agentThread1.StateParts.Add(memoryComponent);

        var agentThread2 = new OpenAIAssistantAgentThread(this.Fixture.AssistantClient);
        agentThread2.StateParts.Add(memoryComponent);

        // Act
        var asyncResults1 = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "Hello, my name is Caoimhe."), agentThread1);
        var results1 = await asyncResults1.ToListAsync();

        var asyncResults2 = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "What is my name?."), agentThread2);
        var results2 = await asyncResults2.ToListAsync();

        // Assert
        Assert.Contains("Caoimhe", results2.First().Message.Content);

        // Cleanup
        await this.Fixture.DeleteThread(agentThread1);
        await this.Fixture.DeleteThread(agentThread2);
    }
}
