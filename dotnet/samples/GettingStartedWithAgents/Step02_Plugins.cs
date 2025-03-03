// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Plugins;
using Resources;

namespace GettingStarted;

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> with a <see cref="KernelPlugin"/>,
/// and then eliciting its response to explicit user messages.
/// </summary>
public class Step02_Plugins(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseChatCompletionWithPluginAsync()
    {
        // Define the agent
        ChatCompletionAgent agent = CreateAgentWithPlugin(
                plugin: KernelPluginFactory.CreateFromType<MenuPlugin>(),
                instructions: "Answer questions about the menu.",
                name: "Host");

        /// Create the chat history to capture the agent interaction.
        ChatHistory chat = [];

        // Respond to user input, invoking functions where appropriate.
        await InvokeAgentAsync(agent, chat, "Hello");
        await InvokeAgentAsync(agent, chat, "What is the special soup and its price?");
        await InvokeAgentAsync(agent, chat, "What is the special drink and its price?");
        await InvokeAgentAsync(agent, chat, "Thank you");
    }

    [Fact]
    public async Task UseChatCompletionWithPluginEnumParameterAsync()
    {
        // Define the agent
        ChatCompletionAgent agent = CreateAgentWithPlugin(
                KernelPluginFactory.CreateFromType<WidgetFactory>());

        /// Create the chat history to capture the agent interaction.
        ChatHistory chat = [];

        // Respond to user input, invoking functions where appropriate.
        await InvokeAgentAsync(agent, chat, "Create a beautiful red colored widget for me.");
    }

    [Fact]
    public async Task UseChatCompletionWithTemplateExecutionSettingsAsync()
    {
        // Read the template resource
        string autoInvokeYaml = EmbeddedResource.Read("AutoInvokeTools.yaml");
        PromptTemplateConfig templateConfig = KernelFunctionYaml.ToPromptTemplateConfig(autoInvokeYaml);
        KernelPromptTemplateFactory templateFactory = new();

        // Define the agent:
        // Execution-settings with auto-invocation of plugins defined via the config.
        ChatCompletionAgent agent =
            new(templateConfig, templateFactory)
            {
                Kernel = this.CreateKernelWithChatCompletion()
            };

        agent.Kernel.Plugins.AddFromType<WidgetFactory>();

        /// Create the chat history to capture the agent interaction.
        ChatHistory chat = [];

        // Respond to user input, invoking functions where appropriate.
        await InvokeAgentAsync(agent, chat, "Create a beautiful red colored widget for me.");
    }

    private ChatCompletionAgent CreateAgentWithPlugin(
        KernelPlugin plugin,
        string? instructions = null,
        string? name = null)
    {
        ChatCompletionAgent agent =
                new()
                {
                    Instructions = instructions,
                    Name = name,
                    Kernel = this.CreateKernelWithChatCompletion(),
                    Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
                };

        // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
        agent.Kernel.Plugins.Add(plugin);

        return agent;
    }

    // Local function to invoke agent and display the conversation messages.
    private async Task InvokeAgentAsync(ChatCompletionAgent agent, ChatHistory chat, string input)
    {
        ChatMessageContent message = new(AuthorRole.User, input);
        chat.Add(message);

        this.WriteAgentChatMessage(message);

        await foreach (ChatMessageContent response in agent.InvokeAsync(chat))
        {
            chat.Add(response);

            this.WriteAgentChatMessage(response);
        }
    }
}
