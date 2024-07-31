// Copyright (c) Microsoft. All rights reserved.
using System.Diagnostics;
using System.Threading;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;

namespace Agents;

/// <summary>
/// Demonstrate using code-interpreter with <see cref="OpenAIAssistantAgent"/> to
/// produce image content displays the requested charts.
/// </summary>
public class OpenAIAssistant_ChartMaker(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Target Open AI services.
    /// </summary>
    protected override bool ForceOpenAI => true;

    private const string AgentName = "ChartMaker";
    private const string AgentInstructions = "Create charts as requested without explanation.";

    [Fact]
    public async Task GenerateChartWithOpenAIAssistantAgentAsync()
    {
        OpenAIServiceConfiguration config = GetOpenAIConfiguration();

        FileClient fileClient = config.CreateFileClient();

        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                config,
                new()
                {
                    Instructions = AgentInstructions,
                    Name = AgentName,
                    EnableCodeInterpreter = true,
                    ModelId = this.Model,
                });

        // Create a chat for agent interaction.
        AgentGroupChat chat = new();

        // Respond to user input
        try
        {
            await InvokeAgentAsync(
                """
                Display this data using a bar-chart:

                Banding  Brown Pink Yellow  Sum
                X00000   339   433     126  898
                X00300    48   421     222  691
                X12345    16   395     352  763
                Others    23   373     156  552
                Sum      426  1622     856 2904
                """);

            await InvokeAgentAsync("Can you regenerate this same chart using the category names as the bar colors?");
            await InvokeAgentAsync("Perfect, can you regenerate this as a line chart?");
        }
        finally
        {
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));

            Console.WriteLine($"# {AuthorRole.User}: '{input}'");

            await foreach (var message in chat.InvokeAsync(agent))
            {
                if (!string.IsNullOrWhiteSpace(message.Content))
                {
                    Console.WriteLine($"# {message.Role} - {message.AuthorName ?? "*"}: '{message.Content}'");
                }

                foreach (var fileReference in message.Items.OfType<FileReferenceContent>())
                {
                    Console.WriteLine($"# {message.Role} - {message.AuthorName ?? "*"}: @{fileReference.FileId}");

                    string downloadPath = await DownloadFileContentAsync(fileReference.FileId);

                    Console.WriteLine($"# {message.Role}: @{fileReference.FileId} downloaded to {downloadPath}");
                }
            }
        }

        async Task<string> DownloadFileContentAsync(string fileId)
        {
            string filePath = Path.Combine(Environment.CurrentDirectory, $"{fileId}.jpg");
            BinaryData content = await fileClient.DownloadFileAsync(fileId);
            await using var outputStream = File.OpenWrite(filePath);
            await outputStream.WriteAsync(content.ToArray());

            Process.Start(
                new ProcessStartInfo
                {
                    FileName = "cmd.exe",
                    Arguments = $"/C start {filePath}"
                });

            return filePath;
        }
    }

    private OpenAIServiceConfiguration GetOpenAIConfiguration()
        =>
            this.UseOpenAIConfig ?
                OpenAIServiceConfiguration.ForOpenAI(this.ApiKey) :
                OpenAIServiceConfiguration.ForAzureOpenAI(this.ApiKey, new Uri(this.Endpoint!));
}
