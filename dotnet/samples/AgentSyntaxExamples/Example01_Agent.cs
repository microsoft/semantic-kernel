// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
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
public class Example01_Agent : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        // $$$
        ChatCompletionAgent agent =
            new(
                kernel: this.CreateKernelWithChatCompletion(),
                instructions: AgentInventory.ParrotInstructions)
            {
                //ExecutionSettings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions },
                InstructionArguments = new() { { "count", 3 } },
            };

        // $$$
        var nexus = new TestChat();

        // $$$
        await WriteAgentResponseAsync("Fortune favors the bold.");
        await WriteAgentResponseAsync("I came, I saw, I conquered.");
        await WriteAgentResponseAsync("Practice makes perfect.");

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

    public Example01_Agent(ITestOutputHelper output) : base(output)
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
