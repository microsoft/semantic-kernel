// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Agents;

/// <summary>
/// Demonstrate usage of <see cref="IAutoFunctionInvocationFilter"/> for both direction invocation
/// of <see cref="ChatCompletionAgent"/> and via <see cref="AgentChat"/>.
/// </summary>
public class ChatCompletion_FunctionTermination(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseAutoFunctionInvocationFilterWithAgentInvocationAsync()
    {
        // Define the agent
        ChatCompletionAgent agent =
            new()
            {
                Instructions = "Answer questions about the menu.",
                Kernel = CreateKernelWithFilter(),
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
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

        // Display the entire chat history.
        WriteChatHistory(chat);

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            chat.Add(message);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(chat))
            {
                // Do not add a message implicitly added to the history.
                if (!response.Items.Any(i => i is FunctionCallContent || i is FunctionResultContent))
                {
                    chat.Add(response);
                }

                this.WriteAgentChatMessage(response);
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
                Kernel = CreateKernelWithFilter(),
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
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

        // Display the entire chat history.
        WriteChatHistory(await chat.GetChatMessagesAsync().ToArrayAsync());

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            chat.AddChatMessage(message);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in chat.InvokeAsync(agent))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }

    [Fact]
    public async Task UseAutoFunctionInvocationFilterWithStreamingAgentInvocationAsync()
    {
        // Define the agent
        ChatCompletionAgent agent =
            new()
            {
                Instructions = "Answer questions about the menu.",
                Kernel = CreateKernelWithFilter(),
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
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

        // Display the entire chat history.
        WriteChatHistory(chat);

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            chat.Add(message);
            this.WriteAgentChatMessage(message);

            int historyCount = chat.Count;

            bool isFirst = false;
            await foreach (StreamingChatMessageContent response in agent.InvokeStreamingAsync(chat))
            {
                if (string.IsNullOrEmpty(response.Content))
                {
                    continue;
                }

                if (!isFirst)
                {
                    Console.WriteLine($"\n# {response.Role} - {response.AuthorName ?? "*"}:");
                    isFirst = true;
                }

                Console.WriteLine($"\t > streamed: '{response.Content}'");
            }

            if (historyCount <= chat.Count)
            {
                for (int index = historyCount; index < chat.Count; index++)
                {
                    this.WriteAgentChatMessage(chat[index]);
                }
            }
        }
    }

    [Fact]
    public async Task UseAutoFunctionInvocationFilterWithStreamingAgentChatAsync()
    {
        // Define the agent
        ChatCompletionAgent agent =
            new()
            {
                Instructions = "Answer questions about the menu.",
                Kernel = CreateKernelWithFilter(),
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
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

        // Display the entire chat history.
        WriteChatHistory(await chat.GetChatMessagesAsync().ToArrayAsync());

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            chat.AddChatMessage(message);
            this.WriteAgentChatMessage(message);

            bool isFirst = false;
            await foreach (StreamingChatMessageContent response in chat.InvokeStreamingAsync(agent))
            {
                if (string.IsNullOrEmpty(response.Content))
                {
                    continue;
                }

                if (!isFirst)
                {
                    Console.WriteLine($"\n# {response.Role} - {response.AuthorName ?? "*"}:");
                    isFirst = true;
                }

                Console.WriteLine($"\t > streamed: '{response.Content}'");
            }
        }
    }

    private void WriteChatHistory(IEnumerable<ChatMessageContent> chat)
    {
        Console.WriteLine("================================");
        Console.WriteLine("CHAT HISTORY");
        Console.WriteLine("================================");
        foreach (ChatMessageContent message in chat)
        {
            this.WriteAgentChatMessage(message);
        }
    }

    private Kernel CreateKernelWithFilter()
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        base.AddChatCompletionToKernel(builder);

        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new AutoInvocationFilter());

        return builder.Build();
    }

    private sealed class MenuPlugin
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
