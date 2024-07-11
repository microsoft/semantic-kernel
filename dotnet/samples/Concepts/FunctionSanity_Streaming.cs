// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Sanity;

public class FunctionSanity_Streaming(ITestOutputHelper output) : BaseTest(output)
{
    private static readonly string[] s_userInput =
        [
            "Hello",
            "What is the special soup and what is its price?",
            "What is the special drink and what is its price?",
            "Thank you"
        ];

    //////////////////////////////
    // CHAT COMPLETION SERVICE

    [Fact]
    public async Task ServiceBasicTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        await RunServiceTestAsync(kernel);
    }

    [Fact]
    public async Task ServiceFunctionFilterTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        kernel.FunctionInvocationFilters.Add(new FunctionFilter());
        await RunServiceTestAsync(kernel);
    }

    [Fact]
    public async Task ServicePromptFilterTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        kernel.FunctionInvocationFilters.Add(new PromptFilter());
        await RunServiceTestAsync(kernel);
    }

    [Fact]
    public async Task ServiceAutoFilterTestAsync()
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.AddAzureOpenAIChatCompletion(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new AutoInvocationFilter());

        Kernel kernel = builder.Build();

        await RunServiceTestAsync(kernel);
    }

    //////////////////////////////
    // KERNEL PROMPT FUNCTION

    [Fact]
    public async Task KernelBasicTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        await RunKernelTestAsync(kernel);
    }

    [Fact]
    public async Task KernelFunctionFilterTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        kernel.FunctionInvocationFilters.Add(new FunctionFilter());
        await RunKernelTestAsync(kernel);
    }

    [Fact]
    public async Task KernelPromptFilterTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        kernel.FunctionInvocationFilters.Add(new PromptFilter());
        await RunKernelTestAsync(kernel);
    }

    [Fact]
    public async Task KernelAutoFilterTestAsync()
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.AddAzureOpenAIChatCompletion(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new AutoInvocationFilter());

        Kernel kernel = builder.Build();

        await RunKernelTestAsync(kernel);
    }

    //////////////////////////////
    // AGENT

    [Fact]
    public async Task AgentInvokeBasicTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        await RunAgentTestAsync(kernel);
    }

    [Fact]
    public async Task AgentInvokeFunctionFilterTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        kernel.FunctionInvocationFilters.Add(new FunctionFilter());
        await RunAgentTestAsync(kernel);
    }

    [Fact]
    public async Task AgentInvokeAutoFilterTestAsync()
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.AddAzureOpenAIChatCompletion(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new AutoInvocationFilter());

        Kernel kernel = builder.Build();

        await RunAgentTestAsync(kernel);
    }

    //////////////////////////////
    // KERNEL TEST
    private async Task RunKernelTestAsync(Kernel kernel)
    {
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        kernel.Plugins.Add(plugin);

        foreach (string input in s_userInput)
        {
            await InvokeWithInputAsync(input);
        }

        async Task InvokeWithInputAsync(string input)
        {
            Console.WriteLine($"[TextContent] {AuthorRole.User}: '{input}'");

            KernelFunction promptFunction = kernel.CreateFunctionFromPrompt(input, new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions });

            await foreach (StreamingChatMessageContent content in kernel.InvokeStreamingAsync<StreamingChatMessageContent>(promptFunction))
            {
                WriteContent(content);
            }
        }
    }

    //////////////////////////////
    // CHAT COMPLETION SERVICE TEST
    private async Task RunServiceTestAsync(Kernel kernel)
    {
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        kernel.Plugins.Add(plugin);

        IChatCompletionService service = kernel.GetRequiredService<IChatCompletionService>();

        ChatHistory chat = [];

        foreach (string input in s_userInput)
        {
            await InvokeWithInputAsync(input);
        }

        async Task InvokeWithInputAsync(string input)
        {
            ChatMessageContent userContent = new(AuthorRole.User, input);
            chat.Add(userContent);
            WriteContent(userContent);

            await foreach (StreamingChatMessageContent content in service.GetStreamingChatMessageContentsAsync(chat, new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions }, kernel))
            {
                WriteContent(content);
            }
        }
    }

    //////////////////////////////
    // AGENT TEST
    private async Task RunAgentTestAsync(Kernel kernel)
    {
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        kernel.Plugins.Add(plugin);

        ChatCompletionAgent agent =
            new()
            {
                Instructions = "Answer questions about the menu.",
                Kernel = kernel,
                ExecutionSettings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions },
            };

        ChatHistory chat = [];

        foreach (string input in s_userInput)
        {
            await InvokeWithInputAsync(input);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeWithInputAsync(string input)
        {
            ChatMessageContent userContent = new(AuthorRole.User, input);
            chat.Add(userContent);
            WriteContent(userContent);

            await foreach (StreamingChatMessageContent content in agent.InvokeStreamingAsync(chat))
            {
                //if (content.Role != AuthorRole.Tool) // %%% BIG PROBLEM
                //{
                //    chat.Add(content); // %%% AWKWARD (BUILDING HISTORY)
                //}

                WriteContent(content);
            }
        }
    }

    //////////////////////////////
    // UTILITY
    private void WriteContent(ChatMessageContent content)
    {
        Console.WriteLine($"[{content.Items.LastOrDefault()?.GetType().Name ?? "(empty)"}] {content.Role} : '{content.Content}'");
    }

    private void WriteContent(StreamingChatMessageContent content)
    {
        Console.WriteLine($"[{content.Items.LastOrDefault()?.GetType().Name ?? "(empty)"}] {content.Role} : '{content.Content}'");
    }

    //////////////////////////////
    // PLUGIN
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

    //////////////////////////////
    // FUNCTION FILTER
    private sealed class FunctionFilter : IFunctionInvocationFilter
    {
        public Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            if (context.Function.PluginName == nameof(MenuPlugin))
            {
                context.Result = new FunctionResult(context.Function, "Menu not available.");
                return Task.CompletedTask;
            }

            return next(context);
        }
    }

    //////////////////////////////
    // PROMPT FILTER
    private sealed class PromptFilter : IFunctionInvocationFilter
    {
        public Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            if (context.Function.PluginName != nameof(MenuPlugin))
            {
                StreamingChatMessageContent[] contents = [new StreamingChatMessageContent(AuthorRole.Assistant, "Intercepted message.")];
                IAsyncEnumerable<StreamingChatMessageContent> contentsAsync = contents.ToAsyncEnumerable();
                context.Result = new FunctionResult(context.Function, contentsAsync);
                return Task.CompletedTask;
            }

            return next(context);
        }
    }

    //////////////////////////////
    // AUTO INVOCATION FILTER
    private sealed class AutoInvocationFilter(bool terminate = true) : IAutoFunctionInvocationFilter
    {
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            ChatHistory chatHistory = context.ChatHistory;

            //await next(context); // %%% MIGHT BE SKIPPED / NO IMPACT HERE

            if (context.Function.PluginName == nameof(MenuPlugin))
            {
                context.Result = new FunctionResult(context.Function, "Menu not available.");
                context.Terminate = terminate;
            }
        }
    }
}
