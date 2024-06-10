// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace ChatCompletion;

/// <summary>
/// These examples demonstrate the ways different content types are streamed by OpenAI LLM via the chat completion service.
/// </summary>
public class OpenAI_ChatCompletionStreaming(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This example demonstrates chat completion streaming using OpenAI.
    /// </summary>
    [Fact]
    public Task StreamOpenAIChatAsync()
    {
        Console.WriteLine("======== Open AI Chat Completion Streaming ========");

        OpenAIChatCompletionService chatCompletionService = new(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);

        return this.StartStreamingChatAsync(chatCompletionService);
    }

    /// <summary>
    /// This example demonstrates chat completion streaming using Azure OpenAI.
    /// </summary>
    [Fact]
    public Task StreamAzureOpenAIChatAsync()
    {
        Console.WriteLine("======== Azure Open AI Chat Completion Streaming ========");

        AzureOpenAIChatCompletionService chatCompletionService = new(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey,
            modelId: TestConfiguration.AzureOpenAI.ChatModelId);

        return this.StartStreamingChatAsync(chatCompletionService);
    }

    /// <summary>
    /// This example demonstrates how the chat completion service streams text content.
    /// It shows how to access the response update via StreamingChatMessageContent.Content property
    /// and alternatively via the StreamingChatMessageContent.Items property.
    /// </summary>
    [Fact]
    public async Task StreamTextContentAsync()
    {
        Console.WriteLine("======== Stream Text Content ========");

        // Create chat completion service
        AzureOpenAIChatCompletionService chatCompletionService = new(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey,
            modelId: TestConfiguration.AzureOpenAI.ChatModelId);

        // Create chat history with initial system and user messages
        ChatHistory chatHistory = new("You are a librarian, an expert on books.");
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions.");
        chatHistory.AddUserMessage("I love history and philosophy. I'd like to learn something new about Greece, any suggestion?");

        // Start streaming chat based on the chat history
        await foreach (StreamingChatMessageContent chatUpdate in chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            // Access the response update via StreamingChatMessageContent.Content property
            Console.Write(chatUpdate.Content);

            // Alternatively, the response update can be accessed via the StreamingChatMessageContent.Items property
            Console.Write(chatUpdate.Items.OfType<StreamingTextContent>().FirstOrDefault());
        }
    }

    /// <summary>
    /// This example demonstrates how the chat completion service streams raw function call content.
    /// See <see cref="FunctionCalling.OpenAI_FunctionCalling.RunStreamingChatAPIWithManualFunctionCallingAsync"/> for a sample demonstrating how to simplify
    /// function call content building out of streamed function call updates using the <see cref="FunctionCallContentBuilder"/>.
    /// </summary>
    [Fact]
    public async Task StreamFunctionCallContentAsync()
    {
        Console.WriteLine("======== Stream Function Call Content ========");

        // Create chat completion service
        OpenAIChatCompletionService chatCompletionService = new(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);

        // Create kernel with helper plugin.
        Kernel kernel = new();
        kernel.ImportPluginFromFunctions("HelperFunctions",
        [
            kernel.CreateFunctionFromMethod((string longTestString) => DateTime.UtcNow.ToString("R"), "GetCurrentUtcTime", "Retrieves the current time in UTC."),
        ]);

        // Create execution settings with manual function calling
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        // Create chat history with initial user question
        ChatHistory chatHistory = new();
        chatHistory.AddUserMessage("Hi, what is the current time?");

        // Start streaming chat based on the chat history
        await foreach (StreamingChatMessageContent chatUpdate in chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory, settings, kernel))
        {
            // Getting list of function call updates requested by LLM
            var streamingFunctionCallUpdates = chatUpdate.Items.OfType<StreamingFunctionCallUpdateContent>();

            // Iterating over function call updates. Please use the unctionCallContentBuilder to simplify function call content building.
            foreach (StreamingFunctionCallUpdateContent update in streamingFunctionCallUpdates)
            {
                Console.WriteLine($"Function call update: callId={update.CallId}, name={update.Name}, arguments={update.Arguments?.Replace("\n", "\\n")}, functionCallIndex={update.FunctionCallIndex}");
            }
        }
    }

    private async Task StartStreamingChatAsync(IChatCompletionService chatCompletionService)
    {
        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = new ChatHistory("You are a librarian, expert about books");
        OutputLastMessage(chatHistory);

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        OutputLastMessage(chatHistory);

        // First bot assistant message
        await StreamMessageOutputAsync(chatCompletionService, chatHistory, AuthorRole.Assistant);

        // Second user message
        chatHistory.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion?");
        OutputLastMessage(chatHistory);

        // Second bot assistant message
        await StreamMessageOutputAsync(chatCompletionService, chatHistory, AuthorRole.Assistant);
    }

    private async Task StreamMessageOutputAsync(IChatCompletionService chatCompletionService, ChatHistory chatHistory, AuthorRole authorRole)
    {
        bool roleWritten = false;
        string fullMessage = string.Empty;

        await foreach (var chatUpdate in chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            if (!roleWritten && chatUpdate.Role.HasValue)
            {
                Console.Write($"{chatUpdate.Role.Value}: {chatUpdate.Content}");
                roleWritten = true;
            }

            if (chatUpdate.Content is { Length: > 0 })
            {
                fullMessage += chatUpdate.Content;
                Console.Write(chatUpdate.Content);
            }
        }

        Console.WriteLine("\n------------------------");
        chatHistory.AddMessage(authorRole, fullMessage);
    }

    /// <summary>
    /// Outputs the last message of the chat history
    /// </summary>
    private void OutputLastMessage(ChatHistory chatHistory)
    {
        var message = chatHistory.Last();

        Console.WriteLine($"{message.Role}: {message.Content}");
        Console.WriteLine("------------------------");
    }
}
