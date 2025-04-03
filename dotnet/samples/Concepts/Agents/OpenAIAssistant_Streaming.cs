// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Assistants;

namespace Agents;

/// <summary>
/// Demonstrate consuming "streaming" message for <see cref="OpenAIAssistantAgent"/>.
/// </summary>
public class OpenAIAssistant_Streaming(ITestOutputHelper output) : BaseAssistantTest(output)
{
    [Fact]
    public async Task UseStreamingAssistantAgentAsync()
    {
        // Define the assistant
        Assistant assistant =
            await this.AssistantClient.CreateAssistantAsync(
                this.Model,
                name: "Parrot",
                instructions: "Repeat the user message in the voice of a pirate and then end with a parrot sound.",
                metadata: SampleMetadata);

        // Create the agent
        OpenAIAssistantAgent agent = new(assistant, this.AssistantClient);

        // Create a thread for the agent conversation.
        OpenAIAssistantAgentThread agentThread = new(this.AssistantClient, metadata: SampleMetadata);

        // Respond to user input
        await InvokeAgentAsync(agent, agentThread, "Fortune favors the bold.");
        await InvokeAgentAsync(agent, agentThread, "I came, I saw, I conquered.");
        await InvokeAgentAsync(agent, agentThread, "Practice makes perfect.");

        // Output the entire chat history
        await DisplayChatHistoryAsync(agentThread);
    }

    [Fact]
    public async Task UseStreamingAssistantAgentWithPluginAsync()
    {
        // Define the assistant
        Assistant assistant =
            await this.AssistantClient.CreateAssistantAsync(
                this.Model,
                name: "Host",
                instructions: "Answer questions about the menu.",
                metadata: SampleMetadata);

        // Create the agent
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        OpenAIAssistantAgent agent = new(assistant, this.AssistantClient, [plugin]);

        // Create a thread for the agent conversation.
        OpenAIAssistantAgentThread agentThread = new(this.AssistantClient, metadata: SampleMetadata);

        // Respond to user input
        await InvokeAgentAsync(agent, agentThread, "What is the special soup and its price?");
        await InvokeAgentAsync(agent, agentThread, "What is the special drink and its price?");

        // Output the entire chat history
        await DisplayChatHistoryAsync(agentThread);
    }

    [Fact]
    public async Task UseStreamingAssistantWithCodeInterpreterAsync()
    {
        // Define the assistant
        Assistant assistant =
            await this.AssistantClient.CreateAssistantAsync(
                this.Model,
                name: "MathGuy",
                instructions: "Solve math problems with code.",
                enableCodeInterpreter: true,
                metadata: SampleMetadata);

        // Create the agent
        OpenAIAssistantAgent agent = new(assistant, this.AssistantClient);

        // Create a thread for the agent conversation.
        OpenAIAssistantAgentThread agentThread = new(this.AssistantClient, metadata: SampleMetadata);

        // Respond to user input
        await InvokeAgentAsync(agent, agentThread, "Is 191 a prime number?");
        await InvokeAgentAsync(agent, agentThread, "Determine the values in the Fibonacci sequence that that are less then the value of 101");

        // Output the entire chat history
        await DisplayChatHistoryAsync(agentThread);
    }

    // Local function to invoke agent and display the conversation messages.
    private async Task InvokeAgentAsync(OpenAIAssistantAgent agent, AgentThread agentThread, string input)
    {
        ChatMessageContent message = new(AuthorRole.User, input);
        this.WriteAgentChatMessage(message);

        // For this sample, also capture fully formed messages so we can display them later.
        ChatHistory history = [];
        Task OnNewMessage(ChatMessageContent message)
        {
            history.Add(message);
            return Task.CompletedTask;
        }

        bool isFirst = false;
        bool isCode = false;
        await foreach (StreamingChatMessageContent response in agent.InvokeStreamingAsync(message, agentThread, new() { OnIntermediateMessage = OnNewMessage }))
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

    private async Task DisplayChatHistoryAsync(OpenAIAssistantAgentThread agentThread)
    {
        Console.WriteLine("================================");
        Console.WriteLine("CHAT HISTORY");
        Console.WriteLine("================================");

        ChatMessageContent[] messages = await agentThread.GetMessagesAsync().ToArrayAsync();
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
