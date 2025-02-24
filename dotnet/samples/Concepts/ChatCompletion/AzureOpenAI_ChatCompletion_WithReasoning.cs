// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using OpenAI.Chat;

namespace ChatCompletion;

// The following example shows how to use Semantic Kernel with Azure OpenAI API
public class AzureOpenAI_ChatCompletion_WithReasoning(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ChatPromptWithReasoningAsync()
    {
        Console.WriteLine("======== Azure Open AI - Chat Completion with Reasoning ========");

        Assert.NotNull(TestConfiguration.AzureOpenAI.ModelId);

        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                modelId: TestConfiguration.AzureOpenAI.ChatModelId)
            .Build();

        var reply = await ExecuteChatPromptWithReasoningAsync(kernel);

        Console.WriteLine(reply);
    }

    /// <summary>
    /// Sample showing how to use Azure Open AI Chat Completion with Azure Default Credential.
    /// If local auth is disabled in the Azure Open AI deployment, you can use Azure Default Credential to authenticate.
    /// </summary>
    [Fact]
    public async Task DefaultAzureCredentialSampleAsync()
    {
        Console.WriteLine("======== Azure Open AI - Chat Completion with Azure Default Credential ========");

        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                credentials: new DefaultAzureCredential(),
                modelId: TestConfiguration.AzureOpenAI.ChatModelId)
            .Build();

        var reply = await ExecuteChatPromptWithReasoningAsync(kernel);

        Console.WriteLine(reply);
    }

    private async Task<string> ExecuteChatPromptWithReasoningAsync(Kernel kernel)
    {
        // Create execution settings with high reasoning effort.
        var executionSettings = new AzureOpenAIPromptExecutionSettings //OpenAIPromptExecutionSettings
        {
            // Flags Azure SDK to use the new token property.
            SetNewMaxCompletionTokensEnabled = true,
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
