﻿// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Assistants;
using Plugins;

namespace GettingStarted.OpenAIAssistants;

/// <summary>
/// Demonstrate creation of <see cref="OpenAIAssistantAgent"/> with a <see cref="KernelPlugin"/>,
/// and then eliciting its response to explicit user messages.
/// </summary>
public class Step02_Assistant_Plugins(ITestOutputHelper output) : BaseAssistantTest(output)
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
        string threadId = await this.AssistantClient.CreateThreadAsync(metadata: SampleMetadata);

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
            await this.AssistantClient.DeleteThreadAsync(threadId);
            await this.AssistantClient.DeleteAssistantAsync(agent.Id);
        }
    }

    [Fact]
    public async Task UseAssistantWithPluginEnumParameterAsync()
    {
        // Define the agent
        OpenAIAssistantAgent agent = await CreateAssistantAgentAsync(plugin: KernelPluginFactory.CreateFromType<WidgetFactory>());

        // Create a thread for the agent conversation.
        string threadId = await this.AssistantClient.CreateThreadAsync(metadata: SampleMetadata);

        // Respond to user input
        try
        {
            await InvokeAgentAsync(agent, threadId, "Create a beautiful red colored widget for me.");
        }
        finally
        {
            await this.AssistantClient.DeleteThreadAsync(threadId);
            await this.AssistantClient.DeleteAssistantAsync(agent.Id);
        }
    }

    private async Task<OpenAIAssistantAgent> CreateAssistantAgentAsync(KernelPlugin plugin, string? instructions = null, string? name = null)
    {
        // Define the assistant
        Assistant assistant =
            await this.AssistantClient.CreateAssistantAsync(
                this.Model,
                name,
                instructions: instructions,
                metadata: SampleMetadata);

        // Create the agent
        OpenAIAssistantAgent agent = new(assistant, this.AssistantClient, [plugin]);

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
