// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Memory;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithStatePartConformance;

public class AzureAIAgentWithStatePartTests() : AgentWithStatePartTests<AzureAIAgentFixture>(() => new AzureAIAgentFixture())
{
    [Fact(Skip = "For manual verification")]
    public virtual async Task Mem0ComponentCapturesMemoriesFromUserInputAsync()
    {
        // Arrange
        var agent = this.Fixture.Agent;

        using var httpClient = new HttpClient();
        httpClient.BaseAddress = new Uri("https://api.mem0.ai");
        httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Token", "m0-uWa1CXDyO9PpotOFMUfI9WzZOwAqJjZwH3GTKgqa");

        var mem0Component = new Mem0MemoryComponent(httpClient, new() { UserId = "U1" });

        var agentThread1 = new AzureAIAgentThread(this.Fixture.AgentsClient);
        agentThread1.StateParts.Add(mem0Component);

        var agentThread2 = new AzureAIAgentThread(this.Fixture.AgentsClient);
        agentThread2.StateParts.Add(mem0Component);

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
