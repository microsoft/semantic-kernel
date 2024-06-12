// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Experimental.Agents;

namespace Agents;

// ReSharper disable once InconsistentNaming
/// <summary>
/// Showcase usage of code_interpreter and retrieval tools.
/// </summary>
public sealed class Legacy_AgentCharts(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Specific model is required that supports agents and parallel function calling.
    /// Currently this is limited to Open AI hosted services.
    /// </summary>
    private const string OpenAIFunctionEnabledModel = "gpt-4-1106-preview";

    /// <summary>
    /// Flag to force usage of OpenAI configuration if both <see cref="TestConfiguration.OpenAI"/>
    /// and <see cref="TestConfiguration.AzureOpenAI"/> are defined.
    /// If 'false', Azure takes precedence.
    /// </summary>
    private new const bool ForceOpenAI = false;

    /// <summary>
    /// Create a chart and retrieve by file_id.
    /// </summary>
    [Fact(Skip = "Launches external processes")]
    public async Task CreateChartAsync()
    {
        Console.WriteLine("======== Using CodeInterpreter tool ========");

        var fileService = CreateFileService();

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
                    Console.WriteLine($"# {message.Role}: {message.Content}");
                    Console.WriteLine($"# {message.Role}: {path}");
                    var content = await fileService.GetFileContentAsync(message.Content);
                    await using var outputStream = File.OpenWrite(filename);
                    await outputStream.WriteAsync(content.Data!.Value);
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

    private static OpenAIFileService CreateFileService()
    {
        return
            ForceOpenAI || string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.Endpoint) ?
                new OpenAIFileService(TestConfiguration.OpenAI.ApiKey) :
                new OpenAIFileService(new Uri(TestConfiguration.AzureOpenAI.Endpoint), apiKey: TestConfiguration.AzureOpenAI.ApiKey);
    }

    private static AgentBuilder CreateAgentBuilder()
    {
        return
            ForceOpenAI || string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.Endpoint) ?
                new AgentBuilder().WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey) :
                new AgentBuilder().WithAzureOpenAIChatCompletion(TestConfiguration.AzureOpenAI.Endpoint, TestConfiguration.AzureOpenAI.ChatDeploymentName, TestConfiguration.AzureOpenAI.ApiKey);
    }
}
