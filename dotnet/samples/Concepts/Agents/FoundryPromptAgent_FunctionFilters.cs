// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Azure.AI.Projects.Agents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Agents;

/// <summary>
/// Demonstrate usage of <see cref="IAutoFunctionInvocationFilter"/> for and
/// <see cref="IFunctionInvocationFilter"/> filters with a Microsoft Foundry Prompt Agent.
/// </summary>
public class FoundryPromptAgent_FunctionFilters(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    [Fact]
    public async Task UseFunctionInvocationFilterAsync()
    {
        // Define the agent
        (ChatCompletionAgent agent, ProjectsAgentVersion promptAgent) = await CreateAgentAsync(kernel => kernel.FunctionInvocationFilters.Add(new InvocationFilter()));

        // Invoke agent (non streaming)
        await InvokeAgentAsync(agent, promptAgent);
    }

    [Fact]
    public async Task UseFunctionInvocationFilterStreamingAsync()
    {
        // Define the agent
        (ChatCompletionAgent agent, ProjectsAgentVersion promptAgent) = await CreateAgentAsync(kernel => kernel.FunctionInvocationFilters.Add(new InvocationFilter()));

        // Invoke agent (streaming)
        await InvokeAgentStreamingAsync(agent, promptAgent);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task UseAutoFunctionInvocationFilterAsync(bool terminate)
    {
        // Define the agent
        (ChatCompletionAgent agent, ProjectsAgentVersion promptAgent) = await CreateAgentAsync(kernel => kernel.AutoFunctionInvocationFilters.Add(new AutoInvocationFilter(terminate)));

        // Invoke agent (non streaming)
        await InvokeAgentAsync(agent, promptAgent);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task UseAutoFunctionInvocationFilterWithStreamingAgentInvocationAsync(bool terminate)
    {
        // Define the agent
        (ChatCompletionAgent agent, ProjectsAgentVersion promptAgent) = await CreateAgentAsync(kernel => kernel.AutoFunctionInvocationFilters.Add(new AutoInvocationFilter(terminate)));

        // Invoke agent (streaming)
        await InvokeAgentStreamingAsync(agent, promptAgent);
    }

    private async Task InvokeAgentAsync(ChatCompletionAgent agent, ProjectsAgentVersion promptAgent)
    {
        ChatHistoryAgentThread agentThread = new();

        try
        {
            // Respond to user input, invoking functions where appropriate.
            ChatMessageContent message = new(AuthorRole.User, "What is the special soup?");
            await agent.InvokeAsync(message, agentThread).ToArrayAsync();

            // Display the entire chat history.
            ChatMessageContent[] history = await agentThread.GetMessagesAsync().ToArrayAsync();
            this.WriteChatHistory(history);
        }
        finally
        {
            await agentThread.DeleteAsync();
            await this.DeletePromptAgentAsync(promptAgent);
        }
    }

    private async Task InvokeAgentStreamingAsync(ChatCompletionAgent agent, ProjectsAgentVersion promptAgent)
    {
        ChatHistoryAgentThread agentThread = new();

        try
        {
            // Respond to user input, invoking functions where appropriate.
            ChatMessageContent message = new(AuthorRole.User, "What is the special soup?");
            await agent.InvokeStreamingAsync(message, agentThread).ToArrayAsync();

            // Display the entire chat history.
            ChatMessageContent[] history = await agentThread.GetMessagesAsync().ToArrayAsync();
            this.WriteChatHistory(history);
        }
        finally
        {
            await agentThread.DeleteAsync();
            await this.DeletePromptAgentAsync(promptAgent);
        }
    }

    private void WriteChatHistory(IEnumerable<ChatMessageContent> history)
    {
        Console.WriteLine("\n================================");
        Console.WriteLine("CHAT HISTORY");
        Console.WriteLine("================================");
        foreach (ChatMessageContent message in history)
        {
            this.WriteAgentChatMessage(message);
        }
    }

    private async Task<(ChatCompletionAgent Agent, ProjectsAgentVersion PromptAgent)> CreateAgentAsync(Action<Kernel> addFilter)
    {
        // Define the Prompt Agent. A Prompt Agent only calls functions declared on its definition,
        // so the plugin functions are declared as function tools.
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        ProjectsAgentVersion promptAgent =
            await this.CreatePromptAgentAsync(
                "Host",
                new DeclarativeAgentDefinition(DeploymentName) { Instructions = "Answer questions about the menu." }
                    .AddFunctionTools(plugin));

        // Semantic Kernel invokes the plugin functions locally, so the kernel filters apply to them.
        Kernel kernel = this.CreateKernel(promptAgent, plugin);
        addFilter(kernel);

        // Create the agent
        ChatCompletionAgent agent =
            new()
            {
                Kernel = kernel,
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };

        return (agent, promptAgent);
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
        public string GetItemPrice([Description("The name of the menu item.")] string menuItem)
        {
            return "$9.99";
        }
    }

    private sealed class InvocationFilter() : IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            System.Console.WriteLine($"FILTER INVOKED {nameof(InvocationFilter)} - {context.Function.Name}");

            // Execution the function
            await next(context);

            // Signal termination if the function is from the MenuPlugin
            if (context.Function.PluginName == nameof(MenuPlugin))
            {
                context.Result = new FunctionResult(context.Function, "BLOCKED");
            }
        }
    }

    private sealed class AutoInvocationFilter(bool terminate = true) : IAutoFunctionInvocationFilter
    {
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            System.Console.WriteLine($"FILTER INVOKED {nameof(AutoInvocationFilter)} - {context.Function.Name}");

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
