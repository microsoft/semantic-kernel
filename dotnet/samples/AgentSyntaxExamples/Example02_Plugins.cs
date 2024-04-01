// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using AgentSyntaxExamples;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Plugins;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// $$$
/// </summary>
public class Example02_Plugins : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        kernel.Plugins.Add(plugin);

        var agent = AgentInventory.OpenAI.CreateHostAgent(kernel);

        // $$$
        var nexus = new TestChat();

        // $$$
        await WriteAgentResponseAsync("Hello");
        await WriteAgentResponseAsync("What is the special soup?");
        await WriteAgentResponseAsync("What is the special drink?");
        await WriteAgentResponseAsync("Thank you");

        // $$$
        async Task WriteAgentResponseAsync(string input)
        {
            await foreach (var content in nexus.InvokeAsync(agent, input))
            {
                this.WriteLine($"# {content.Role}: '{content.Content}'");
                //this.WriteLine($"# {content.Role} - {content.Name ?? "*"}: '{content.Content}'");
            }
        }
    }

    public Example02_Plugins(ITestOutputHelper output)
        : base(output)
    {
        // Nothing to do...
    }

    /// <summary>
    /// A basic nexus for the agent example.
    /// </summary>
    /// <remarks>
    /// $$$ POINTER TO NEXUS EXAMPLE START
    /// </remarks>
    private sealed class TestChat : AgentNexus
    {
        public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            Agent agent,
            string? input = null,
            CancellationToken cancellationToken = default) =>
                base.InvokeAgentAsync(agent, CreateUserMessage(input), cancellationToken);
    }
}
