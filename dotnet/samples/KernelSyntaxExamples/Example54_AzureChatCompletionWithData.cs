// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using xRetry;
using Xunit.Abstractions;

namespace Examples;

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
public class Example54_AzureChatCompletionWithData : BaseTest
{
    [RetryFact(typeof(HttpOperationException))]
    public async Task ExampleWithChatCompletionAsync()
    {
        WriteLine("=== Example with Chat Completion ===");

        var chatCompletion = new AzureOpenAIChatCompletionWithDataService(GetCompletionWithDataConfig());
        var chatHistory = new ChatHistory();

        // First question without previous context based on uploaded content.
        var ask = "How did Emily and David meet?";
        chatHistory.AddUserMessage(ask);

        // Chat Completion example
        var chatMessage = (AzureOpenAIWithDataChatMessageContent)await chatCompletion.GetChatMessageContentAsync(chatHistory);

        var response = chatMessage.Content!;
        var toolResponse = chatMessage.ToolContent;

        // Output
        // Ask: How did Emily and David meet?
        // Response: Emily and David, both passionate scientists, met during a research expedition to Antarctica.
        WriteLine($"Ask: {ask}");
        WriteLine($"Response: {response}");
        WriteLine();

        // Chat history maintenance
        if (!string.IsNullOrEmpty(toolResponse))
        {
            chatHistory.AddMessage(AuthorRole.Tool, toolResponse);
        }

        chatHistory.AddAssistantMessage(response);

        // Second question based on uploaded content.
        ask = "What are Emily and David studying?";
        chatHistory.AddUserMessage(ask);

        // Chat Completion Streaming example
        WriteLine($"Ask: {ask}");
        WriteLine("Response: ");

        await foreach (var word in chatCompletion.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            Write(word);
        }

        WriteLine(Environment.NewLine);
    }

    [RetryFact(typeof(HttpOperationException))]
    public async Task ExampleWithKernelAsync()
    {
        WriteLine("=== Example with Kernel ===");

        var ask = "How did Emily and David meet?";

        var completionWithDataConfig = GetCompletionWithDataConfig();

        Kernel kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(config: completionWithDataConfig)
            .Build();

        var function = kernel.CreateFunctionFromPrompt("Question: {{$input}}");

        // First question without previous context based on uploaded content.
        var response = await kernel.InvokeAsync(function, new() { ["input"] = ask });

        // Output
        // Ask: How did Emily and David meet?
        // Response: Emily and David, both passionate scientists, met during a research expedition to Antarctica.
        WriteLine($"Ask: {ask}");
        WriteLine($"Response: {response.GetValue<string>()}");
        WriteLine();

        // Second question based on uploaded content.
        ask = "What are Emily and David studying?";
        response = await kernel.InvokeAsync(function, new() { ["input"] = ask });

        // Output
        // Ask: What are Emily and David studying?
        // Response: They are passionate scientists who study glaciology,
        // a branch of geology that deals with the study of ice and its effects.
        WriteLine($"Ask: {ask}");
        WriteLine($"Response: {response.GetValue<string>()}");
        WriteLine();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIChatCompletionWithDataConfig"/> class.
    /// </summary>
    private static AzureOpenAIChatCompletionWithDataConfig GetCompletionWithDataConfig()
    {
        return new AzureOpenAIChatCompletionWithDataConfig
        {
            CompletionModelId = TestConfiguration.AzureOpenAI.ChatDeploymentName,
            CompletionEndpoint = TestConfiguration.AzureOpenAI.Endpoint,
            CompletionApiKey = TestConfiguration.AzureOpenAI.ApiKey,
            DataSourceEndpoint = TestConfiguration.AzureAISearch.Endpoint,
            DataSourceApiKey = TestConfiguration.AzureAISearch.ApiKey,
            DataSourceIndex = TestConfiguration.AzureAISearch.IndexName
        };
    }

    public Example54_AzureChatCompletionWithData(ITestOutputHelper output) : base(output)
    {
    }
}
