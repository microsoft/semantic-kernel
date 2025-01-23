// Copyright (c) Microsoft. All rights reserved.
using System.Diagnostics;
using System.IO;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;
using Resources;
using AzureAIP = Azure.AI.Projects;

namespace Agents;

/// <summary>
/// Demonstrate using code-interpreter to manipulate and generate csv files with <see cref="AzureAIAgent"/> .
/// </summary>
public class AzureAIAgent_FileManipulation(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task AnalyzeCSVFileUsingAzureAIAgentAsync()
    {
        AzureAIClientProvider clientProvider = this.GetAzureProvider();
        AzureAIP.AgentsClient client = clientProvider.Client.GetAgentsClient();

        await using Stream stream = EmbeddedResource.ReadStream("sales.csv")!;
        AzureAIP.AgentFile fileInfo = await client.UploadFileAsync(stream, AzureAIP.AgentFilePurpose.Agents, "sales.csv");

        // Define the agent
        AzureAIP.Agent definition = await client.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId,
            tools: [new AzureAIP.CodeInterpreterToolDefinition()],
            toolResources:
                new()
                {
                    CodeInterpreter = new()
                    {
                        FileIds = { fileInfo.Id },
                    }
                });
        AzureAIAgent agent = new(definition, clientProvider);

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
            await client.DeleteAgentAsync(agent.Id);
            await client.DeleteFileAsync(fileInfo.Id);
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
                await this.DownloadContentAsync(client, response);
            }
        }
    }

    private async Task DownloadContentAsync(AzureAIP.AgentsClient client, ChatMessageContent message)
    {
        foreach (KernelContent item in message.Items)
        {
            if (item is AnnotationContent annotation)
            {
                await this.DownloadFileAsync(client, annotation.FileId!);
            }
        }
    }

    private async Task DownloadFileAsync(AzureAIP.AgentsClient client, string fileId, bool launchViewer = false)
    {
        AzureAIP.AgentFile fileInfo = client.GetFile(fileId);
        if (fileInfo.Purpose == AzureAIP.AgentFilePurpose.AgentsOutput)
        {
            string filePath = Path.Combine(Path.GetTempPath(), Path.GetFileName(fileInfo.Filename));
            if (launchViewer)
            {
                filePath = Path.ChangeExtension(filePath, ".png");
            }

            BinaryData content = await client.GetFileContentAsync(fileId);
            File.WriteAllBytes(filePath, content.ToArray());
            Console.WriteLine($"  File #{fileId} saved to: {filePath}");

            if (launchViewer)
            {
                Process.Start(
                    new ProcessStartInfo
                    {
                        FileName = "cmd.exe",
                        Arguments = $"/C start {filePath}"
                    });
            }
        }
    }
}
