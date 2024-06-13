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
    /// Example with multiple chat completion results using <see cref="Kernel"/>.
    /// </summary>
    private async Task UsingKernelAsync(Kernel kernel)
    {
        Console.WriteLine("======== Using Kernel ========");

        var chatMessageContents = await kernel.InvokePromptAsync<IReadOnlyList<ChatMessageContent>>("Write one paragraph about why AI is awesome", new(this._executionSettings));

        foreach (var chatMessageContent in chatMessageContents!)
        {
            Console.Write(chatMessageContent.Content ?? string.Empty);
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
