// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;

namespace ChatCompletion;

// The following example shows how to use Semantic Kernel with Azure OpenAI API
public class AzureOpenAI_ChatCompletion(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ChatPromptAsync()
    {
        Assert.NotNull(TestConfiguration.AzureOpenAI.ChatDeploymentName);
        Assert.NotNull(TestConfiguration.AzureOpenAI.Endpoint);

        StringBuilder chatPrompt = new("""
                                       <message role="system">You are a librarian, expert about books</message>
                                       <message role="user">Hi, I'm looking for book suggestions</message>
                                       """);

        var kernelBuilder = Kernel.CreateBuilder();
        if (string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.ApiKey))
        {
            kernelBuilder.AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                credentials: new DefaultAzureCredential(),
                modelId: TestConfiguration.AzureOpenAI.ChatModelId);
        }
        else
        {
            kernelBuilder.AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                modelId: TestConfiguration.AzureOpenAI.ChatModelId);
        }
        var kernel = kernelBuilder.Build();

        var reply = await kernel.InvokePromptAsync(chatPrompt.ToString());

        chatPrompt.AppendLine($"<message role=\"assistant\"><![CDATA[{reply}]]></message>");
        chatPrompt.AppendLine("<message role=\"user\">I love history and philosophy, I'd like to learn something new about Greece, any suggestion</message>");

        reply = await kernel.InvokePromptAsync(chatPrompt.ToString());

        Console.WriteLine(reply);
    }

    [Fact]
    public async Task ServicePromptAsync()
    {
        Console.WriteLine("======== Azure Open AI - Chat Completion ========");

        AzureOpenAIChatCompletionService chatCompletionService =
            string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.ApiKey) ?
            new(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                credentials: new DefaultAzureCredential(),
                modelId: TestConfiguration.AzureOpenAI.ChatModelId) :
            new(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey,
            modelId: TestConfiguration.AzureOpenAI.ChatModelId);

        await StartChatAsync(chatCompletionService);
    }

    /// <summary>
    /// Sample showing how to use Azure Open AI Chat Completion with Azure Default Credential.
    /// If local auth is disabled in the Azure Open AI deployment, you can use Azure Default Credential to authenticate.
    /// </summary>
    [Fact]
    public async Task DefaultAzureCredentialSampleAsync()
    {
        Console.WriteLine("======== Azure Open AI - Chat Completion with Azure Default Credential ========");

        AzureOpenAIChatCompletionService chatCompletionService =
            string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.ApiKey) ?
            new(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                credentials: new DefaultAzureCredential(),
                modelId: TestConfiguration.AzureOpenAI.ChatModelId) :
            new(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey,
            modelId: TestConfiguration.AzureOpenAI.ChatModelId);

        await StartChatAsync(chatCompletionService);
    }

    private async Task StartChatAsync(IChatCompletionService chatGPT)
    {
        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = new ChatHistory("You are a librarian, expert about books");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        OutputLastMessage(chatHistory);

        // First assistant message
        var reply = await chatGPT.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        OutputLastMessage(chatHistory);

        // Second user message
        chatHistory.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion");
        OutputLastMessage(chatHistory);

        // Second assistant message
        reply = await chatGPT.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        OutputLastMessage(chatHistory);
    }
}
