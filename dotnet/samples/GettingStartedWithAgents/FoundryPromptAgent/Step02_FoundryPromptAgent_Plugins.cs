// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects.Agents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Plugins;

namespace GettingStarted.FoundryPromptAgents;

/// <summary>
/// Demonstrate using a <see cref="KernelPlugin"/> with a Microsoft Foundry Prompt Agent,
/// and then eliciting its response to explicit user messages.
/// </summary>
public class Step02_FoundryPromptAgent_Plugins(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    [Fact]
    public async Task UseFoundryPromptAgentWithPlugin()
    {
        // Define the agent
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        (ChatCompletionAgent agent, ProjectsAgentVersion promptAgent) = await CreateAgentAsync(
                plugin: plugin,
                instructions: "Answer questions about the menu.",
                name: "Host");

        // Create a thread for the agent conversation.
        AgentThread thread = new ChatHistoryAgentThread();

        // Respond to user input
        try
        {
            await InvokeAgentAsync(agent, thread, "Hello");
            await InvokeAgentAsync(agent, thread, "What is the special soup and its price?");
            await InvokeAgentAsync(agent, thread, "What is the special drink and its price?");
            await InvokeAgentAsync(agent, thread, "Thank you");
        }
        finally
        {
            await thread.DeleteAsync();
            await this.DeletePromptAgentAsync(promptAgent);
        }
    }

    [Fact]
    public async Task UseFoundryPromptAgentWithPluginEnumParameter()
    {
        // Define the agent
        (ChatCompletionAgent agent, ProjectsAgentVersion promptAgent) = await CreateAgentAsync(plugin: KernelPluginFactory.CreateFromType<WidgetFactory>());

        // Create a thread for the agent conversation.
        AgentThread thread = new ChatHistoryAgentThread();

        // Respond to user input
        try
        {
            await InvokeAgentAsync(agent, thread, "Create a beautiful red colored widget for me.");
        }
        finally
        {
            await thread.DeleteAsync();
            await this.DeletePromptAgentAsync(promptAgent);
        }
    }

    private async Task<(ChatCompletionAgent Agent, ProjectsAgentVersion PromptAgent)> CreateAgentAsync(KernelPlugin plugin, string? instructions = null, string? name = null)
    {
        // Define the Prompt Agent. A Prompt Agent only calls functions declared on its definition,
        // so the plugin functions are declared as function tools.
        ProjectsAgentVersion promptAgent =
            await this.CreatePromptAgentAsync(
                name ?? "Agent",
                new DeclarativeAgentDefinition(DeploymentName) { Instructions = instructions }
                    .AddFunctionTools(plugin));

        // Create the agent. Semantic Kernel runs the plugin functions locally when the Prompt Agent calls them.
        ChatCompletionAgent agent =
            new()
            {
                Name = name,
                Kernel = this.CreateKernel(promptAgent, plugin),
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };

        return (agent, promptAgent);
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
