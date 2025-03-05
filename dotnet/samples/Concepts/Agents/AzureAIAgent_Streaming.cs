// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Azure.AI.Projects;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Agent = Azure.AI.Projects.Agent;

namespace Agents;

/// <summary>
/// Demonstrate consuming "streaming" message for <see cref="AzureAIAgent"/>.
/// </summary>
public class AzureAIAgent_Streaming(ITestOutputHelper output) : BaseAzureAgentTest(output)
{
    [Fact]
    public async Task UseStreamingAgentAsync()
    {
        const string AgentName = "Parrot";
        const string AgentInstructions = "Repeat the user message in the voice of a pirate and then end with a parrot sound.";

        // Define the agent
        Agent definition = await this.AgentsClient.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId,
            AgentName,
            null,
            AgentInstructions);
        AzureAIAgent agent = new(definition, this.AgentsClient);

        // Create a thread for the agent conversation.
        AgentThread thread = await this.AgentsClient.CreateThreadAsync(metadata: SampleMetadata);

        // Respond to user input
        await InvokeAgentAsync(agent, thread.Id, "Fortune favors the bold.");
        await InvokeAgentAsync(agent, thread.Id, "I came, I saw, I conquered.");
        await InvokeAgentAsync(agent, thread.Id, "Practice makes perfect.");

        // Output the entire chat history
        await DisplayChatHistoryAsync(agent, thread.Id);
    }

    [Fact]
    public async Task UseStreamingAssistantAgentWithPluginAsync()
    {
        const string AgentName = "Host";
        const string AgentInstructions = "Answer questions about the menu.";

        // Define the agent
        Agent definition = await this.AgentsClient.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId,
            AgentName,
            null,
            AgentInstructions);
        AzureAIAgent agent = new(definition, this.AgentsClient)
        {
            Kernel = new Kernel(),
        };

        // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        agent.Kernel.Plugins.Add(plugin);

        // Create a thread for the agent conversation.
        AgentThread thread = await this.AgentsClient.CreateThreadAsync(metadata: SampleMetadata);

        // Respond to user input
        await InvokeAgentAsync(agent, thread.Id, "What is the special soup and its price?");
        await InvokeAgentAsync(agent, thread.Id, "What is the special drink and its price?");

        // Output the entire chat history
        await DisplayChatHistoryAsync(agent, thread.Id);
    }

    [Fact]
    public async Task UseStreamingAssistantWithCodeInterpreterAsync()
    {
        const string AgentName = "MathGuy";
        const string AgentInstructions = "Solve math problems with code.";

        // Define the agent
        Agent definition = await this.AgentsClient.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId,
            AgentName,
            null,
            AgentInstructions,
            [new CodeInterpreterToolDefinition()]);
        AzureAIAgent agent = new(definition, this.AgentsClient)
        {
            Kernel = new Kernel(),
        };

        // Create a thread for the agent conversation.
        AgentThread thread = await this.AgentsClient.CreateThreadAsync(metadata: SampleMetadata);

        // Respond to user input
        await InvokeAgentAsync(agent, thread.Id, "Is 191 a prime number?");
        await InvokeAgentAsync(agent, thread.Id, "Determine the values in the Fibonacci sequence that that are less then the value of 101");

        // Output the entire chat history
        await DisplayChatHistoryAsync(agent, thread.Id);
    }

    // Local function to invoke agent and display the conversation messages.
    private async Task InvokeAgentAsync(AzureAIAgent agent, string threadId, string input)
    {
        ChatMessageContent message = new(AuthorRole.User, input);
        await agent.AddChatMessageAsync(threadId, message);
        this.WriteAgentChatMessage(message);

        ChatHistory history = [];

        bool isFirst = false;
        bool isCode = false;
        await foreach (StreamingChatMessageContent response in agent.InvokeStreamingAsync(threadId, messages: history))
        {
            if (string.IsNullOrEmpty(response.Content))
            {
                StreamingFunctionCallUpdateContent? functionCall = response.Items.OfType<StreamingFunctionCallUpdateContent>().SingleOrDefault();
                if (functionCall != null)
                {
                    Console.WriteLine($"\n# {response.Role} - {response.AuthorName ?? "*"}: FUNCTION CALL - {functionCall.Name}");
                }

                continue;
            }

            // Differentiate between assistant and tool messages
            if (isCode != (response.Metadata?.ContainsKey(AzureAIAgent.CodeInterpreterMetadataKey) ?? false))
            {
                isFirst = false;
                isCode = !isCode;
            }

            if (!isFirst)
            {
                Console.WriteLine($"\n# {response.Role} - {response.AuthorName ?? "*"}:");
                isFirst = true;
            }

            Console.WriteLine($"\t > streamed: '{response.Content}'");
        }

        foreach (ChatMessageContent content in history)
        {
            this.WriteAgentChatMessage(content);
        }
    }

    private async Task DisplayChatHistoryAsync(AzureAIAgent agent, string threadId)
    {
        Console.WriteLine("================================");
        Console.WriteLine("CHAT HISTORY");
        Console.WriteLine("================================");

        ChatMessageContent[] messages = await agent.GetThreadMessagesAsync(threadId).ToArrayAsync();
        for (int index = messages.Length - 1; index >= 0; --index)
        {
            this.WriteAgentChatMessage(messages[index]);
        }
    }

    public sealed class MenuPlugin
    {
        [KernelFunction, Description("Provides a list of specials from the menu.")]
        [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1024:Use properties where appropriate", Justification = "Too smart")]
        public string GetSpecials()
        {
            return @"
Special Soup: Clam Chowder
Special Salad: Cobb Salad
Special Drink: Chai Tea
";
        }

        [KernelFunction, Description("Provides the price of the requested menu item.")]
        public string GetItemPrice(
            [Description("The name of the menu item.")]
        string menuItem)
        {
            return "$9.99";
        }
    }
}
