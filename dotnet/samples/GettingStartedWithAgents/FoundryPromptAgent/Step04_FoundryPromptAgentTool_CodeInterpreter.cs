// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects.Agents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Responses;

namespace GettingStarted.FoundryPromptAgents;

/// <summary>
/// Demonstrate using code-interpreter on a Microsoft Foundry Prompt Agent.
/// </summary>
public class Step04_FoundryPromptAgentTool_CodeInterpreter(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    [Fact]
    public async Task UseCodeInterpreterToolWithFoundryPromptAgent()
    {
        // Define the Prompt Agent with the code-interpreter tool.
        DeclarativeAgentDefinition definition = new(DeploymentName);
        definition.Tools.Add(
            ResponseTool.CreateCodeInterpreterTool(
                new CodeInterpreterToolContainer(
                    CodeInterpreterToolContainerConfiguration.CreateAutomaticContainerConfiguration())));
        ProjectsAgentVersion promptAgent = await this.CreatePromptAgentAsync("Coder", definition);

        // Create the agent
        ChatCompletionAgent agent =
            new()
            {
                Kernel = this.CreateKernel(promptAgent),
            };

        // Create a thread for the agent conversation.
        AgentThread thread = new ChatHistoryAgentThread();

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Use code to determine the values in the Fibonacci sequence that that are less then the value of 101?");
        }
        finally
        {
            await thread.DeleteAsync();
            await this.DeletePromptAgentAsync(promptAgent);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(message, thread))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }
}
