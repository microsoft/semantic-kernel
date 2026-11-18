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
/// Demonstrate <see cref="ChatCompletionAgent"/> agent interacts with
/// an agent that uses a Microsoft Foundry Prompt Agent when it produces file output.
/// </summary>
public class MixedChat_Files(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    private const string SummaryInstructions = "Summarize the entire conversation for the user in natural language.";

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task AnalyzeFileAndGenerateReport(bool useChatClient)
    {
        // Define the agents
        ChatCompletionAgent summaryAgent =
            new()
            {
                Instructions = SummaryInstructions,
                Kernel = this.CreateKernelWithChatCompletion(useChatClient, out var chatClient),
            };

        await using Stream stream = EmbeddedResource.ReadStream("30-user-context.txt")!;
        OpenAIFile file = await this.UploadFileAsync(stream, "30-user-context.txt");

        // Define the Prompt Agent with the code-interpreter tool, which can read the uploaded file.
        DeclarativeAgentDefinition definition = new(DeploymentName);
        definition.Tools.Add(
            ResponseTool.CreateCodeInterpreterTool(
                new CodeInterpreterToolContainer(
                    CodeInterpreterToolContainerConfiguration.CreateAutomaticContainerConfiguration([file.Id]))));
        ProjectsAgentVersion promptAgent = await this.CreatePromptAgentAsync("Analyst", definition);

        // Create the agent that uses the Prompt Agent
        ChatCompletionAgent analystAgent =
            new()
            {
                Kernel = this.CreateKernel(promptAgent),
            };

        // Create a chat for agent interaction.
        AgentGroupChat chat = new();

        // Respond to user input
        try
        {
            await InvokeAgentAsync(
                analystAgent,
                """
                Create a tab delimited file report of the ordered (descending) frequency distribution
                of words in the file '30-user-context.txt' for any words used more than once.
                """);
            await InvokeAgentAsync(summaryAgent);
        }
        finally
        {
            await this.DeletePromptAgentAsync(promptAgent);
            await this.FileClient.DeleteFileAsync(file.Id);
        }

        chatClient?.Dispose();

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(Agent agent, string? input = null)
        {
            if (!string.IsNullOrWhiteSpace(input))
            {
                ChatMessageContent message = new(AuthorRole.User, input);
                chat.AddChatMessage(new(AuthorRole.User, input));
                this.WriteAgentChatMessage(message);
            }

            await foreach (ChatMessageContent response in chat.InvokeAsync(agent))
            {
                this.WriteAgentChatMessage(response);
                await this.DownloadGeneratedFilesAsync(response);
            }
        }
    }
}
