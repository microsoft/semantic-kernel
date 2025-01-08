// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;
using AzureAIP = Azure.AI.Projects;

namespace GettingStarted;

/// <summary>
/// This example demonstrates similarity between using <see cref="AzureAIAgent"/>
/// and <see cref="ChatCompletionAgent"/> (see: Step 2).
/// </summary>
public class Step12_Azure(ITestOutputHelper output) : BaseAgentsTest(output)
{
    private const string HostName = "Host";
    private const string HostInstructions = "Answer questions about the menu.";

    [Fact]
    public async Task UseSingleAssistantAgentAsync()
    {
        // Define the agent
        AzureAIClientProvider clientProvider = this.GetAzureProvider();
        AzureAIP.AgentsClient client = clientProvider.Client.GetAgentsClient();
        AzureAIP.Agent definition = await client.CreateAgentAsync(
            this.Model,
            HostName,
            null,
            HostInstructions);
        AzureAIAgent agent = new(definition, clientProvider)
        {
            Kernel = new Kernel(),
        };

        // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        agent.Kernel.Plugins.Add(plugin);

        // Create a thread for the agent conversation.
        string threadId = await agent.CreateThreadAsync(new AzureAIThreadCreationOptions { Metadata = AssistantSampleMetadata });

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Hello");
            await InvokeAgentAsync("What is the special soup and its price?");
            await InvokeAgentAsync("What is the special drink and its price?");
            await InvokeAgentAsync("Thank you");
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
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

    [Fact]
    public async Task UseTemplateForAssistantAgentAsync()
    {
        // Define the agent
        string generateStoryYaml = EmbeddedResource.Read("GenerateStory.yaml");
        PromptTemplateConfig templateConfig = KernelFunctionYaml.ToPromptTemplateConfig(generateStoryYaml);
        IPromptTemplate promptTemplate = new KernelPromptTemplateFactory().Create(templateConfig);
        AzureAIClientProvider clientProvider = this.GetAzureProvider();
        AzureAIP.Agent definition = await clientProvider.Client.GetAgentsClient().CreateAgentAsync(this.Model);
        // Instructions, Name and Description properties defined via the config.
        AzureAIAgent agent = new(definition, clientProvider, promptTemplate)
        {
            Kernel = new Kernel(),
            Arguments = new KernelArguments()
            {
                { "topic", "Dog" },
                { "length", "3" },
            },
        };

        // Create a thread for the agent conversation.
        string threadId = await agent.CreateThreadAsync(new AzureAIThreadCreationOptions { Metadata = AssistantSampleMetadata });

        try
        {
            // Invoke the agent with the default arguments.
            await InvokeAgentAsync();

            // Invoke the agent with the override arguments.
            await InvokeAgentAsync(
                        new()
                        {
                { "topic", "Cat" },
                { "length", "3" },
                        });
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the response.
        async Task InvokeAgentAsync(KernelArguments? arguments = null)
        {
            await foreach (ChatMessageContent response in agent.InvokeAsync(threadId, arguments))
            {
                WriteAgentChatMessage(response);
            }
        }
    }

    private sealed class MenuPlugin
    {
        [KernelFunction, Description("Provides a list of specials from the menu.")]
        [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1024:Use properties where appropriate", Justification = "Too smart")]
        public string GetSpecials() =>
            """
            Special Soup: Clam Chowder
            Special Salad: Cobb Salad
            Special Drink: Chai Tea
            """;

        [KernelFunction, Description("Provides the price of the requested menu item.")]
        public string GetItemPrice(
            [Description("The name of the menu item.")]
            string menuItem) =>
            "$9.99";
    }
}
