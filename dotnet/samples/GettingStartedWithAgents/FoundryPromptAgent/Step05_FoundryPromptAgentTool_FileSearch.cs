// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.Projects.Agents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;
using OpenAI.Responses;
using OpenAI.VectorStores;
using Resources;

namespace GettingStarted.FoundryPromptAgents;

/// <summary>
/// Demonstrate using a Microsoft Foundry Prompt Agent with file search.
/// </summary>
public class Step05_FoundryPromptAgentTool_FileSearch(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    [Fact]
    public async Task UseFileSearchToolWithFoundryPromptAgent()
    {
        // Upload file - Using a table of fictional employees.
        await using Stream stream = EmbeddedResource.ReadStream("employees.pdf")!;
        OpenAIFile file = await this.UploadFileAsync(stream, "employees.pdf");

        // Create a vector-store
        VectorStore vectorStore =
            (await this.VectorStoreClient.CreateVectorStoreAsync(
                new VectorStoreCreationOptions()
                {
                    Name = "step5_employees",
                    FileIds = { file.Id },
                })).Value;

        // Define the Prompt Agent with the file-search tool associated with the vector-store.
        DeclarativeAgentDefinition definition = new(DeploymentName);
        definition.Tools.Add(ResponseTool.CreateFileSearchTool([vectorStore.Id]));
        ProjectsAgentVersion promptAgent = await this.CreatePromptAgentAsync("Search", definition);

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
            await InvokeAgentAsync("Who is the youngest employee?");
            await InvokeAgentAsync("Who works in sales?");
            await InvokeAgentAsync("I have a customer request, who can help me?");
        }
        finally
        {
            await thread.DeleteAsync();
            await this.DeletePromptAgentAsync(promptAgent);
            await this.VectorStoreClient.DeleteVectorStoreAsync(vectorStore.Id);
            await this.FileClient.DeleteFileAsync(file.Id);
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
