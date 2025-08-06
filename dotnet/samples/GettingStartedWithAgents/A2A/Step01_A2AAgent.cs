// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using A2A;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;

namespace GettingStarted.A2A;

/// <summary>
/// This example demonstrates similarity between using <see cref="A2AAgent"/>
/// and other agent types.
/// </summary>
public class Step01_A2AAgent(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseA2AAgent()
    {
        // Create an A2A agent instance
        var url = TestConfiguration.A2A.AgentUrl;
        using var httpClient = CreateHttpClient();
        var client = new A2AClient(url, httpClient);
        var cardResolver = new A2ACardResolver(url, httpClient);
        var agentCard = await cardResolver.GetAgentCardAsync();
        Console.WriteLine(JsonSerializer.Serialize(agentCard, s_jsonSerializerOptions));
        var agent = new A2AAgent(client, agentCard);

        // Invoke the A2A agent
        await foreach (AgentResponseItem<ChatMessageContent> response in agent.InvokeAsync("List the latest invoices for Contoso?"))
        {
            this.WriteAgentChatMessage(response);
        }
    }

    [Fact]
    public async Task UseA2AAgentStreaming()
    {
        // Create an A2A agent instance
        var url = TestConfiguration.A2A.AgentUrl;
        using var httpClient = CreateHttpClient();
        var client = new A2AClient(url, httpClient);
        var cardResolver = new A2ACardResolver(url, httpClient);
        var agentCard = await cardResolver.GetAgentCardAsync();
        Console.WriteLine(JsonSerializer.Serialize(agentCard, s_jsonSerializerOptions));
        var agent = new A2AAgent(client, agentCard);

        // Invoke the A2A agent
        var responseItems = agent.InvokeStreamingAsync("List the latest invoices for Contoso?");
        await WriteAgentStreamMessageAsync(responseItems);
    }

    #region private
    private bool EnableLogging { get; set; } = false;

    private HttpClient CreateHttpClient()
    {
        if (this.EnableLogging)
        {
            var handler = new LoggingHandler(new HttpClientHandler(), this.Output);
            return new HttpClient(handler);
        }

        return new HttpClient();
    }

    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new() { WriteIndented = true };
    #endregion
}
