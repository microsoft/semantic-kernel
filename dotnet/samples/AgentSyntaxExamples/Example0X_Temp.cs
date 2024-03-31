// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using AgentSyntaxExamples;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// $$$
/// </summary>
public class Example0X_Temp : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        // $$$
        Kernel kernel = this.CreateKernelWithChatCompletion();
        var agent = AgentInventory.OpenAI.CreateParrotAgent(kernel);
        agent.InstructionArguments = new() { { "count", 3 } };

        // $$$
        var nexus = new TestChat();

        await WriteContentAsync(nexus.InvokeAsync(agent, "Fortune favors the bold."));
        await WriteContentAsync(nexus.InvokeAsync(agent, "I came, I saw, I conquered."));
        await WriteContentAsync(nexus.InvokeAsync(agent, "Practice makes perfect."));
    }

    private async Task<AgentNexus> RunSingleAgentAsync(Agent agent, params string[] messages)
    {
        this.WriteLine("[AGENTS]");
        WriteAgent(agent, full: true);
        WriteLine();

        this.WriteLine("[CHAT]");
        var nexus = new TestChat();

        // Process each user message and agent response.
        foreach (var message in messages)
        {
            await WriteChatAsync(nexus, agent, message);
        }

        this.WriteLine("\n[HISTORY]");
        await WriteHistoryAsync(nexus);
        await WriteHistoryAsync(nexus, agent);

        return nexus;
    }

    private Task WriteChatAsync(TestChat nexus, Agent agent, string? message = null)
    {
        return WriteContentAsync(nexus.InvokeAsync(agent, message));
    }

    private void WriteAgent(Agent agent, bool full = false)
    {
        this.WriteLine($"[{agent.GetType().Name}:{agent.Id}:{agent.Name ?? "*"}]");
        if (agent is KernelAgent kernelAgent)
        {
            this.WriteLine($"\t> {kernelAgent.Instructions ?? "*"}");
        }
    }

    private async Task WriteContentAsync(IAsyncEnumerable<ChatMessageContent> messages)
    {
        await foreach (var content in messages)
        {
            this.WriteLine($"# {content.Role}: '{content.Content}'");
            //this.WriteLine($"# {content.Role} - {content.Name ?? "*"}: '{content.Content}'");
        }
    }

    private async Task WriteHistoryAsync(AgentNexus nexus, Agent? agent = null)
    {
        if (agent == null)
        {
            this.WriteLine("\n[PRIMARY]");
        }
        else
        {
            this.WriteLine();
            this.WriteAgent(agent);
        }

        var history = await nexus.GetHistoryAsync(agent).ToArrayAsync();

        await WriteContentAsync(history.Reverse().ToAsyncEnumerable());
    }

    public Example0X_Temp(ITestOutputHelper output) : base(output)
    {
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
