﻿// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace ChatCompletion;

// The following example shows how to use Semantic Kernel with OpenAI API
public class OpenAI_ChatCompletion(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ServicePromptAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        Console.WriteLine("======== Open AI - Chat Completion ========");

        OpenAIChatCompletionService chatCompletionService = new(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);

        await StartChatAsync(chatCompletionService);
    }

    [Fact]
    public async Task ServicePromptWithInnerContentAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        Console.WriteLine("======== Open AI - Chat Completion ========");

        OpenAIChatCompletionService chatService = new(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = new ChatHistory("You are a librarian, expert about books");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        this.OutputLastMessage(chatHistory);

        // First assistant message
        var reply = await chatService.GetChatMessageContentAsync(chatHistory, new OpenAIPromptExecutionSettings { Logprobs = true, TopLogprobs = 3 });

        // Assistant message details
        var replyInnerContent = reply.InnerContent as OpenAI.Chat.ChatCompletion;

        OutputInnerContent(replyInnerContent!);
    }

    [Fact]
    public async Task ChatPromptAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        StringBuilder chatPrompt = new("""
                                       <message role="system">You are a librarian, expert about books</message>
                                       <message role="user">Hi, I'm looking for book suggestions</message>
                                       """);

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        var reply = await kernel.InvokePromptAsync(chatPrompt.ToString());

        chatPrompt.AppendLine($"<message role=\"assistant\"><![CDATA[{reply}]]></message>");
        chatPrompt.AppendLine("<message role=\"user\">I love history and philosophy, I'd like to learn something new about Greece, any suggestion</message>");

        reply = await kernel.InvokePromptAsync(chatPrompt.ToString());

        Console.WriteLine(reply);
    }

    /// <summary>
    /// Demonstrates how you can template a chat history call and get extra information from the response while using the kernel for invocation.
    /// </summary>
    /// <remarks>
    /// This is a breaking glass scenario, any attempt on running with different versions of OpenAI SDK that introduces breaking changes
    /// may cause breaking changes in the code below.
    /// </remarks>
    [Fact]
    public async Task ChatPromptWithInnerContentAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        StringBuilder chatPrompt = new("""
                                       <message role="system">You are a librarian, expert about books</message>
                                       <message role="user">Hi, I'm looking for book suggestions</message>
                                       """);

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        var functionResult = await kernel.InvokePromptAsync(chatPrompt.ToString(),
            new(new OpenAIPromptExecutionSettings { Logprobs = true, TopLogprobs = 3 }));

        var messageContent = functionResult.GetValue<ChatMessageContent>(); // Retrieves underlying chat message content from FunctionResult.
        var replyInnerContent = messageContent!.InnerContent as OpenAI.Chat.ChatCompletion; // Retrieves inner content from ChatMessageContent.

        OutputInnerContent(replyInnerContent!);
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

    /// <summary>
    /// Retrieve extra information from a <see cref="ChatMessageContent"/> inner content of type <see cref="OpenAI.Chat.ChatCompletion"/>.
    /// </summary>
    /// <param name="innerContent">An instance of <see cref="OpenAI.Chat.ChatCompletion"/> retrieved as an inner content of <see cref="ChatMessageContent"/>.</param>
    /// <remarks>
    /// This is a breaking glass scenario, any attempt on running with different versions of OpenAI SDK that introduces breaking changes
    /// may break the code below.
    /// </remarks>
    private void OutputInnerContent(OpenAI.Chat.ChatCompletion innerContent)
    {
        Console.WriteLine($"Message role: {innerContent.Role}"); // Available as a property of ChatMessageContent
        Console.WriteLine($"Message content: {innerContent.Content[0].Text}"); // Available as a property of ChatMessageContent

        Console.WriteLine($"Model: {innerContent.Model}"); // Model doesn't change per chunk, so we can get it from the first chunk only
        Console.WriteLine($"Created At: {innerContent.CreatedAt}");

        Console.WriteLine($"Finish reason: {innerContent.FinishReason}");
        Console.WriteLine($"Input tokens usage: {innerContent.Usage.InputTokenCount}");
        Console.WriteLine($"Output tokens usage: {innerContent.Usage.OutputTokenCount}");
        Console.WriteLine($"Total tokens usage: {innerContent.Usage.TotalTokenCount}");
        Console.WriteLine($"Refusal: {innerContent.Refusal} ");
        Console.WriteLine($"Id: {innerContent.Id}");
        Console.WriteLine($"System fingerprint: {innerContent.SystemFingerprint}");

        if (innerContent.ContentTokenLogProbabilities.Count > 0)
        {
            Console.WriteLine("Content token log probabilities:");
            foreach (var contentTokenLogProbability in innerContent.ContentTokenLogProbabilities)
            {
                Console.WriteLine($"Token: {contentTokenLogProbability.Token}");
                Console.WriteLine($"Log probability: {contentTokenLogProbability.LogProbability}");

                Console.WriteLine("   Top log probabilities for this token:");
                foreach (var topLogProbability in contentTokenLogProbability.TopLogProbabilities)
                {
                    Console.WriteLine($"   Token: {topLogProbability.Token}");
                    Console.WriteLine($"   Log probability: {topLogProbability.LogProbability}");
                    Console.WriteLine("   =======");
                }

                Console.WriteLine("--------------");
            }
        }

        if (innerContent.RefusalTokenLogProbabilities.Count > 0)
        {
            Console.WriteLine("Refusal token log probabilities:");
            foreach (var refusalTokenLogProbability in innerContent.RefusalTokenLogProbabilities)
            {
                Console.WriteLine($"Token: {refusalTokenLogProbability.Token}");
                Console.WriteLine($"Log probability: {refusalTokenLogProbability.LogProbability}");

                Console.WriteLine("   Refusal top log probabilities for this token:");
                foreach (var topLogProbability in refusalTokenLogProbability.TopLogProbabilities)
                {
                    Console.WriteLine($"   Token: {topLogProbability.Token}");
                    Console.WriteLine($"   Log probability: {topLogProbability.LogProbability}");
                    Console.WriteLine("   =======");
                }
            }
        }
    }
}
