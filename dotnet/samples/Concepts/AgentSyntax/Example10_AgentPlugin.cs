// Copyright (c) Microsoft. All rights reserved.
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
/// Demonstrate one agent calling another as a plug-in.
/// </summary>
public class Example10_AgentPlugin : BaseTest
{
    private const string TopName = "TopDog";
    private const string HostName = "Host";
    private const string HostInstructions = "Answer questions about the menu.";

    [Fact]
    public async Task RunAsync()
    {
        // Define the first agent
        ChatCompletionAgent agentHost =
            new()
            {
                Instructions = HostInstructions,
                Name = HostName,
                Kernel = this.CreateKernelWithChatCompletion(),
                ExecutionSettings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions },
            };

        // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        agentHost.Kernel.Plugins.Add(plugin);

        // Create another agent with the first agent configured as a plug-in.
        ChatCompletionAgent agentTop =
            new()
            {
                Name = TopName,
                Kernel = this.CreateKernelWithChatCompletion(),
                ExecutionSettings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions },
            };
        agentTop.Kernel.Plugins.Add(agentHost.AsPlugin());

        // Create a chat for agent interaction.
        AgentGroupChat chat = new();

        // Respond to user input, invoking functions where appropriate.
        await InvokeAgentAsync("Hello");
        await InvokeAgentAsync("What is the special soup?");
        await InvokeAgentAsync("What is the special drink?");
        await InvokeAgentAsync("Thank you");

        await foreach (var content in chat.GetChatMessagesAsync())
        {
            this.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));
            this.WriteLine($"# {AuthorRole.User}: '{input}'");

            // Use the "top" agent which does not have direct access to the menu.
            await foreach (var content in chat.InvokeAsync(agentTop))
            {
                this.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
            }
        }
    }

    public Example10_AgentPlugin(ITestOutputHelper output)
        : base(output)
    { }
}
