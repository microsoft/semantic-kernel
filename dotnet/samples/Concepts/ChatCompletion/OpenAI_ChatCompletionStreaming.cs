// Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
using System.Text;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
using System.Text;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
using System.Text;
>>>>>>> main
>>>>>>> Stashed changes
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    public Task StreamOpenAIChatAsync()
    {
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    public Task StreamOpenAIChatAsync()
    {
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
    public Task StreamOpenAIChatAsync()
    {
=======
>>>>>>> Stashed changes
    public async Task StreamServicePromptAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        Console.WriteLine("======== Open AI Chat Completion Streaming ========");

        OpenAIChatCompletionService chatCompletionService = new(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = new ChatHistory("You are a librarian, expert about books");
        OutputLastMessage(chatHistory);

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        OutputLastMessage(chatHistory);

        // First assistant message
        await StreamMessageOutputAsync(chatCompletionService, chatHistory, AuthorRole.Assistant);

        // Second user message
        chatHistory.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion?");
        OutputLastMessage(chatHistory);

        // Second assistant message
        await StreamMessageOutputAsync(chatCompletionService, chatHistory, AuthorRole.Assistant);
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    }

    /// <summary>
    /// This example demonstrates how the chat completion service streams text content.
    /// It shows how to access the response update via StreamingChatMessageContent.Content property
    /// and alternatively via the StreamingChatMessageContent.Items property.
    /// </summary>
    [Fact]
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    public async Task StreamTextContentAsync()
    {
        Console.WriteLine("======== Stream Text Content ========");

        // Create chat completion service
        AzureOpenAIChatCompletionService chatCompletionService = new(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey,
            modelId: TestConfiguration.AzureOpenAI.ChatModelId);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    public async Task StreamServicePromptTextAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        Console.WriteLine("======== Stream Text Content ========");

        // Create chat completion service
        OpenAIChatCompletionService chatCompletionService = new(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    /// This example demonstrates retrieving extra information chat completion streaming using OpenAI.
    /// </summary>
    /// <remarks>
    /// This is a breaking glass scenario, any attempt on running with different versions of OpenAI SDK that introduces breaking changes
    /// may break the code below.
    /// </remarks>
    [Fact]
    public async Task StreamServicePromptWithInnerContentAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        Console.WriteLine("======== OpenAI - Chat Completion Streaming (InnerContent) ========");

        var chatService = new OpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = new ChatHistory("Answer straight, do not explain your answer");
        this.OutputLastMessage(chatHistory);

        // First user message
        chatHistory.AddUserMessage("How many natural satellites are around Earth?");
        this.OutputLastMessage(chatHistory);

        await foreach (var chatUpdate in chatService.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            var innerContent = chatUpdate.InnerContent as OpenAI.Chat.StreamingChatCompletionUpdate;
            OutputInnerContent(innerContent!);
        }
    }

    /// <summary>
    /// Demonstrates how you can template a chat history call while using the kernel for invocation.
    /// </summary>
    [Fact]
    public async Task StreamChatPromptAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        Console.WriteLine("======== OpenAI - Chat Prompt Completion Streaming ========");

        StringBuilder chatPrompt = new("""
                                       <message role="system">You are a librarian, expert about books</message>
                                       <message role="user">Hi, I'm looking for book suggestions</message>
                                       """);

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        var reply = await StreamMessageOutputFromKernelAsync(kernel, chatPrompt.ToString());
        chatPrompt.AppendLine($"<message role=\"assistant\"><![CDATA[{reply}]]></message>");
        chatPrompt.AppendLine("<message role=\"user\">I love history and philosophy, I'd like to learn something new about Greece, any suggestion</message>");
        reply = await StreamMessageOutputFromKernelAsync(kernel, chatPrompt.ToString());
        Console.WriteLine(reply);
    }

    /// <summary>
    /// Demonstrates how you can template a chat history call and get extra information from the response while using the kernel for invocation.
    /// </summary>
    /// <remarks>
    /// This is a breaking glass scenario, any attempt on running with different versions of OllamaSharp library that introduces breaking changes
    /// may cause breaking changes in the code below.
    /// </remarks>
    [Fact]
    public async Task StreamChatPromptWithInnerContentAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        Console.WriteLine("======== OpenAI - Chat Prompt Completion Streaming (InnerContent) ========");

        StringBuilder chatPrompt = new("""
                                       <message role="system">Answer straight, do not explain your answer</message>
                                       <message role="user">How many natural satellites are around Earth?</message>
                                       """);

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        await foreach (var chatUpdate in kernel.InvokePromptStreamingAsync<StreamingChatMessageContent>(chatPrompt.ToString()))
        {
            var innerContent = chatUpdate.InnerContent as OpenAI.Chat.StreamingChatCompletionUpdate;
            OutputInnerContent(innerContent!);
        }
    }

    /// <summary>
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    /// This example demonstrates how the chat completion service streams raw function call content.
    /// See <see cref="FunctionCalling.FunctionCalling.RunStreamingChatCompletionApiWithManualFunctionCallingAsync"/> for a sample demonstrating how to simplify
    /// function call content building out of streamed function call updates using the <see cref="FunctionCallContentBuilder"/>.
    /// </summary>
    [Fact]
    public async Task StreamFunctionCallContentAsync()
    {
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false) };

        // Create chat history with initial user question
        ChatHistory chatHistory = [];
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

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    private async Task StartStreamingChatAsync(IChatCompletionService chatCompletionService)
    {
        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = new ChatHistory("You are a librarian, expert about books");
        OutputLastMessage(chatHistory);

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        OutputLastMessage(chatHistory);

        // First assistant message
        await StreamMessageOutputAsync(chatCompletionService, chatHistory, AuthorRole.Assistant);

        // Second user message
        chatHistory.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion?");
        OutputLastMessage(chatHistory);

        // Second assistant message
        await StreamMessageOutputAsync(chatCompletionService, chatHistory, AuthorRole.Assistant);
    }

    private async Task StreamMessageOutputAsync(IChatCompletionService chatCompletionService, ChatHistory chatHistory, AuthorRole authorRole)
    {
        bool roleWritten = false;
        string fullMessage = string.Empty;

        await foreach (var chatUpdate in chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory))
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    private async Task StreamMessageOutputAsync(OpenAIChatCompletionService chatCompletionService, ChatHistory chatHistory, AuthorRole authorRole)
    {
        bool roleWritten = false;
        string fullMessage = string.Empty;

        await foreach (var chatUpdate in chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory))
<<<<<<< Updated upstream
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

            // The last message in the chunk has the usage metadata.
            // https://platform.openai.com/docs/api-reference/chat/create#chat-create-stream_options
            if (chatUpdate.Metadata?["Usage"] is not null)
            {
                Console.WriteLine(chatUpdate.Metadata["Usage"]?.AsJson());
            }
<<<<<<< Updated upstream
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
        }

        Console.WriteLine("\n------------------------");
        chatHistory.AddMessage(authorRole, fullMessage);
    }
<<<<<<< Updated upstream
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

    private async Task<string> StreamMessageOutputFromKernelAsync(Kernel kernel, string prompt)
    {
        bool roleWritten = false;
        string fullMessage = string.Empty;
        await foreach (var chatUpdate in kernel.InvokePromptStreamingAsync<StreamingChatMessageContent>(prompt))
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        {
            if (!roleWritten && chatUpdate.Role.HasValue)
            {
                Console.Write($"{chatUpdate.Role.Value}: {chatUpdate.Content}");
                roleWritten = true;
            }
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< HEAD

=======
>>>>>>> main
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======

=======
>>>>>>> main
>>>>>>> Stashed changes
            if (chatUpdate.Content is { Length: > 0 })
            {
                fullMessage += chatUpdate.Content;
                Console.Write(chatUpdate.Content);
            }
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        }

        Console.WriteLine("\n------------------------");
        chatHistory.AddMessage(authorRole, fullMessage);
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

            // The last message in the chunk has the usage metadata.
            // https://platform.openai.com/docs/api-reference/chat/create#chat-create-stream_options
            if (chatUpdate.Metadata?["Usage"] is not null)
            {
                Console.WriteLine(chatUpdate.Metadata["Usage"]?.AsJson());
            }
        }
        Console.WriteLine("\n------------------------");
        return fullMessage;
    }

    /// <summary>
    /// Retrieve extra information from a <see cref="StreamingChatMessageContent"/> inner content of type <see cref="OpenAI.Chat.StreamingChatCompletionUpdate"/>.
    /// </summary>
    /// <param name="streamChunk">An instance of <see cref="OpenAI.Chat.StreamingChatCompletionUpdate"/> retrieved as an inner content of <see cref="StreamingChatMessageContent"/>.</param>
    /// <remarks>
    /// This is a breaking glass scenario, any attempt on running with different versions of OpenAI SDK that introduces breaking changes
    /// may break the code below.
    /// </remarks>
    private void OutputInnerContent(OpenAI.Chat.StreamingChatCompletionUpdate streamChunk)
    {
        Console.WriteLine($"Id: {streamChunk.CompletionId}");
        Console.WriteLine($"Model: {streamChunk.Model}");
        Console.WriteLine($"Created at: {streamChunk.CreatedAt}");
        Console.WriteLine($"Finish reason: {(streamChunk.FinishReason?.ToString() ?? "--")}");
        Console.WriteLine($"System fingerprint: {streamChunk.SystemFingerprint}");

        Console.WriteLine($"Content updates: {streamChunk.ContentUpdate.Count}");
        foreach (var contentUpdate in streamChunk.ContentUpdate)
        {
            Console.WriteLine($"   Kind: {contentUpdate.Kind}");
            if (contentUpdate.Kind == OpenAI.Chat.ChatMessageContentPartKind.Text)
            {
                Console.WriteLine($"   Text: {contentUpdate.Text}"); // Available as a properties of StreamingChatMessageContent.Items
                Console.WriteLine("   =======");
            }
            else if (contentUpdate.Kind == OpenAI.Chat.ChatMessageContentPartKind.Image)
            {
                Console.WriteLine($"   Image uri: {contentUpdate.ImageUri}");
                Console.WriteLine($"   Image media type: {contentUpdate.ImageBytesMediaType}");
                Console.WriteLine($"   Image detail: {contentUpdate.ImageDetailLevel}");
                Console.WriteLine($"   Image bytes: {contentUpdate.ImageBytes}");
                Console.WriteLine("   =======");
            }
            else if (contentUpdate.Kind == OpenAI.Chat.ChatMessageContentPartKind.Refusal)
            {
                Console.WriteLine($"   Refusal: {contentUpdate.Refusal}");
                Console.WriteLine("   =======");
            }
        }

        if (streamChunk.ContentTokenLogProbabilities.Count > 0)
        {
            Console.WriteLine("Content token log probabilities:");
            foreach (var contentTokenLogProbability in streamChunk.ContentTokenLogProbabilities)
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

        if (streamChunk.RefusalTokenLogProbabilities.Count > 0)
        {
            Console.WriteLine("Refusal token log probabilities:");
            foreach (var refusalTokenLogProbability in streamChunk.RefusalTokenLogProbabilities)
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

        // The last message in the chunk has the usage metadata.
        // https://platform.openai.com/docs/api-reference/chat/create#chat-create-stream_options
        if (streamChunk.Usage is not null)
        {
            Console.WriteLine($"Usage input tokens: {streamChunk.Usage.InputTokenCount}");
            Console.WriteLine($"Usage output tokens: {streamChunk.Usage.OutputTokenCount}");
            Console.WriteLine($"Usage total tokens: {streamChunk.Usage.TotalTokenCount}");
        }
        Console.WriteLine("------------------------");
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
    }
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    }
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
    }
>>>>>>> Stashed changes
}
