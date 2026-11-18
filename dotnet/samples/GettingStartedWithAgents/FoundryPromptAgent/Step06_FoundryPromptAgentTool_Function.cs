// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects.Agents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Responses;
using Plugins;

namespace GettingStarted.FoundryPromptAgents;

/// <summary>
/// This example demonstrates how to define function tools for a Microsoft Foundry Prompt Agent
/// when the agent is created. This is useful if you want to retrieve the agent later and
/// then dynamically check what function tools it requires.
/// </summary>
public class Step06_FoundryPromptAgentTool_Function(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    private const string HostName = "Host";
    private const string HostInstructions = "Answer questions about the menu.";

    [Fact]
    public async Task UseSingleFoundryPromptAgentWithFunctionTools()
    {
        // In this sample the function tools are added to the Prompt Agent definition, which is stored in the Foundry project.
        // This is important if you want to retrieve the agent later and then dynamically check what function tools it requires.
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        ProjectsAgentVersion createdAgent =
            await this.CreatePromptAgentAsync(
                HostName,
                new DeclarativeAgentDefinition(DeploymentName) { Instructions = HostInstructions }
                    .AddFunctionTools(plugin));

        try
        {
            // Retrieve the stored Prompt Agent, as an application does for an agent that already exists.
            ProjectsAgentVersion promptAgent = await this.Client.AgentAdministrationClient.GetAgentVersionAsync(createdAgent.Name, createdAgent.Version);

            // Check which function tools the Prompt Agent requires, and confirm that the plugin provides each of them.
            // Function tool names have the form "<plugin>_<function>".
            DeclarativeAgentDefinition definition = (DeclarativeAgentDefinition)promptAgent.Definition;
            foreach (FunctionTool tool in definition.Tools.OfType<FunctionTool>())
            {
                bool isAvailable = plugin.Any(function => $"{plugin.Name}_{function.Name}" == tool.FunctionName);
                Console.WriteLine($"Required function tool: {tool.FunctionName} (available: {isAvailable})");
            }

            // Create the agent and add the plugin to the agent's Kernel (same as direct Kernel usage).
            ChatCompletionAgent agent =
                new()
                {
                    Name = HostName,
                    Kernel = this.CreateKernel(promptAgent, plugin),
                    Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
                };

            // Create a thread for the agent conversation.
            AgentThread thread = new ChatHistoryAgentThread();

            // Respond to user input
            await InvokeAgentAsync(agent, thread, "Hello");
            await InvokeAgentAsync(agent, thread, "What is the special soup and its price?");
            await InvokeAgentAsync(agent, thread, "What is the special drink and its price?");
            await InvokeAgentAsync(agent, thread, "Thank you");

            await thread.DeleteAsync();
        }
        finally
        {
            await this.DeletePromptAgentAsync(createdAgent);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(ChatCompletionAgent agent, AgentThread thread, string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(message, thread))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }
}
