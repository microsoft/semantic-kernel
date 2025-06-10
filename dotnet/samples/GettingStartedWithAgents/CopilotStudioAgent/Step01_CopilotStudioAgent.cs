// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Agents.CopilotStudio.Client;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Copilot;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.CopilotStudioAgents;

/// <summary>
/// Demonstrates how to use the <see cref="CopilotStudioAgent"/> to interact with a Copilot Agent service.
/// This sample shows how to create a CopilotStudioAgent, send user messages, and display the agent's responses.
/// </summary>
public sealed class Step01_CopilotStudioAgent(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseCopilotStudioAgent()
    {
        CopilotStudioConnectionSettings settings = new(TestConfiguration.GetSection(nameof(CopilotStudioAgent)));
        CopilotClient client = CopilotStudioAgent.CreateClient(settings);
        CopilotStudioAgent agent = new(client);

        await InvokeAgentAsync("Why is the sky blue?");
        await InvokeAgentAsync("What is the speed of light?");

        // Local function to invoke agent and display the response.
        async Task InvokeAgentAsync(string input)
        {
            Console.WriteLine($"\n# {AuthorRole.User}: {input}");

            await foreach (ChatMessageContent response in agent.InvokeAsync(input))
            {
                WriteAgentChatMessage(response);
            }
        }
    }
}
