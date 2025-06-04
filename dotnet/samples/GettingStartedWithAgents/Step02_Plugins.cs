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
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task UseChatCompletionWithPlugin(bool useChatClient)
    {
        // Define the agent
        ChatCompletionAgent agent = CreateAgentWithPlugin(
                plugin: KernelPluginFactory.CreateFromType<MenuPlugin>(),
                instructions: "Answer questions about the menu.",
                name: "Host",
                useChatClient: useChatClient);

        /// Create the chat history thread to capture the agent interaction.
        AgentThread thread = new ChatHistoryAgentThread();

        // Respond to user input, invoking functions where appropriate.
        await InvokeAgentAsync(agent, thread, "Hello");
        await InvokeAgentAsync(agent, thread, "What is the special soup and its price?");
        await InvokeAgentAsync(agent, thread, "What is the special drink and its price?");
        await InvokeAgentAsync(agent, thread, "Thank you");
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task UseChatCompletionWithPluginEnumParameter(bool useChatClient)
    {
        // Define the agent
        ChatCompletionAgent agent = CreateAgentWithPlugin(
                KernelPluginFactory.CreateFromType<WidgetFactory>(),
                useChatClient: useChatClient);

        /// Create the chat history thread to capture the agent interaction.
        AgentThread thread = new ChatHistoryAgentThread();

        // Respond to user input, invoking functions where appropriate.
        await InvokeAgentAsync(agent, thread, "Create a beautiful red colored widget for me.");
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task UseChatCompletionWithTemplateExecutionSettings(bool useChatClient)
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
                Kernel = this.CreateKernelWithChatCompletion(useChatClient, out var chatClient),
            };

        agent.Kernel.Plugins.AddFromType<WidgetFactory>();

        /// Create the chat history thread to capture the agent interaction.
        AgentThread thread = new ChatHistoryAgentThread();

        // Respond to user input, invoking functions where appropriate.
        await InvokeAgentAsync(agent, thread, "Create a beautiful red colored widget for me.");

        chatClient?.Dispose();
    }

    private ChatCompletionAgent CreateAgentWithPlugin(
        KernelPlugin plugin,
        string? instructions = null,
        string? name = null,
        bool useChatClient = false)
    {
        ChatCompletionAgent agent =
                new()
                {
                    Instructions = instructions,
                    Name = name,
                    Kernel = this.CreateKernelWithChatCompletion(useChatClient, out _),
                    Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
                };

        // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
        agent.Kernel.Plugins.Add(plugin);

        return agent;
    }

    // Local function to invoke agent and display the conversation messages.
    private async Task InvokeAgentAsync(ChatCompletionAgent agent, AgentThread thread, string input)
    {
        ChatMessageContent message = new(AuthorRole.User, input);
        this.WriteAgentChatMessage(message);

        await foreach (ChatMessageContent response in agent.InvokeAsync(message, thread))
        {
            this.WriteAgentChatMessage(response);
        }
    }
}
