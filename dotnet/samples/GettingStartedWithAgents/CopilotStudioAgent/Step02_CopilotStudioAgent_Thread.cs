// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Agents.CopilotStudio.Client;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Copilot;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.CopilotStudioAgents;

/// <summary>
/// Demonstrates how to use a <see cref="CopilotStudioAgent"/> with a persistent <see cref="CopilotStudioAgentThread"/>
/// to maintain conversation context across multiple user interactions. This sample shows how to send messages to the agent,
/// receive responses, and reset the conversation thread.
/// </summary>
public sealed class Step02_CopilotStudioAgent_Threads(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseCopilotStudioAgentThread()
    {
        CopilotStudioConnectionSettings settings = new(TestConfiguration.GetSection(nameof(CopilotStudioAgent)));
        CopilotClient client = CopilotStudioAgent.CreateClient(settings);
        CopilotStudioAgent agent = new(client);
        CopilotStudioAgentThread thread = new(client);

        await InvokeAgentAsync("Hello! Who are you? My name is John Doe.");
        await InvokeAgentAsync("What is the speed of light?");
        await InvokeAgentAsync("What did I just ask?");
        await InvokeAgentAsync("What is my name?");
        await InvokeAgentAsync("RESET");
        await InvokeAgentAsync("Yes");
        await InvokeAgentAsync("What is my name?");

        // Local function to invoke agent and display the response.
        async Task InvokeAgentAsync(string input)
        {
            Console.WriteLine($"\n# {AuthorRole.User}: {input}");

            await foreach (ChatMessageContent response in agent.InvokeAsync(input, thread))
            {
                WriteAgentChatMessage(response);
            }
        }
    }
}
