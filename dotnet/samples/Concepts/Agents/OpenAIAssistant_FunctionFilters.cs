﻿// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Agents;

/// <summary>
/// Demonstrate usage of <see cref="IAutoFunctionInvocationFilter"/> for and
/// <see cref="IFunctionInvocationFilter"/> filters with <see cref="OpenAIAssistantAgent"/>
/// via <see cref="AgentChat"/>.
/// </summary>
public class OpenAIAssistant_FunctionFilters(ITestOutputHelper output) : BaseAgentsTest(output)
{
    protected override bool ForceOpenAI => true; // %%% REMOVE

    [Fact]
    public async Task UseFunctionInvocationFilterAsync()
    {
        // Define the agent
        OpenAIAssistantAgent agent = await CreateAssistantAsync(CreateKernelWithInvokeFilter());

        // Invoke assistant agent (non streaming)
        await InvokeAssistantAsync(agent);
    }

    [Fact]
    public async Task UseFunctionInvocationFilterStreamingAsync()
    {
        // Define the agent
        OpenAIAssistantAgent agent = await CreateAssistantAsync(CreateKernelWithInvokeFilter());

        // Invoke assistant agent (streaming)
        await InvokeAssistantStreamingAsync(agent);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task UseAutoFunctionInvocationFilterAsync(bool terminate)
    {
        // Define the agent
        OpenAIAssistantAgent agent = await CreateAssistantAsync(CreateKernelWithAutoFilter(terminate));

        // Invoke assistant agent (non streaming)
        await InvokeAssistantAsync(agent);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task UseAutoFunctionInvocationFilterWithStreamingAgentInvocationAsync(bool terminate)
    {
        // Define the agent
        OpenAIAssistantAgent agent = await CreateAssistantAsync(CreateKernelWithAutoFilter(terminate));

        // Invoke assistant agent (streaming)
        await InvokeAssistantStreamingAsync(agent);
    }

    private async Task InvokeAssistantAsync(OpenAIAssistantAgent agent)
    {
        // Create a thread for the agent conversation.
        AgentGroupChat chat = new();

        try
        {
            // Respond to user input, invoking functions where appropriate.
            ChatMessageContent message = new(AuthorRole.User, "What is the special soup?");
            chat.AddChatMessage(message);
            await chat.InvokeAsync(agent).ToArrayAsync();

            // Display the entire chat history.
            ChatMessageContent[] history = await chat.GetChatMessagesAsync().Reverse().ToArrayAsync();
            this.WriteChatHistory(history);
        }
        finally
        {
            await chat.ResetAsync();
            await agent.DeleteAsync();
        }
    }

    private async Task InvokeAssistantStreamingAsync(OpenAIAssistantAgent agent)
    {
        // Create a thread for the agent conversation.
        AgentGroupChat chat = new();

        try
        {
            // Respond to user input, invoking functions where appropriate.
            ChatMessageContent message = new(AuthorRole.User, "What is the special soup?");
            chat.AddChatMessage(message);
            await chat.InvokeStreamingAsync(agent).ToArrayAsync();

            // Display the entire chat history.
            ChatMessageContent[] history = await chat.GetChatMessagesAsync().Reverse().ToArrayAsync();
            this.WriteChatHistory(history);
        }
        finally
        {
            await chat.ResetAsync();
            await agent.DeleteAsync();
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

    private async Task<OpenAIAssistantAgent> CreateAssistantAsync(Kernel kernel)
    {
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                this.GetClientProvider(),
                new OpenAIAssistantDefinition(base.Model)
                {
                    Instructions = "Answer questions about the menu.",
                    Metadata = AssistantSampleMetadata,
                },
                kernel: kernel
            );

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        agent.Kernel.Plugins.Add(plugin);

        return agent;
    }

    private Kernel CreateKernelWithAutoFilter(bool terminate)
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        base.AddChatCompletionToKernel(builder);

        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new AutoInvocationFilter(terminate));

        return builder.Build();
    }

    private Kernel CreateKernelWithInvokeFilter()
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        base.AddChatCompletionToKernel(builder);

        builder.Services.AddSingleton<IFunctionInvocationFilter>(new InvocationFilter());

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
