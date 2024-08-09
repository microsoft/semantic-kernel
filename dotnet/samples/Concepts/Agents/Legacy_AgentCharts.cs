// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.Experimental.Agents;
using OpenAI;
using OpenAI.Files;

namespace Agents;

// ReSharper disable once InconsistentNaming
/// <summary>
/// Showcase usage of code_interpreter and retrieval tools.
/// </summary>
public sealed class Legacy_AgentCharts(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Create a chart and retrieve by file_id.
    /// </summary>
    [Fact]
    public async Task CreateChartAsync()
    {
        Console.WriteLine("======== Using CodeInterpreter tool ========");

        FileClient fileClient = CreateFileClient();

        var agent = await CreateAgentBuilder().WithCodeInterpreter().BuildAsync();

        try
        {
            var thread = await agent.NewThreadAsync();

            await InvokeAgentAsync(
                thread,
                "1-first", @"
Display this data using a bar-chart with no summation:

Banding  Brown Pink Yellow  Sum
X00000   339   433     126  898
X00300    48   421     222  691
X12345    16   395     352  763
Others    23   373     156  552
Sum      426  1622     856 2904
");
            await InvokeAgentAsync(thread, "2-colors", "Can you regenerate this same chart using the category names as the bar colors?");
            await InvokeAgentAsync(thread, "3-line", "Can you regenerate this as a line chart?");
        }
        finally
        {
            await agent.DeleteAsync();
        }

        async Task InvokeAgentAsync(IAgentThread thread, string imageName, string question)
        {
            await foreach (var message in thread.InvokeAsync(agent, question))
            {
                if (message.ContentType == ChatMessageType.Image)
                {
                    var filename = $"{imageName}.jpg";
                    var path = Path.Combine(Environment.CurrentDirectory, filename);
                    var fileId = message.Content;
                    Console.WriteLine($"# {message.Role}: {fileId}");
                    Console.WriteLine($"# {message.Role}: {path}");
                    BinaryData content = await fileClient.DownloadFileAsync(fileId);
                    File.WriteAllBytes(filename, content.ToArray());
                    Process.Start(
                        new ProcessStartInfo
                        {
                            FileName = "cmd.exe",
                            Arguments = $"/C start {path}"
                        });
                }
                else
                {
                    Console.WriteLine($"# {message.Role}: {message.Content}");
                }
            }

            Console.WriteLine();
        }
    }

    private FileClient CreateFileClient()

    {
        OpenAIClient client =
            this.ForceOpenAI || string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.Endpoint) ?
                new OpenAIClient(TestConfiguration.OpenAI.ApiKey) :
                new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAI.Endpoint), TestConfiguration.AzureOpenAI.ApiKey);

        return client.GetFileClient();
    }
#pragma warning restore CS0618 // Type or member is obsolete

    private AgentBuilder CreateAgentBuilder()
    {
        return
            this.ForceOpenAI || string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.Endpoint) ?
                new AgentBuilder().WithOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey) :
                new AgentBuilder().WithAzureOpenAIChatCompletion(TestConfiguration.AzureOpenAI.Endpoint, TestConfiguration.AzureOpenAI.ChatDeploymentName, TestConfiguration.AzureOpenAI.ApiKey);
    }
}
