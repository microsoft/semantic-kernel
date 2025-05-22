// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;
using SharpA2A.Core;

namespace GettingStarted.A2A;

/// <summary>
/// This example demonstrates similarity between using <see cref="A2AAgent"/>
/// and other agent types.
/// </summary>
public class Step01_A2AAgent(ITestOutputHelper output) : BaseAzureAgentTest(output)
{
    [Fact]
    public async Task UseA2AAgent()
    {
        // Create an A2A agent instance
        using var httpClient = new HttpClient
        {
            BaseAddress = new Uri(TestConfiguration.A2A.Agent)
        };
        var client = new A2AClient(httpClient);
        var cardResolver = new A2ACardResolver(httpClient);
        var agentCard = await cardResolver.GetAgentCardAsync();
        Console.WriteLine(JsonSerializer.Serialize(agentCard, s_jsonSerializerOptions));
        var agent = new A2AAgent(client, agentCard);

        // Invoke the A2A agent
        await foreach (AgentResponseItem<ChatMessageContent> response in agent.InvokeAsync("Hello"))
        {
            this.WriteAgentChatMessage(response);
        }
    }

    #region private
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new() { WriteIndented = true };
    #endregion
}
