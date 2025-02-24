// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel;
//using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;

namespace ChatCompletion;

// The following example shows how to use Semantic Kernel with Azure OpenAI API
public class OpenAI_ChatCompletion_WithReasoning(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ChatPromptWithReasoningAsync()
    {
        Console.WriteLine("======== Open AI - Chat Completion with Reasoning ========");

        Assert.NotNull(TestConfiguration.AzureOpenAI.ModelId);

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var reply = await ExecuteChatPromptWithReasoningAsync(kernel);

        Console.WriteLine(reply);
    }

    private async Task<string> ExecuteChatPromptWithReasoningAsync(Kernel kernel)
    {
        // Create execution settings with high reasoning effort.
        var executionSettings = new OpenAIPromptExecutionSettings //OpenAIPromptExecutionSettings
        {
            MaxTokens = 2000,
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(),
            // Note: reasoning effort is only available for reasoning models (at this moment o3-mini & o1 models)
            ReasoningEffort = ChatReasoningEffortLevel.High
        };

        // Create KernelArguments using the execution settings.
        var kernelArgs = new KernelArguments(executionSettings);

        StringBuilder chatPrompt = new("""
                                   <message role="system">You are an expert software engineer, specialized in the Semantic Kernel SDK and NET framework</message>
                                   <message role="user">Hi, Please craft me an example code in .NET using Semantic Kernel that implements a chat loop .</message>
                                   """);

        // Invoke the prompt with high reasoning effort.
        var reply = await kernel.InvokePromptAsync(chatPrompt.ToString(), kernelArgs);

        return reply.ToString();
    }
}
