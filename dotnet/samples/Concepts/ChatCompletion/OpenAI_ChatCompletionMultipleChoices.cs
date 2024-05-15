// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace ChatCompletion;

// The following example shows how to use Semantic Kernel with streaming Multiple Results Chat Completion.
public class OpenAI_ChatCompletionMultipleChoices(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public Task AzureOpenAIMultiChatCompletionAsync()
    {
        Console.WriteLine("======== Azure OpenAI - Multiple Chat Completion ========");

        var chatCompletionService = new AzureOpenAIChatCompletionService(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey,
            modelId: TestConfiguration.AzureOpenAI.ChatModelId);

        return ChatCompletionAsync(chatCompletionService);
    }

    [Fact]
    public Task OpenAIMultiChatCompletionAsync()
    {
        Console.WriteLine("======== Open AI - Multiple Chat Completion ========");

        var chatCompletionService = new OpenAIChatCompletionService(
            TestConfiguration.OpenAI.ChatModelId,
            TestConfiguration.OpenAI.ApiKey);

        return ChatCompletionAsync(chatCompletionService);
    }

    private async Task ChatCompletionAsync(IChatCompletionService chatCompletionService)
    {
        var executionSettings = new OpenAIPromptExecutionSettings()
        {
            MaxTokens = 200,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
            Temperature = 1,
            TopP = 0.5,
            ResultsPerPrompt = 2,
        };

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Write one paragraph about why AI is awesome");

        foreach (var chatMessageChoice in await chatCompletionService.GetChatMessageContentsAsync(chatHistory, executionSettings))
        {
            Console.Write(chatMessageChoice.Content ?? string.Empty);
            Console.WriteLine("\n-------------\n");
        }

        Console.WriteLine();
    }
}
