// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace ChatCompletion;

/// <summary>
/// The following example shows how to use Semantic Kernel with multiple chat completion results.
/// </summary>
public class OpenAI_ChatCompletionMultipleChoices(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Example with multiple chat completion results using <see cref="Kernel"/>.
    /// </summary>
    [Fact]
    public async Task MultipleChatCompletionResultsUsingKernelAsync()
    {
        var kernel = Kernel
            .CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Execution settings with configured ResultsPerPrompt property.
        var executionSettings = new OpenAIPromptExecutionSettings { MaxTokens = 200, ResultsPerPrompt = 3 };

        var contents = await kernel.InvokePromptAsync<IReadOnlyList<KernelContent>>("Write a paragraph about why AI is awesome", new(executionSettings));

        foreach (var content in contents!)
        {
            Console.Write(content.ToString() ?? string.Empty);
            Console.WriteLine("\n-------------\n");
        }
    }

    /// <summary>
    /// Example with multiple chat completion results using <see cref="IChatCompletionService"/>.
    /// </summary>
    [Fact]
    public async Task MultipleChatCompletionResultsUsingChatCompletionServiceAsync()
    {
        var kernel = Kernel
            .CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Execution settings with configured ResultsPerPrompt property.
        var executionSettings = new OpenAIPromptExecutionSettings { MaxTokens = 200, ResultsPerPrompt = 3 };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Write a paragraph about why AI is awesome");

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        foreach (var chatMessageContent in await chatCompletionService.GetChatMessageContentsAsync(chatHistory, executionSettings))
        {
            Console.Write(chatMessageContent.Content ?? string.Empty);
            Console.WriteLine("\n-------------\n");
        }
    }

    /// <summary>
    /// This example shows how to handle multiple results in case if prompt template contains a call to another prompt function.
    /// <see cref="FunctionResultSelectionFilter"/> is used for result selection.
    /// </summary>
    [Fact]
    public async Task MultipleChatCompletionResultsInPromptTemplateAsync()
    {
        var kernel = Kernel
            .CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var executionSettings = new OpenAIPromptExecutionSettings { MaxTokens = 200, ResultsPerPrompt = 3 };

        // Initializing a function with execution settings for multiple results.
        // We ask AI to write one paragraph, but in execution settings we specified that we want 3 different results for this request.
        var function = KernelFunctionFactory.CreateFromPrompt("Write a paragraph about why AI is awesome", executionSettings, "GetParagraph");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);

        kernel.Plugins.Add(plugin);

        // Add function result selection filter.
        kernel.FunctionInvocationFilters.Add(new FunctionResultSelectionFilter(this.Output));

        // Inside our main request, we call MyPlugin.GetParagraph function for text summarization.
        // Taking into account that MyPlugin.GetParagraph function produces 3 results, for text summarization we need to choose only one of them.
        // Registered filter will be invoked during execution, which will select and return only 1 result, and this result will be inserted in our main request for summarization.
        var result = await kernel.InvokePromptAsync("Summarize this text: {{MyPlugin.GetParagraph}}");

        // It's possible to check what prompt was rendered for our main request.
        Console.WriteLine($"Rendered prompt: '{result.RenderedPrompt}'");

        // Output:
        // Rendered prompt: 'Summarize this text: AI is awesome because...'
    }

    /// <summary>
    /// Example of filter which is responsible for result selection in case if some function produces multiple results.
    /// </summary>
    private sealed class FunctionResultSelectionFilter(ITestOutputHelper output) : IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            await next(context);

            // Selection logic for function which is expected to produce multiple results.
            if (context.Function.Name == "GetParagraph")
            {
                // Get multiple results from function invocation
                var contents = context.Result.GetValue<IReadOnlyList<KernelContent>>()!;

                output.WriteLine("Multiple results:");

                foreach (var content in contents)
                {
                    output.WriteLine(content.ToString());
                }

                // Select first result for correct prompt rendering
                var selectedContent = contents[0];
                context.Result = new FunctionResult(context.Function, selectedContent, context.Kernel.Culture, selectedContent.Metadata);
            }
        }
    }
}
