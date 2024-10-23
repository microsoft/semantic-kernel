// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI.Chat;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using xRetry;

namespace ChatCompletion;

/// <summary>
/// This example demonstrates how to use Azure OpenAI Chat Completion with data.
/// </summary>
/// <value>
/// Set-up instructions:
/// <para>1. Upload the following content in Azure Blob Storage in a .txt file.</para>
/// <para>You can follow the steps here: <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/use-your-data-quickstart"/></para>
/// <para>
/// Emily and David, two passionate scientists, met during a research expedition to Antarctica.
/// Bonded by their love for the natural world and shared curiosity,
/// they uncovered a groundbreaking phenomenon in glaciology that could
/// potentially reshape our understanding of climate change.
/// </para>
/// 2. Set your secrets:
/// <para> dotnet user-secrets set "AzureAISearch:Endpoint" "https://... .search.windows.net"</para>
/// <para> dotnet user-secrets set "AzureAISearch:ApiKey" "{Key from your Search service resource}"</para>
/// <para> dotnet user-secrets set "AzureAISearch:IndexName" "..."</para>
/// </value>
public class AzureOpenAIWithData_ChatCompletion(ITestOutputHelper output) : BaseTest(output)
{
    [RetryFact(typeof(HttpOperationException))]
    public async Task ExampleWithChatCompletionAsync()
    {
        Console.WriteLine("=== Example with Chat Completion ===");

        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        var chatHistory = new ChatHistory();

        // First question without previous context based on uploaded content.
        var ask = "How did Emily and David meet?";
        chatHistory.AddUserMessage(ask);

        // Chat Completion example
        var dataSource = GetAzureSearchDataSource();
        var promptExecutionSettings = new AzureOpenAIPromptExecutionSettings { AzureChatDataSource = dataSource };

        var chatCompletion = kernel.GetRequiredService<IChatCompletionService>();

        var chatMessage = await chatCompletion.GetChatMessageContentAsync(chatHistory, promptExecutionSettings);

        var response = chatMessage.Content!;

        // Output
        // Ask: How did Emily and David meet?
        // Response: Emily and David, both passionate scientists, met during a research expedition to Antarctica.
        Console.WriteLine($"Ask: {ask}");
        Console.WriteLine($"Response: {response}");

        var citations = GetCitations(chatMessage);

        OutputCitations(citations);

        Console.WriteLine();

        // Chat history maintenance
        chatHistory.AddAssistantMessage(response);

        // Second question based on uploaded content.
        ask = "What are Emily and David studying?";
        chatHistory.AddUserMessage(ask);

        // Chat Completion Streaming example
        Console.WriteLine($"Ask: {ask}");
        Console.WriteLine("Response: ");

        await foreach (var word in chatCompletion.GetStreamingChatMessageContentsAsync(chatHistory, promptExecutionSettings))
        {
            Console.Write(word);
        }

        citations = GetCitations(chatMessage);

        OutputCitations(citations);

        Console.WriteLine(Environment.NewLine);
    }

    [RetryFact(typeof(HttpOperationException))]
    public async Task ExampleWithKernelAsync()
    {
        Console.WriteLine("=== Example with Kernel ===");

        var ask = "How did Emily and David meet?";

        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        var function = kernel.CreateFunctionFromPrompt("Question: {{$input}}");

        var dataSource = GetAzureSearchDataSource();
        var promptExecutionSettings = new AzureOpenAIPromptExecutionSettings { AzureChatDataSource = dataSource };

        // First question without previous context based on uploaded content.
        var response = await kernel.InvokeAsync(function, new(promptExecutionSettings) { ["input"] = ask });

        // Output
        // Ask: How did Emily and David meet?
        // Response: Emily and David, both passionate scientists, met during a research expedition to Antarctica.
        Console.WriteLine($"Ask: {ask}");
        Console.WriteLine($"Response: {response.GetValue<string>()}");
        Console.WriteLine();

        // Second question based on uploaded content.
        ask = "What are Emily and David studying?";
        response = await kernel.InvokeAsync(function, new(promptExecutionSettings) { ["input"] = ask });

        // Output
        // Ask: What are Emily and David studying?
        // Response: They are passionate scientists who study glaciology,
        // a branch of geology that deals with the study of ice and its effects.
        Console.WriteLine($"Ask: {ask}");
        Console.WriteLine($"Response: {response.GetValue<string>()}");
        Console.WriteLine();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureSearchChatDataSource"/> class.
    /// </summary>
#pragma warning disable AOAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
    private static AzureSearchChatDataSource GetAzureSearchDataSource()
    {
        return new AzureSearchChatDataSource
        {
            Endpoint = new Uri(TestConfiguration.AzureAISearch.Endpoint),
            Authentication = DataSourceAuthentication.FromApiKey(TestConfiguration.AzureAISearch.ApiKey),
            IndexName = TestConfiguration.AzureAISearch.IndexName
        };
    }

    /// <summary>
    /// Returns a collection of <see cref="ChatCitation"/>.
    /// </summary>
    private static IReadOnlyList<ChatCitation> GetCitations(ChatMessageContent chatMessageContent)
    {
        var message = chatMessageContent.InnerContent as OpenAI.Chat.ChatCompletion;
        var messageContext = message.GetMessageContext();

        return messageContext.Citations;
    }

    /// <summary>
    /// Outputs a collection of <see cref="ChatCitation"/>.
    /// </summary>
    private void OutputCitations(IReadOnlyList<ChatCitation> citations)
    {
        Console.WriteLine("Citations:");

        foreach (var citation in citations)
        {
            Console.WriteLine($"Chunk ID: {citation.ChunkId}");
            Console.WriteLine($"Title: {citation.Title}");
            Console.WriteLine($"File path: {citation.FilePath}");
            Console.WriteLine($"URI: {citation.Uri}");
            Console.WriteLine($"Content: {citation.Content}");
        }
    }

#pragma warning restore AOAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
}
