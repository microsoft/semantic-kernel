// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
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
        var chatExtensionsOptions = GetAzureChatExtensionsOptions();
        var promptExecutionSettings = new OpenAIPromptExecutionSettings { AzureChatExtensionsOptions = chatExtensionsOptions };

        var chatCompletion = kernel.GetRequiredService<IChatCompletionService>();

        var chatMessage = await chatCompletion.GetChatMessageContentAsync(chatHistory, promptExecutionSettings);

        var response = chatMessage.Content!;

        // Output
        // Ask: How did Emily and David meet?
        // Response: Emily and David, both passionate scientists, met during a research expedition to Antarctica.
        Console.WriteLine($"Ask: {ask}");
        Console.WriteLine($"Response: {response}");
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

        var chatExtensionsOptions = GetAzureChatExtensionsOptions();
        var promptExecutionSettings = new OpenAIPromptExecutionSettings { AzureChatExtensionsOptions = chatExtensionsOptions };

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
    /// Initializes a new instance of the <see cref="AzureOpenAIChatCompletionWithDataConfig"/> class.
    /// </summary>
    private static AzureChatExtensionsOptions GetAzureChatExtensionsOptions()
    {
        var azureSearchExtensionConfiguration = new AzureSearchChatExtensionConfiguration
        {
            SearchEndpoint = new Uri(TestConfiguration.AzureAISearch.Endpoint),
            Authentication = new OnYourDataApiKeyAuthenticationOptions(TestConfiguration.AzureAISearch.ApiKey),
            IndexName = TestConfiguration.AzureAISearch.IndexName
        };

        return new AzureChatExtensionsOptions
        {
            Extensions = { azureSearchExtensionConfiguration }
        };
    }
}
