// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Plugins;

namespace GettingStarted.OpenAIResponseAgents;

/// <summary>
/// This example demonstrates how perform function calling with a <see cref="OpenAIResponseAgent"/>.
/// </summary>
public class Step03_OpenAIResponseAgent_FunctionCalling(ITestOutputHelper output) : BaseResponsesAgentTest(output)
{
    [Fact]
    public async Task UseOpenAIResponseAgentWithFunctionCallingAsync()
    {
        // Define the agent
        OpenAIResponseAgent agent = new(this.Client)
        {
            Name = "Host",
            Instructions = "Answer questions about the menu.",
            Plugins = [
                KernelPluginFactory.CreateFromType<MenuPlugin>(),
            ]
        };

        // Invoke the agent and output the response
        var responseItems = agent.InvokeAsync("What is the special soup and its price?");
        await foreach (ChatMessageContent responseItem in responseItems)
        {
            WriteAgentChatMessage(responseItem);
        }
    }
}
