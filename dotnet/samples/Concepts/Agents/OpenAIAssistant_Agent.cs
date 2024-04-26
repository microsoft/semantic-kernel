// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Plugins;

namespace Examples;
/// <summary>
/// Demonstrate creation of <see cref="OpenAIAssistantAgent"/> and
/// eliciting its response to three explicit user messages.
/// </summary>
/// <remarks>
/// This example demonstrates that outside of initialization (and cleanup), using
/// <see cref="OpenAIAssistantAgent"/> is no different from <see cref="ChatCompletionAgent"/>
/// even with with a <see cref="KernelPlugin"/>.
/// </remarks>
public class OpenAIAssistant_Agent(ITestOutputHelper output) : BaseTest(output)
{
    private const string HostName = "Host";
    private const string HostInstructions = "Answer questions about the menu.";

    [Fact]
    public async Task RunAsync()
    {
        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: this.CreateEmptyKernel(),
                config: new(this.ApiKey, this.Endpoint),
                new()
                {
                    Instructions = HostInstructions,
                    Name = HostName,
                    ModelId = this.Model,
                });

        // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        agent.Kernel.Plugins.Add(plugin);

        // Create a chat for agent interaction.
        var chat = new AgentGroupChat();

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Hello");
            await InvokeAgentAsync("What is the special soup?");
            await InvokeAgentAsync("What is the special drink?");
            await InvokeAgentAsync("Thank you");
        }
        finally
        {
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));

            this.WriteLine($"# {AuthorRole.User}: '{input}'");

            await foreach (var content in chat.InvokeAsync(agent))
            {
                this.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
            }
        }
    }
}
