// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Azure.AI.Projects.Agents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Responses;

namespace Agents;

/// <summary>
/// Demonstrate consuming "streaming" message for an agent that uses a Microsoft Foundry Prompt Agent.
/// </summary>
public class FoundryPromptAgent_Streaming(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    [Fact]
    public async Task UseStreamingFoundryPromptAgentAsync()
    {
        // Define the Prompt Agent
        ProjectsAgentVersion promptAgent =
            await this.CreatePromptAgentAsync(
                "Parrot",
                new DeclarativeAgentDefinition(DeploymentName)
                {
                    Instructions = "Repeat the user message in the voice of a pirate and then end with a parrot sound.",
                });

        // Create the agent
        ChatCompletionAgent agent =
            new()
            {
                Name = "Parrot",
                Kernel = this.CreateKernel(promptAgent),
            };

        // Create a thread for the agent conversation.
        ChatHistoryAgentThread agentThread = new();

        try
        {
            // Respond to user input
            await InvokeAgentAsync(agent, agentThread, "Fortune favors the bold.");
            await InvokeAgentAsync(agent, agentThread, "I came, I saw, I conquered.");
            await InvokeAgentAsync(agent, agentThread, "Practice makes perfect.");

            // Output the entire chat history
            await DisplayChatHistoryAsync(agentThread);
        }
        finally
        {
            await this.DeletePromptAgentAsync(promptAgent);
        }
    }

    [Fact]
    public async Task UseStreamingFoundryPromptAgentWithPluginAsync()
    {
        // Define the Prompt Agent. A Prompt Agent only calls functions declared on its definition,
        // so the plugin functions are declared as function tools.
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        ProjectsAgentVersion promptAgent =
            await this.CreatePromptAgentAsync(
                "Host",
                new DeclarativeAgentDefinition(DeploymentName) { Instructions = "Answer questions about the menu." }
                    .AddFunctionTools(plugin));

        // Create the agent
        ChatCompletionAgent agent =
            new()
            {
                Name = "Host",
                Kernel = this.CreateKernel(promptAgent, plugin),
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };

        // Create a thread for the agent conversation.
        ChatHistoryAgentThread agentThread = new();

        try
        {
            // Respond to user input
            await InvokeAgentAsync(agent, agentThread, "What is the special soup and its price?");
            await InvokeAgentAsync(agent, agentThread, "What is the special drink and its price?");

            // Output the entire chat history
            await DisplayChatHistoryAsync(agentThread);
        }
        finally
        {
            await this.DeletePromptAgentAsync(promptAgent);
        }
    }

    [Fact]
    public async Task UseStreamingFoundryPromptAgentWithCodeInterpreterAsync()
    {
        // Define the Prompt Agent with the code-interpreter tool.
        DeclarativeAgentDefinition definition = new(DeploymentName)
        {
            Instructions = "Solve math problems with code.",
        };
        definition.Tools.Add(
            ResponseTool.CreateCodeInterpreterTool(
                new CodeInterpreterToolContainer(
                    CodeInterpreterToolContainerConfiguration.CreateAutomaticContainerConfiguration())));
        ProjectsAgentVersion promptAgent = await this.CreatePromptAgentAsync("MathGuy", definition);

        // Create the agent. The code that the code interpreter runs is not streamed; only the answer text is.
        ChatCompletionAgent agent =
            new()
            {
                Name = "MathGuy",
                Kernel = this.CreateKernel(promptAgent),
            };

        // Create a thread for the agent conversation.
        ChatHistoryAgentThread agentThread = new();

        try
        {
            // Respond to user input
            await InvokeAgentAsync(agent, agentThread, "Is 191 a prime number?");
            await InvokeAgentAsync(agent, agentThread, "Determine the values in the Fibonacci sequence that that are less then the value of 101");

            // Output the entire chat history
            await DisplayChatHistoryAsync(agentThread);
        }
        finally
        {
            await this.DeletePromptAgentAsync(promptAgent);
        }
    }

    // Local function to invoke agent and display the conversation messages.
    private async Task InvokeAgentAsync(ChatCompletionAgent agent, AgentThread agentThread, string input)
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
        await foreach (StreamingChatMessageContent response in agent.InvokeStreamingAsync(message, agentThread, new() { OnIntermediateMessage = OnNewMessage }))
        {
            if (string.IsNullOrEmpty(response.Content))
            {
                StreamingFunctionCallUpdateContent? functionCall = response.Items.OfType<StreamingFunctionCallUpdateContent>().SingleOrDefault();
                if (functionCall?.Name != null)
                {
                    (string? pluginName, string functionName) = this.ParseFunctionName(functionCall.Name);
                    Console.WriteLine($"\n# {response.Role} - {response.AuthorName ?? "*"}: FUNCTION CALL - {$"{pluginName}." ?? string.Empty}{functionName}");
                }

                continue;
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

    private async Task DisplayChatHistoryAsync(ChatHistoryAgentThread agentThread)
    {
        Console.WriteLine("================================");
        Console.WriteLine("CHAT HISTORY");
        Console.WriteLine("================================");

        await foreach (ChatMessageContent message in agentThread.GetMessagesAsync())
        {
            this.WriteAgentChatMessage(message);
        }
    }

    public sealed class MenuPlugin
    {
        [KernelFunction, Description("Provides a list of specials from the menu.")]
        [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1024:Use properties where appropriate", Justification = "Too smart")]
        public string GetSpecials()
        {
            return
                """
                Special Soup: Clam Chowder
                Special Salad: Cobb Salad
                Special Drink: Chai Tea
                """;
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
