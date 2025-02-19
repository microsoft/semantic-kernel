// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;
using Agent = Azure.AI.Projects.Agent;

namespace Agents;

/// <summary>
/// Demonstrate using code-interpreter to manipulate and generate csv files with <see cref="AzureAIAgent"/> .
/// </summary>
public class AzureAIAgent_FileManipulation(ITestOutputHelper output) : BaseAzureAgentTest(output)
{
    [Fact]
    public async Task AnalyzeCSVFileUsingAzureAIAgentAsync()
    {
        await using Stream stream = EmbeddedResource.ReadStream("sales.csv")!;
        AgentFile fileInfo = await this.AgentsClient.UploadFileAsync(stream, AgentFilePurpose.Agents, "sales.csv");

        // Define the agent
        Agent definition = await this.AgentsClient.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId,
            tools: [new CodeInterpreterToolDefinition()],
            toolResources:
                new()
                {
                    CodeInterpreter = new()
                    {
                        FileIds = { fileInfo.Id },
                    }
                });
        AzureAIAgent agent = new(definition, this.AgentsClient);

        // Create a chat for agent interaction.
        AgentGroupChat chat = new();

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Which segment had the most sales?");
            await InvokeAgentAsync("List the top 5 countries that generated the most profit.");
            await InvokeAgentAsync("Create a tab delimited file report of profit by each country per month.");
        }
        finally
        {
            await this.AgentsClient.DeleteAgentAsync(agent.Id);
            await this.AgentsClient.DeleteFileAsync(fileInfo.Id);
            await chat.ResetAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            chat.AddChatMessage(new(AuthorRole.User, input));
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in chat.InvokeAsync(agent))
            {
                this.WriteAgentChatMessage(response);
                await this.DownloadContentAsync(response);
            }
        }
    }
}
