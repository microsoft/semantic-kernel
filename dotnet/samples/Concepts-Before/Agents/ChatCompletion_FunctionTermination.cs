// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Agents;

/// <summary>
/// Demonstrate usage of <see cref="IAutoFunctionInvocationFilter"/> for both direction invocation
/// of <see cref="ChatCompletionAgent"/> and via <see cref="AgentChat"/>.
/// </summary>
public class ChatCompletion_FunctionTermination(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task UseAutoFunctionInvocationFilterWithAgentInvocationAsync()
    {
        // Define the agent
        ChatCompletionAgent agent =
            new()
            {
                Instructions = "Answer questions about the menu.",
                Kernel = CreateKernelWithChatCompletion(),
                ExecutionSettings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions },
            };

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        agent.Kernel.Plugins.Add(plugin);

        /// Create the chat history to capture the agent interaction.
        ChatHistory chat = [];

        // Respond to user input, invoking functions where appropriate.
        await InvokeAgentAsync("Hello");
        await InvokeAgentAsync("What is the special soup?");
        await InvokeAgentAsync("What is the special drink?");
        await InvokeAgentAsync("Thank you");

        // Display the chat history.
        Console.WriteLine("================================");
        Console.WriteLine("CHAT HISTORY");
        Console.WriteLine("================================");
        foreach (ChatMessageContent message in chat)
        {
            this.WriteContent(message);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent userContent = new(AuthorRole.User, input);
            chat.Add(userContent);
            this.WriteContent(userContent);

            await foreach (ChatMessageContent content in agent.InvokeAsync(chat))
            {
                // Do not add a message implicitly added to the history.
                if (!content.Items.Any(i => i is FunctionCallContent || i is FunctionResultContent))
                {
                    chat.Add(content);
                }

                this.WriteContent(content);
            }
        }
    }

    [Fact]
    public async Task UseAutoFunctionInvocationFilterWithAgentChatAsync()
    {
        // Define the agent
        ChatCompletionAgent agent =
            new()
            {
                Instructions = "Answer questions about the menu.",
                Kernel = CreateKernelWithChatCompletion(),
                ExecutionSettings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions },
            };

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        agent.Kernel.Plugins.Add(plugin);

        // Create a chat for agent interaction.
        AgentGroupChat chat = new();

        // Respond to user input, invoking functions where appropriate.
        await InvokeAgentAsync("Hello");
        await InvokeAgentAsync("What is the special soup?");
        await InvokeAgentAsync("What is the special drink?");
        await InvokeAgentAsync("Thank you");

        // Display the chat history.
        Console.WriteLine("================================");
        Console.WriteLine("CHAT HISTORY");
        Console.WriteLine("================================");
        ChatMessageContent[] history = await chat.GetChatMessagesAsync().ToArrayAsync();
        for (int index = history.Length; index > 0; --index)
        {
            this.WriteContent(history[index - 1]);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent userContent = new(AuthorRole.User, input);
            chat.AddChatMessage(userContent);
            this.WriteContent(userContent);

            await foreach (ChatMessageContent content in chat.InvokeAsync(agent))
            {
                this.WriteContent(content);
            }
        }
    }

    private void WriteContent(ChatMessageContent content)
    {
        Console.WriteLine($"[{content.Items.LastOrDefault()?.GetType().Name ?? "(empty)"}] {content.Role} : '{content.Content}'");
    }

    private sealed class MenuPlugin
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

    private sealed class AutoInvocationFilter(bool terminate = true) : IAutoFunctionInvocationFilter
    {
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            // Execution the function
            await next(context);

            // Signal termination if the function is from the MenuPlugin
            if (context.Function.PluginName == nameof(MenuPlugin))
            {
                context.Terminate = terminate;
            }
        }
    }
}
