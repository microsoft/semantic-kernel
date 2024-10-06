// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Experimental.Agents;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

// ReSharper disable once InconsistentNaming
/// <summary>
/// Showcase usage of code_interpreter and retrieval tools.
/// </summary>
public sealed class Example85_AgentCharts : BaseTest
{
    /// <summary>
    /// Specific model is required that supports agents and parallel function calling.
    /// Currently this is limited to Open AI hosted services.
    /// </summary>
    private const string OpenAIFunctionEnabledModel = "gpt-4-1106-preview";

    /// <summary>
    /// Create a chart and retrieve by file_id.
    /// </summary>
    [Fact(Skip = "Launches external processes")]
    public async Task CreateChartAsync()
    {
        this.WriteLine("======== Using CodeInterpreter tool ========");

        if (TestConfiguration.OpenAI.ApiKey == null)
        {
            this.WriteLine("OpenAI apiKey not found. Skipping example.");
            return;
        }

        this.WriteLine(Environment.CurrentDirectory);

        var fileService = new OpenAIFileService(TestConfiguration.OpenAI.ApiKey);

        var agent =
            await new AgentBuilder()
                .WithOpenAIChatCompletion(OpenAIFunctionEnabledModel, TestConfiguration.OpenAI.ApiKey)
                .WithCodeInterpreter()
                .BuildAsync();

        try
        {
            var thread = await agent.NewThreadAsync();

            await InvokeAgentAsync(
                thread,
                "1-first", @"
Display this data using a bar-chart:

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
                    var content = fileService.GetFileContent(message.Content);
                    await using var outputStream = File.OpenWrite(filename);
                    await using var inputStream = await content.GetStreamAsync();
                    await inputStream.CopyToAsync(outputStream);
                    var path = Path.Combine(Environment.CurrentDirectory, filename);
                    this.WriteLine($"# {message.Role}: {path}");
                    Process.Start(
                        new ProcessStartInfo
                        {
                            FileName = "cmd.exe",
                            Arguments = $"/C start {path}"
                        });
                }
                else
                {
                    this.WriteLine($"# {message.Role}: {message.Content}");
                }
            }

            this.WriteLine();
        }
    }

    public Example85_AgentCharts(ITestOutputHelper output) : base(output) { }
}
