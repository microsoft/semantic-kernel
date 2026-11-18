// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects.Agents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Responses;

namespace Agents;

/// <summary>
/// Demonstrate using code-interpreter with a Microsoft Foundry Prompt Agent to
/// produce image content displays the requested charts.
/// </summary>
public class FoundryPromptAgent_ChartMaker(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    [Fact]
    public async Task GenerateChartWithFoundryPromptAgentAsync()
    {
        // Define the Prompt Agent with the code-interpreter tool.
        DeclarativeAgentDefinition definition = new(DeploymentName)
        {
            Instructions = "Create charts as requested without explanation.",
        };
        definition.Tools.Add(
            ResponseTool.CreateCodeInterpreterTool(
                new CodeInterpreterToolContainer(
                    CodeInterpreterToolContainerConfiguration.CreateAutomaticContainerConfiguration())));
        ProjectsAgentVersion promptAgent = await this.CreatePromptAgentAsync("ChartMaker", definition);

        // Create the agent
        ChatCompletionAgent agent =
            new()
            {
                Name = "ChartMaker",
                Kernel = this.CreateKernel(promptAgent),
            };
        AgentThread? agentThread = null;

        // Respond to user input
        try
        {
            await InvokeAgentAsync(
                """
                Display this data using a bar-chart (not stacked):

                Banding  Brown Pink Yellow  Sum
                X00000   339   433     126  898
                X00300    48   421     222  691
                X12345    16   395     352  763
                Others    23   373     156  552
                Sum      426  1622     856 2904
                """);

            await InvokeAgentAsync("Can you regenerate this same chart using the category names as the bar colors?");
        }
        finally
        {
            if (agentThread is not null)
            {
                await agentThread.DeleteAsync();
            }

            await this.DeletePromptAgentAsync(promptAgent);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(message);

            await foreach (AgentResponseItem<ChatMessageContent> response in agent.InvokeAsync(message, agentThread))
            {
                this.WriteAgentChatMessage(response);
                await this.DownloadGeneratedFilesAsync(response, launchViewer: true);

                agentThread = response.Thread;
            }
        }
    }
}
