// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Plugins;

namespace GettingStarted.OpenAIAssistants;

/// <summary>
/// Demonstrate creation of <see cref="OpenAIAssistantAgent"/> with a <see cref="KernelPlugin"/>,
/// and then eliciting its response to explicit user messages.
/// </summary>
public class Step02_Assistant_Plugins(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseAssistantWithPluginAsync()
    {
        // Define the agent
        OpenAIAssistantAgent agent = await CreateAssistantAgentAsync(
                plugin: KernelPluginFactory.CreateFromType<MenuPlugin>(),
                instructions: "Answer questions about the menu.",
                name: "Host");

        // Create a thread for the agent conversation.
        string threadId = await agent.CreateThreadAsync(new OpenAIThreadCreationOptions { Metadata = AssistantSampleMetadata });

        // Respond to user input
        try
        {
            await InvokeAgentAsync(agent, threadId, "Hello");
            await InvokeAgentAsync(agent, threadId, "What is the special soup and its price?");
            await InvokeAgentAsync(agent, threadId, "What is the special drink and its price?");
            await InvokeAgentAsync(agent, threadId, "Thank you");
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }
    }

    [Fact]
    public async Task UseAssistantWithPluginEnumParameterAsync()
    {
        // Define the agent
        OpenAIAssistantAgent agent = await CreateAssistantAgentAsync(plugin: KernelPluginFactory.CreateFromType<WidgetFactory>());

        // Create a thread for the agent conversation.
        string threadId = await agent.CreateThreadAsync(new OpenAIThreadCreationOptions { Metadata = AssistantSampleMetadata });

        // Respond to user input
        try
        {
            await InvokeAgentAsync(agent, threadId, "Create a beautiful red colored widget for me.");
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }
    }

    private async Task<OpenAIAssistantAgent> CreateAssistantAgentAsync(KernelPlugin plugin, string? instructions = null, string? name = null)
    {
        // Create the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                clientProvider: this.GetClientProvider(),
                definition: new OpenAIAssistantDefinition(this.Model)
                {
                    Instructions = instructions,
                    Name = name,
                    Metadata = AssistantSampleMetadata,
                },
                kernel: new Kernel());

        // Add to the agent's Kernel
        agent.Kernel.Plugins.Add(plugin);

        return agent;
    }

    // Local function to invoke agent and display the conversation messages.
    private async Task InvokeAgentAsync(OpenAIAssistantAgent agent, string threadId, string input)
    {
        ChatMessageContent message = new(AuthorRole.User, input);
        await agent.AddChatMessageAsync(threadId, message);
        this.WriteAgentChatMessage(message);

        await foreach (ChatMessageContent response in agent.InvokeAsync(threadId))
        {
            this.WriteAgentChatMessage(response);
        }
    }
}
