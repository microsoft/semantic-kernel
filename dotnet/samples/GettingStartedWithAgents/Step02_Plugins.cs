// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Plugins;
using Resources;

namespace GettingStarted;

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> with a <see cref="KernelPlugin"/>,
/// and then eliciting its response to explicit user messages.
/// </summary>
public class Step02_Plugins(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task UseChatCompletionWithPlugin(bool useChatClient)
    {
        // Define the agent
        ChatCompletionAgent agent = CreateAgentWithPlugin(
                plugin: KernelPluginFactory.CreateFromType<MenuPlugin>(),
                instructions: "Answer questions about the menu.",
                name: "Host",
                useChatClient: useChatClient);

        // Create the chat history thread to capture the agent interaction.
        ChatHistoryAgentThread thread = new();

        // Respond to user input, invoking functions where appropriate.
        await InvokeAgentAsync(agent, thread, "Hello");
        await InvokeAgentAsync(agent, thread, "What is the special soup and its price?");
        await InvokeAgentAsync(agent, thread, "What is the special drink and its price?");
        await InvokeAgentAsync(agent, thread, "Thank you");
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task UseChatCompletionWithPluginEnumParameter(bool useChatClient)
    {
        // Define the agent
        ChatCompletionAgent agent = CreateAgentWithPlugin(
                KernelPluginFactory.CreateFromType<WidgetFactory>(),
                useChatClient: useChatClient);

        // Create the chat history thread to capture the agent interaction.
        ChatHistoryAgentThread thread = new();

        // Respond to user input, invoking functions where appropriate.
        await InvokeAgentAsync(agent, thread, "Create a beautiful red colored widget for me.");
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task UseChatCompletionWithPromptFunction(bool useChatClient)
    {
        // Define prompt function
        KernelFunction promptFunction =
            KernelFunctionFactory.CreateFromPrompt(
                promptTemplate:
                    """
                    Count the number of vowels in INPUT and report as a markdown table.

                    INPUT:
                    {{$input}}
                    """,
                description: "Counts the number of vowels");

        // Define the agent
        ChatCompletionAgent agent = CreateAgentWithPlugin(
                KernelPluginFactory.CreateFromFunctions("AgentPlugin", [promptFunction]),
                instructions: "You job is to only and always analyze the vowels in the user input without confirmation.",
                useChatClient: useChatClient);

        // Add a filter to the agent's kernel to log function invocations.
        agent.Kernel.FunctionInvocationFilters.Add(new PromptFunctionFilter());

        // Create the chat history thread to capture the agent interaction.
        ChatHistoryAgentThread thread = new();

        // Respond to user input, invoking functions where appropriate.
        await InvokeAgentAsync(agent, thread, "Who would know naught of art must learn, act, and then take his ease.");
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task UseChatCompletionWithTemplateExecutionSettings(bool useChatClient)
    {
        // Read the template resource
        string autoInvokeYaml = EmbeddedResource.Read("AutoInvokeTools.yaml");
        PromptTemplateConfig templateConfig = KernelFunctionYaml.ToPromptTemplateConfig(autoInvokeYaml);
        KernelPromptTemplateFactory templateFactory = new();

        // Define the agent:
        // Execution-settings with auto-invocation of plugins defined via the config.
        ChatCompletionAgent agent =
            new(templateConfig, templateFactory)
            {
                Kernel = this.CreateKernelWithChatCompletion(useChatClient, out var chatClient),
            };

        agent.Kernel.Plugins.AddFromType<WidgetFactory>();

        // Create the chat history thread to capture the agent interaction.
        ChatHistoryAgentThread thread = new();

        // Respond to user input, invoking functions where appropriate.
        await InvokeAgentAsync(agent, thread, "Create a beautiful red colored widget for me.");

        chatClient?.Dispose();
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task UseChatCompletionWithManualFunctionCalling(bool useChatClient)
    {
        // Define the agent
        ChatCompletionAgent agent = CreateAgentWithPlugin(
                KernelPluginFactory.CreateFromType<MenuPlugin>(),
                functionChoiceBehavior: FunctionChoiceBehavior.Auto(autoInvoke: false),
                useChatClient: useChatClient);

        /// Create the chat history thread to capture the agent interaction.
        ChatHistoryAgentThread thread = new();

        // Respond to user input, invoking functions where appropriate.
        await InvokeAgentAsync(agent, thread, "What is the special soup and its price?");
        await InvokeAgentAsync(agent, thread, "What is the special drink and its price?");
    }

    private ChatCompletionAgent CreateAgentWithPlugin(
        KernelPlugin plugin,
        string? instructions = null,
        string? name = null,
        FunctionChoiceBehavior? functionChoiceBehavior = null,
        bool useChatClient = false)
    {
        ChatCompletionAgent agent =
            new()
            {
                Instructions = instructions,
                Name = name,
                Kernel = this.CreateKernelWithChatCompletion(useChatClient, out _),
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = functionChoiceBehavior ?? FunctionChoiceBehavior.Auto() }),
            };

        // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
        agent.Kernel.Plugins.Add(plugin);

        return agent;
    }

    private async Task InvokeAgentAsync(ChatCompletionAgent agent, ChatHistoryAgentThread thread, string input)
    {
        ChatMessageContent message = new(AuthorRole.User, input);
        this.WriteAgentChatMessage(message);

        await foreach (ChatMessageContent response in agent.InvokeAsync(message, thread))
        {
            this.WriteAgentChatMessage(response);

            Task<FunctionResultContent>[] functionResults = await ProcessFunctionCalls(response, agent.Kernel).ToArrayAsync();
            thread.ChatHistory.Add(response);
            foreach (ChatMessageContent functionResult in functionResults.Select(result => result.Result.ToChatMessage()))
            {
                this.WriteAgentChatMessage(functionResult);
                thread.ChatHistory.Add(functionResult);
            }
        }
    }

    private async IAsyncEnumerable<Task<FunctionResultContent>> ProcessFunctionCalls(ChatMessageContent response, Kernel kernel)
    {
        foreach (FunctionCallContent functionCall in response.Items.OfType<FunctionCallContent>())
        {
            yield return functionCall.InvokeAsync(kernel);
        }
    }

    private sealed class PromptFunctionFilter : IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            System.Console.WriteLine($"INVOKING: {context.Function.Name}");
            await next.Invoke(context);
            System.Console.WriteLine($"RESULT: {context.Result}");
        }
    }
}
