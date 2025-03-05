// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Plugins;
using Agent = Azure.AI.Projects.Agent;

namespace GettingStarted.AzureAgents;

/// <summary>
/// Demonstrate creation of <see cref="AzureAIAgent"/> with a <see cref="KernelPlugin"/>,
/// and then eliciting its response to explicit user messages.
/// </summary>
public class Step02_AzureAIAgent_Plugins(ITestOutputHelper output) : BaseAzureAgentTest(output)
{
    [Fact]
    public async Task UseAzureAgentWithPluginAsync()
    {
        // Define the agent
        AzureAIAgent agent = await CreateAzureAgentAsync(
                plugin: KernelPluginFactory.CreateFromType<MenuPlugin>(),
                instructions: "Answer questions about the menu.",
                name: "Host");

        // Create a thread for the agent conversation.
        AgentThread thread = await this.AgentsClient.CreateThreadAsync(metadata: SampleMetadata);

        // Respond to user input
        try
        {
            await InvokeAgentAsync(agent, thread.Id, "Hello");
            await InvokeAgentAsync(agent, thread.Id, "What is the special soup and its price?");
            await InvokeAgentAsync(agent, thread.Id, "What is the special drink and its price?");
            await InvokeAgentAsync(agent, thread.Id, "Thank you");
        }
        finally
        {
            await this.AgentsClient.DeleteThreadAsync(thread.Id);
            await this.AgentsClient.DeleteAgentAsync(agent.Id);
        }
    }

    [Fact]
    public async Task UseAzureAgentWithPluginEnumParameterAsync()
    {
        // Define the agent
        AzureAIAgent agent = await CreateAzureAgentAsync(plugin: KernelPluginFactory.CreateFromType<WidgetFactory>());

        // Create a thread for the agent conversation.
        AgentThread thread = await this.AgentsClient.CreateThreadAsync(metadata: SampleMetadata);

        // Respond to user input
        try
        {
            await InvokeAgentAsync(agent, thread.Id, "Create a beautiful red colored widget for me.");
        }
        finally
        {
            await this.AgentsClient.DeleteThreadAsync(thread.Id);
            await this.AgentsClient.DeleteAgentAsync(agent.Id);
        }
    }

    private async Task<AzureAIAgent> CreateAzureAgentAsync(KernelPlugin plugin, string? instructions = null, string? name = null)
    {
        // Define the agent
        Agent definition = await this.AgentsClient.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId,
            name,
            null,
            instructions);

        AzureAIAgent agent = new(definition, this.AgentsClient)
        {
            Kernel = new Kernel(),
        };

        // Add to the agent's Kernel
        if (plugin != null)
        {
            agent.Kernel.Plugins.Add(plugin);
        }

        return agent;
    }

    // Local function to invoke agent and display the conversation messages.
    private async Task InvokeAgentAsync(AzureAIAgent agent, string threadId, string input)
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
