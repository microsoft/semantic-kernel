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
    /// Default prompt execution settings with configured <see cref="OpenAIPromptExecutionSettings.ResultsPerPrompt"/> property.
    /// </summary>
    private readonly OpenAIPromptExecutionSettings _executionSettings = new()
    {
        MaxTokens = 200,
        FrequencyPenalty = 0,
        PresencePenalty = 0,
        Temperature = 1,
        TopP = 0.5,
        ResultsPerPrompt = 2
    };

    /// <summary>
    /// Example with multiple chat completion results using <see cref="AzureOpenAIChatCompletionService"/>.
    /// </summary>
    [Fact]
    public async Task AzureOpenAIMultipleChatCompletionResultsAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Multiple Chat Completion Results ========");

        var kernel = Kernel
            .CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                serviceId: TestConfiguration.AzureOpenAI.ChatModelId)
            .Build();

        await UsingKernelAsync(kernel);
        await UsingChatCompletionServiceAsync(kernel.GetRequiredService<IChatCompletionService>());
    }

    /// <summary>
    /// Example with multiple chat completion results using <see cref="OpenAIChatCompletionService"/>.
    /// </summary>
    [Fact]
    public async Task OpenAIMultipleChatCompletionResultsAsync()
    {
        Console.WriteLine("======== Open AI - Multiple Chat Completion Results ========");

        var kernel = Kernel
            .CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        await UsingKernelAsync(kernel);
        await UsingChatCompletionServiceAsync(kernel.GetRequiredService<IChatCompletionService>());
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
        var function = KernelFunctionFactory.CreateFromPrompt("Write one paragraph about why AI is awesome", executionSettings, "GetParagraph");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);

        kernel.Plugins.Add(plugin);

        // Add function result selection filter.
        kernel.FunctionInvocationFilters.Add(new FunctionResultSelectionFilter(this.Output));

        // Inside our main request, we call MyPlugin.GetParagraph function for text summarization.
        // Taking into account that MyPlugin.GetParagraph function produces 3 results, for text summarization we need to choose only one of them.
        // During execution, the filter will be invoked, which will select and return only 1 result, which will be inserted in our main request for summarization.
        var result = await kernel.InvokePromptAsync("Summarize this text: {{MyPlugin.GetParagraph}}");

        // It's possible to check what prompt was rendered for our main request.
        Console.WriteLine($"Rendered prompt: '{result.RenderedPrompt}'");

        // Output:
        // Rendered prompt: 'Summarize this text: AI is awesome because...'
    }

    /// <summary>
    /// Example of filter which is responsible for result selection in case if some function produces multiple results.
    /// </summary>
    private class FunctionResultSelectionFilter(ITestOutputHelper output) : IFunctionInvocationFilter
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

    /// <summary>
    /// Example with multiple chat completion results using <see cref="Kernel"/>.
    /// </summary>
    private async Task UsingKernelAsync(Kernel kernel)
    {
        Console.WriteLine("======== Using Kernel ========");

        var contents = await kernel.InvokePromptAsync<IReadOnlyList<KernelContent>>("Write one paragraph about why AI is awesome", new(this._executionSettings));

        foreach (var content in contents!)
        {
            Console.Write(content.ToString() ?? string.Empty);
            Console.WriteLine("\n-------------\n");
        }

        Console.WriteLine();
    }

    /// <summary>
    /// Example with multiple chat completion results using <see cref="IChatCompletionService"/>.
    /// </summary>
    private async Task UsingChatCompletionServiceAsync(IChatCompletionService chatCompletionService)
    {
        Console.WriteLine("======== Using IChatCompletionService ========");

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Write one paragraph about why AI is awesome");

        foreach (var chatMessageContent in await chatCompletionService.GetChatMessageContentsAsync(chatHistory, this._executionSettings))
        {
            Console.Write(chatMessageContent.Content ?? string.Empty);
            Console.WriteLine("\n-------------\n");
        }

        Console.WriteLine();
    }
}
