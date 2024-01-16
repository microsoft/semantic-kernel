// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

// The following example shows how to use Semantic Kernel with streaming Multiple Results Chat Completion.
public class Example36_MultiCompletion : BaseTest
{
    [Fact]
    public Task AzureOpenAIMultiChatCompletionAsync()
    {
        WriteLine("======== Azure OpenAI - Multiple Chat Completion ========");

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
        WriteLine("======== Open AI - Multiple Chat Completion ========");

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
            Write(chatMessageChoice.Content ?? string.Empty);
            WriteLine("\n-------------\n");
        }

        WriteLine();
    }

    public Example36_MultiCompletion(ITestOutputHelper output) : base(output)
    {
    }
}
