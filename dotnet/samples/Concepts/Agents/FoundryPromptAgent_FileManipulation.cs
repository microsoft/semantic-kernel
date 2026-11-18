// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects.Agents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;
using OpenAI.Responses;
using Resources;

namespace Agents;

/// <summary>
/// Demonstrate using code-interpreter to manipulate and generate csv files with a Microsoft Foundry Prompt Agent.
/// </summary>
public class FoundryPromptAgent_FileManipulation(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    [Fact]
    public async Task AnalyzeCSVFileUsingFoundryPromptAgentAsync()
    {
        await using Stream stream = EmbeddedResource.ReadStream("sales.csv")!;
        OpenAIFile file = await this.UploadFileAsync(stream, "sales.csv");

        // Define the Prompt Agent with the code-interpreter tool, which can read the uploaded file.
        DeclarativeAgentDefinition definition = new(DeploymentName);
        definition.Tools.Add(
            ResponseTool.CreateCodeInterpreterTool(
                new CodeInterpreterToolContainer(
                    CodeInterpreterToolContainerConfiguration.CreateAutomaticContainerConfiguration([file.Id]))));
        ProjectsAgentVersion promptAgent = await this.CreatePromptAgentAsync("Analyst", definition);

        // Create the agent
        ChatCompletionAgent agent =
            new()
            {
                Kernel = this.CreateKernel(promptAgent),
            };
        AgentThread? agentThread = null;

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Which segment had the most sales?");
            await InvokeAgentAsync("List the top 5 countries that generated the most profit.");
            await InvokeAgentAsync("Create a tab delimited file report of profit by each country per month.");
        }
        finally
        {
            if (agentThread is not null)
            {
                await agentThread.DeleteAsync();
            }

            await this.DeletePromptAgentAsync(promptAgent);
            await this.FileClient.DeleteFileAsync(file.Id);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(message);

            await foreach (AgentResponseItem<ChatMessageContent> response in agent.InvokeAsync(message, agentThread))
            {
                this.WriteAgentChatMessage(response);
                await this.DownloadGeneratedFilesAsync(response);

                agentThread = response.Thread;
            }
        }
    }
}
