// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Memory;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithMemoryConformance;

public class ChatCompletionAgentWithMemoryTests() : AgentWithMemoryTests<ChatCompletionAgentFixture>(() => new ChatCompletionAgentFixture())
{
    [Fact]
    public virtual async Task MemoryComponentCapturesMemoriesFromUserInputAsync()
    {
        // Arrange
        var agent = this.Fixture.Agent;
        var memoryComponent = new UserPreferencesMemoryComponent(this.Fixture.Agent.Kernel);

        var agentThread1 = new ChatHistoryAgentThread();
        agentThread1.ThreadExtensionsManager.RegisterThreadExtension(memoryComponent);

        var agentThread2 = new ChatHistoryAgentThread();
        agentThread2.ThreadExtensionsManager.RegisterThreadExtension(memoryComponent);

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
