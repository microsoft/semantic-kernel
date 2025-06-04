// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted;

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> and
/// eliciting its response to three explicit user messages.
/// </summary>
public class Step08_AgentAsKernelFunction(ITestOutputHelper output) : BaseAgentsTest(output)
{
    protected override bool ForceOpenAI { get; } = true;

    [Fact]
    public async Task SalesAssistantAgent()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        kernel.Plugins.AddFromType<OrderPlugin>();
        kernel.AutoFunctionInvocationFilters.Add(new AutoFunctionInvocationFilter(this.Output));

        // Define the agent
        ChatCompletionAgent agent =
            new()
            {
                Name = "SalesAssistant",
                Instructions = "You are a sales assistant. Place orders for items the user requests.",
                Kernel = kernel,
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };

        // Invoke the agent and display the responses
        var responseItems = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "Place an order for a black boot."));
        await foreach (ChatMessageContent responseItem in responseItems)
        {
            this.WriteAgentChatMessage(responseItem);
        }
    }

    [Fact]
    public async Task RefundAgent()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        kernel.Plugins.AddFromType<RefundPlugin>();
        kernel.AutoFunctionInvocationFilters.Add(new AutoFunctionInvocationFilter(this.Output));

        // Define the agent
        ChatCompletionAgent agent =
            new()
            {
                Name = "RefundAgent",
                Instructions = "You are a refund agent. Help the user with refunds.",
                Kernel = kernel,
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };

        // Invoke the agent and display the responses
        var responseItems = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "I want a refund for a black boot."));
        await foreach (ChatMessageContent responseItem in responseItems)
        {
            this.WriteAgentChatMessage(responseItem);
        }
    }

    [Fact]
    public async Task MultipleAgents()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        var agentPlugin = KernelPluginFactory.CreateFromFunctions("AgentPlugin",
            [
                AgentKernelFunctionFactory.CreateFromAgent(this.CreateSalesAssistant()),
                AgentKernelFunctionFactory.CreateFromAgent(this.CreateRefundAgent())
            ]);
        kernel.Plugins.Add(agentPlugin);
        kernel.AutoFunctionInvocationFilters.Add(new AutoFunctionInvocationFilter(this.Output));

        // Define the agent
        ChatCompletionAgent agent =
            new()
            {
                Name = "ShoppingAssistant",
                Instructions = "You are a sales assistant. Delegate to the provided agents to help the user with placing orders and requesting refunds.",
                Kernel = kernel,
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };

        // Invoke the agent and display the responses
        string[] messages =
            [
                "Place an order for a black boot.",
                "Now I want a refund for the black boot."
            ];

        AgentThread? agentThread = null;
        foreach (var message in messages)
        {
            var responseItems = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, message), agentThread);
            await foreach (var responseItem in responseItems)
            {
                agentThread = responseItem.Thread;
                this.WriteAgentChatMessage(responseItem.Message);
            }
        }
    }

    #region private
    private ChatCompletionAgent CreateSalesAssistant()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        kernel.Plugins.AddFromType<OrderPlugin>();
        kernel.AutoFunctionInvocationFilters.Add(new AutoFunctionInvocationFilter(this.Output));

        // Define the agent
        return new()
        {
            Name = "SalesAssistant",
            Instructions = "You are a sales assistant. Place orders for items the user requests.",
            Description = "Agent to invoke to place orders for items the user requests.",
            Kernel = kernel,
            Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
        };
    }

    private ChatCompletionAgent CreateRefundAgent()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        kernel.Plugins.AddFromType<RefundPlugin>();
        kernel.AutoFunctionInvocationFilters.Add(new AutoFunctionInvocationFilter(this.Output));

        // Define the agent
        return new()
        {
            Name = "RefundAgent",
            Instructions = "You are a refund agent. Help the user with refunds.",
            Description = "Agent to invoke to execute a refund an item on behalf of the user.",
            Kernel = kernel,
            Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
        };
    }
    #endregion
}

public sealed class OrderPlugin
{
    [KernelFunction, Description("Place an order for the specified item.")]
    public string PlaceOrder([Description("The name of the item to be ordered.")] string itemName) => "success";
}

public sealed class RefundPlugin
{
    [KernelFunction, Description("Execute a refund for the specified item.")]
    public string ExecuteRefund(string itemName) => "success";
}

public sealed class AutoFunctionInvocationFilter(ITestOutputHelper output) : IAutoFunctionInvocationFilter
{
    public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
    {
        output.WriteLine($"Invoke: {context.Function.Name}");

        await next(context);
    }
}
