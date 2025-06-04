// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Agents.Persistent;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Plugins;

namespace GettingStarted.AzureAgents;

/// <summary>
/// Demonstrate creation of <see cref="AzureAIAgent"/> with a <see cref="KernelPlugin"/>,
/// and then eliciting its response to explicit user messages.
/// </summary>
public class Step02_AzureAIAgent_Plugins(ITestOutputHelper output) : BaseAzureAgentTest(output)
{
    [Fact]
    public async Task UseAzureAgentWithPlugin()
    {
        // Define the agent
        AzureAIAgent agent = await CreateAzureAgentAsync(
                plugin: KernelPluginFactory.CreateFromType<MenuPlugin>(),
                instructions: "Answer questions about the menu.",
                name: "Host");

        // Create a thread for the agent conversation.
        AgentThread thread = new AzureAIAgentThread(this.Client, metadata: SampleMetadata);

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
            await this.Client.Administration.DeleteAgentAsync(agent.Id);
        }
    }

    [Fact]
    public async Task UseAzureAgentWithPluginEnumParameter()
    {
        // Define the agent
        AzureAIAgent agent = await CreateAzureAgentAsync(plugin: KernelPluginFactory.CreateFromType<WidgetFactory>());

        // Create a thread for the agent conversation.
        AgentThread thread = new AzureAIAgentThread(this.Client, metadata: SampleMetadata);

        // Respond to user input
        try
        {
            await InvokeAgentAsync(agent, thread, "Create a beautiful red colored widget for me.");
        }
        finally
        {
            await thread.DeleteAsync();
            await this.Client.Administration.DeleteAgentAsync(agent.Id);
        }
    }

    [Fact]
    public async Task UseAzureAgentWithPromptFunction()
    {
        // Define prompt function
        KernelFunction promptFunction =
            KernelFunctionFactory.CreateFromPrompt(
                promptTemplate:
                    """
                    Count the number of vowels in INPUT and report as a markdown table.

                    INPUT:
                    {{$input}}
                    """,
                description: "Counts the number of vowels");

        // Define the agent
        AzureAIAgent agent =
            await CreateAzureAgentAsync(
                KernelPluginFactory.CreateFromFunctions("AgentPlugin", [promptFunction]),
                instructions: "You job is to only and always analyze the vowels in the user input without confirmation.");

        agent.Kernel.FunctionInvocationFilters.Add(new PromptFunctionFilter());

        // Create the chat history thread to capture the agent interaction.
        AzureAIAgentThread thread = new(agent.Client);

        // Respond to user input, invoking functions where appropriate.
        await InvokeAgentAsync(agent, thread, "Who would know naught of art must learn, act, and then take his ease.");
    }

    private async Task<AzureAIAgent> CreateAzureAgentAsync(KernelPlugin plugin, string? instructions = null, string? name = null)
    {
        // Define the agent
        PersistentAgent definition = await this.Client.Administration.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId,
            name,
            null,
            instructions);

        AzureAIAgent agent =
            new(definition, this.Client)
            {
                Kernel = this.CreateKernelWithChatCompletion(),
            };

        // Add to the agent's Kernel
        if (plugin != null)
        {
            agent.Kernel.Plugins.Add(plugin);
        }

        return agent;
    }

    // Local function to invoke agent and display the conversation messages.
    private async Task InvokeAgentAsync(AzureAIAgent agent, AgentThread thread, string input)
    {
        ChatMessageContent message = new(AuthorRole.User, input);
        this.WriteAgentChatMessage(message);

        await foreach (ChatMessageContent response in agent.InvokeAsync(message, thread))
        {
            this.WriteAgentChatMessage(response);
        }
    }

    private sealed class PromptFunctionFilter : IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            System.Console.WriteLine($"INVOKING: {context.Function.Name}");
            await next.Invoke(context);
            System.Console.WriteLine($"RESULT: {context.Result}");
        }
    }
}
