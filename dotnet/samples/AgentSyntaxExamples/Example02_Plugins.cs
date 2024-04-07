// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Plugins;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> with a <see cref="KernelPlugin"/>,
/// and then eliciting its response to explicit user messages.
/// </summary>
public class Example02_Plugins : BaseTest
{
    public const string HostName = "Host";
    public const string HostInstructions = "Answer questions about the menu.";

    [Fact]
    public async Task RunAsync()
    {
        // Define the agent
        ChatCompletionAgent agent =
            new(
                kernel: this.CreateKernelWithChatCompletion(),
                instructions: HostInstructions,
                name: HostName)
            {
                ExecutionSettings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions }
            };

        // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        agent.Kernel.Plugins.Add(plugin);

        // Create a chat for agent interaction. For more, see: Example03_Chat.
        var chat = new TestChat();

        // Respond to user input, invoking functions where appropriate.
        await WriteAgentResponseAsync("Hello");
        await WriteAgentResponseAsync("What is the special soup?");
        await WriteAgentResponseAsync("What is the special drink?");
        await WriteAgentResponseAsync("Thank you");

        // Local function to invoke agent and display the conversation messages.
        async Task WriteAgentResponseAsync(string input)
        {
            chat.AddUserMessage(input);
            this.WriteLine($"# {AuthorRole.User}: '{input}'");

            await foreach (var content in chat.InvokeAsync(agent))
            {
                this.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
            }
        }
    }

    public Example02_Plugins(ITestOutputHelper output)
        : base(output)
    { }

    /// <summary>
    ///
    /// A simple chat for the agent example.
    /// </summary>
    /// <remarks>
    /// For further exploration of <see cref="AgentChat"/>, see: Example03_Chat.
    /// </remarks>
    private sealed class TestChat : AgentChat
    {
        public IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            Agent agent,
            CancellationToken cancellationToken = default) =>
                base.InvokeAgentAsync(agent, cancellationToken);
    }
}
