// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Sanity;

public class FunctionSanity(ITestOutputHelper output) : BaseTest(output)
{
    private static readonly string[] s_userInput =
        [
            //"Hello",
            "What is the special soup and what is its price?",
            "What is the special drink and what is its price?",
            //"Thank you"
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
    public async Task ServiceManualFunctionTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        await RunServiceTestAsync(kernel, ToolCallBehavior.EnableKernelFunctions);
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
    public async Task KernelManualFunctionTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        await RunKernelTestAsync(kernel, ToolCallBehavior.EnableKernelFunctions);
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
    public async Task AgentChatBasicTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        await RunAgentChatTestAsync(kernel);
    }

    [Fact]
    public async Task AgentInvokeManualFunctionTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        await RunAgentTestAsync(kernel, ToolCallBehavior.EnableKernelFunctions);
    }

    [Fact]
    public async Task AgentChatManualFunctionTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        await RunAgentChatTestAsync(kernel, ToolCallBehavior.EnableKernelFunctions);
    }

    [Fact]
    public async Task AgentInvokeFunctionFilterTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        kernel.FunctionInvocationFilters.Add(new FunctionFilter());
        await RunAgentTestAsync(kernel);
    }

    [Fact]
    public async Task AgentChatFunctionFilterTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        kernel.FunctionInvocationFilters.Add(new FunctionFilter());
        await RunAgentChatTestAsync(kernel);
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

    [Fact]
    public async Task AgentChatAutoFilterTestAsync()
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.AddAzureOpenAIChatCompletion(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new AutoInvocationFilter());

        Kernel kernel = builder.Build();

        await RunAgentChatTestAsync(kernel);
    }

    //////////////////////////////
    // ASSISTANT

    [Fact]
    public async Task AssistantInvokeBasicTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        await RunAgentTestAsync(kernel);
    }

    [Fact]
    public async Task AssistantChatBasicTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        await RunAgentChatTestAsync(kernel, useAssistant: true);
    }

    [Fact]
    public async Task AssistantInvokeManualFunctionTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        await RunAgentTestAsync(kernel, ToolCallBehavior.EnableKernelFunctions);
    }

    [Fact]
    public async Task AssistantChatManualFunctionTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        await RunAgentChatTestAsync(kernel, ToolCallBehavior.EnableKernelFunctions, useAssistant: true);
    }

    [Fact]
    public async Task AssistantInvokeFunctionFilterTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        kernel.FunctionInvocationFilters.Add(new FunctionFilter());
        await RunAgentTestAsync(kernel);
    }

    [Fact]
    public async Task AssistantChatFunctionFilterTestAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        kernel.FunctionInvocationFilters.Add(new FunctionFilter());
        await RunAgentChatTestAsync(kernel, useAssistant: true);
    }

    [Fact]
    public async Task AssistantInvokeAutoFilterTestAsync()
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

    [Fact]
    public async Task AssistantChatAutoFilterTestAsync()
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.AddAzureOpenAIChatCompletion(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new AutoInvocationFilter());

        Kernel kernel = builder.Build();

        await RunAgentChatTestAsync(kernel, useAssistant: true);
    }

    //////////////////////////////
    // KERNEL TEST
    private async Task RunKernelTestAsync(Kernel kernel, ToolCallBehavior? toolCallBehavior = null)
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

            KernelFunction promptFunction = kernel.CreateFunctionFromPrompt(input, new OpenAIPromptExecutionSettings() { ToolCallBehavior = toolCallBehavior ?? ToolCallBehavior.AutoInvokeKernelFunctions });

            ChatMessageContent content = (await kernel.InvokeAsync<ChatMessageContent>(promptFunction))!;
            this.WriteContent(content);
        }
    }

    //////////////////////////////
    // CHAT COMPLETION SERVICE TEST
    private async Task RunServiceTestAsync(Kernel kernel, ToolCallBehavior? toolCallBehavior = null)
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
            this.WriteContent(userContent);

            foreach (ChatMessageContent content in await service.GetChatMessageContentsAsync(chat, new OpenAIPromptExecutionSettings() { ToolCallBehavior = toolCallBehavior ?? ToolCallBehavior.AutoInvokeKernelFunctions }, kernel))
            {
                if (content.Role != AuthorRole.Tool && !content.Items.Any(i => i is FunctionCallContent || i is FunctionResultContent))
                {
                    chat.Add(content);
                }

                this.WriteContent(content);
            }
        }
    }

    //////////////////////////////
    // AGENT TEST
    private async Task RunAgentTestAsync(Kernel kernel, ToolCallBehavior? toolCallBehavior = null)
    {
        ChatCompletionAgent agent =
            new()
            {
                Instructions = "Answer questions about the menu.",
                Kernel = kernel,
                ExecutionSettings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = toolCallBehavior ?? ToolCallBehavior.AutoInvokeKernelFunctions },
            };

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        kernel.Plugins.Add(plugin);

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
            this.WriteContent(userContent);

            await foreach (ChatMessageContent content in agent.InvokeAsync(chat))
            {
                if (content.Role != AuthorRole.Tool && !content.Items.Any(i => i is FunctionCallContent || i is FunctionResultContent))
                {
                    chat.Add(content);
                }

                this.WriteContent(content);
            }
        }
    }

    //////////////////////////////
    // AGENT CHAT TEST
    private async Task RunAgentChatTestAsync(Kernel kernel, ToolCallBehavior? toolCallBehavior = null, bool useAssistant = false)
    {
        Agent agent =
            useAssistant ?
            await OpenAIAssistantAgent.CreateAsync(kernel, new(this.ApiKey, this.Endpoint), new() { ModelId = this.Model, Instructions = "Answer questions about the menu." }) :
            new ChatCompletionAgent()
            {
                Instructions = "Answer questions about the menu.",
                Kernel = kernel,
                ExecutionSettings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = toolCallBehavior ?? ToolCallBehavior.AutoInvokeKernelFunctions },
            };

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        kernel.Plugins.Add(plugin);

        AgentGroupChat chat = new();

        foreach (string input in s_userInput)
        {
            await InvokeWithInputAsync(input);
        }

        Console.WriteLine("================================");
        Console.WriteLine("PRIMARY HISTORY");
        Console.WriteLine("================================");
        IEnumerable<ChatMessageContent> history = chat.GetChatMessagesAsync().ToEnumerable().Reverse();
        foreach (ChatMessageContent content in history)
        {
            this.WriteContent(content);
        }

        if (useAssistant)
        {
            await ((OpenAIAssistantAgent)agent).DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeWithInputAsync(string input)
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

    //////////////////////////////
    // UTILITY
    private void WriteContent(ChatMessageContent content)
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

        [KernelFunction, Description("Provides the prices of the specials from the menu.")]
        [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1024:Use properties where appropriate", Justification = "Too smart")]
        public string GetPrices()
        {
            return @"
Clam Chowder: $9.99
Cobb Salad: $9.99
Chai Tea: $9.99
";
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
                context.Result = new FunctionResult(context.Function, new ChatMessageContent(AuthorRole.Assistant, "Intercepted message."));
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
            FunctionCallContent[] functionCalls = FunctionCallContent.GetFunctionCalls(context.ChatHistory.Last()).ToArray();

            await next(context);

            if (context.Function.PluginName == nameof(MenuPlugin))
            {
                //context.Result = new FunctionResult(context.Function, "Menu not available.");
                context.Terminate = terminate;
            }
        }
    }
}
