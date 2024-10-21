// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Agents;

/// <summary>
/// Demonstrate consuming "streaming" message for <see cref="OpenAIAssistantAgent"/>.
/// </summary>
public class OpenAIAssistant_Streaming(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseStreamingAssistantAgentAsync()
    {
        const string AgentName = "Parrot";
        const string AgentInstructions = "Repeat the user message in the voice of a pirate and then end with a parrot sound.";

        // Define the agent
        OpenAIAssistantAgent agent =
                await OpenAIAssistantAgent.CreateAsync(
                    kernel: new(),
                    clientProvider: this.GetClientProvider(),
                    definition: new OpenAIAssistantDefinition(this.Model)
                    {
                        Instructions = AgentInstructions,
                        Name = AgentName,
                        EnableCodeInterpreter = true,
                        Metadata = AssistantSampleMetadata,
                    });

        // Create a thread for the agent conversation.
        string threadId = await agent.CreateThreadAsync(new OpenAIThreadCreationOptions { Metadata = AssistantSampleMetadata });

        // Respond to user input
        await InvokeAgentAsync(agent, threadId, "Fortune favors the bold.");
        await InvokeAgentAsync(agent, threadId, "I came, I saw, I conquered.");
        await InvokeAgentAsync(agent, threadId, "Practice makes perfect.");

        // Output the entire chat history
        await DisplayChatHistoryAsync(agent, threadId);
    }

    [Fact]
    public async Task UseStreamingAssistantAgentWithPluginAsync()
    {
        const string AgentName = "Host";
        const string AgentInstructions = "Answer questions about the menu.";

        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                clientProvider: this.GetClientProvider(),
                definition: new OpenAIAssistantDefinition(this.Model)
                {
                    Instructions = AgentInstructions,
                    Name = AgentName,
                    Metadata = AssistantSampleMetadata,
                });

        // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        agent.Kernel.Plugins.Add(plugin);

        // Create a thread for the agent conversation.
        string threadId = await agent.CreateThreadAsync(new OpenAIThreadCreationOptions { Metadata = AssistantSampleMetadata });

        // Respond to user input
        await InvokeAgentAsync(agent, threadId, "What is the special soup and its price?");
        await InvokeAgentAsync(agent, threadId, "What is the special drink and its price?");

        // Output the entire chat history
        await DisplayChatHistoryAsync(agent, threadId);
    }

    [Fact]
    public async Task UseStreamingAssistantWithCodeInterpreterAsync()
    {
        const string AgentName = "MathGuy";
        const string AgentInstructions = "Solve math problems with code.";

        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                clientProvider: this.GetClientProvider(),
                definition: new OpenAIAssistantDefinition(this.Model)
                {
                    Instructions = AgentInstructions,
                    Name = AgentName,
                    EnableCodeInterpreter = true,
                    Metadata = AssistantSampleMetadata,
                });

        // Create a thread for the agent conversation.
        string threadId = await agent.CreateThreadAsync(new OpenAIThreadCreationOptions { Metadata = AssistantSampleMetadata });

        // Respond to user input
        await InvokeAgentAsync(agent, threadId, "Is 191 a prime number?");
        await InvokeAgentAsync(agent, threadId, "Determine the values in the Fibonacci sequence that that are less then the value of 101");

        // Output the entire chat history
        await DisplayChatHistoryAsync(agent, threadId);
    }

    // Local function to invoke agent and display the conversation messages.
    private async Task InvokeAgentAsync(OpenAIAssistantAgent agent, string threadId, string input)
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
            if (isCode != (response.Metadata?.ContainsKey(OpenAIAssistantAgent.CodeInterpreterMetadataKey) ?? false))
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

    private async Task DisplayChatHistoryAsync(OpenAIAssistantAgent agent, string threadId)
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
