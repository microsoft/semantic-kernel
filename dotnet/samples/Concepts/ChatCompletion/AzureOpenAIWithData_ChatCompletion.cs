// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Azure.AI.OpenAI.Chat;
using Microsoft.Extensions.DependencyInjection;
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

        await foreach (var update in chatCompletion.GetStreamingChatMessageContentsAsync(chatHistory, promptExecutionSettings))
        {
            Console.Write(update);

            var streamingCitations = GetCitations(update);

            OutputCitations(streamingCitations);
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
    /// This example shows how to use Azure OpenAI Chat Completion with data and function calling.
    /// Note: Using a data source and function calling is currently not supported in a single request. Enabling both features
    /// will result in the function calling information being ignored and the operation behaving as if only the data source was provided.
    /// More information about this limitation here: <see href="https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/openai/Azure.AI.OpenAI/README.md#use-your-own-data-with-azure-openai"/>.
    /// To address this limitation, consider separating function calling and data source across multiple requests in your solution design.
    /// The example demonstrates how to implement a retry mechanism for unanswered queries. If the current request uses an Azure Data Source, the logic retries using function calling, and vice versa.
    /// </summary>
    [Fact]
    public async Task ExampleWithFunctionCallingAsync()
    {
        Console.WriteLine("=== Example with Function Calling ===");

        var builder = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey);

        // Add retry filter.
        // This filter will evaluate if the model provided the answer to user's question.
        // If yes, it will return the result. Otherwise it will try to use Azure Data Source and function calling sequentially until
        // the requested information is provided. If both sources doesn't contain the requested information, the model will explain that in response.
        builder.Services.AddSingleton<IFunctionInvocationFilter, FunctionInvocationRetryFilter>();

        var kernel = builder.Build();

        // Import plugin.
        kernel.ImportPluginFromType<DataPlugin>();

        // Define response schema.
        // The model evaluates its own answer and provides a boolean flag,
        // which allows to understand whether the user's question was actually answered or not.
        // Based on that, it's possible to make a decision whether the source of information should be changed or the response
        // should be provided back to the user.
        var responseSchema =
            """
            {
                "type": "object",
                "properties": {
                    "Message": { "type": "string" },
                    "IsAnswered": { "type": "boolean" },
                }
            }
            """;

        // Define execution settings with response format and initial instructions.
        var promptExecutionSettings = new AzureOpenAIPromptExecutionSettings
        {
            ResponseFormat = "json_object",
            ChatSystemPrompt =
                "Provide concrete answers to user questions. " +
                "If you don't have the information - do not generate it, but respond accordingly. " +
                $"Use following JSON schema for all the responses: {responseSchema}. "
        };

        // First question without previous context based on uploaded content.
        var ask = "How did Emily and David meet?";

        // The answer to the first question is expected to be fetched from Azure Data Source (in this example Azure AI Search).
        // Azure Data Source is not enabled in initial execution settings, but is configured in retry filter.
        var response = await kernel.InvokePromptAsync(ask, new(promptExecutionSettings));
        var modelResult = ModelResult.Parse(response.ToString());

        // Output
        // Ask: How did Emily and David meet?
        // Response: Emily and David, both passionate scientists, met during a research expedition to Antarctica [doc1].
        Console.WriteLine($"Ask: {ask}");
        Console.WriteLine($"Response: {modelResult?.Message}");

        ask = "Can I have Emily's and David's emails?";

        // The answer to the second question is expected to be fetched from DataPlugin-GetEmails function using function calling.
        // Function calling is not enabled in initial execution settings, but is configured in retry filter.
        response = await kernel.InvokePromptAsync(ask, new(promptExecutionSettings));
        modelResult = ModelResult.Parse(response.ToString());

        // Output
        // Ask: Can I have their emails?
        // Response: Emily's email is emily@contoso.com and David's email is david@contoso.com.
        Console.WriteLine($"Ask: {ask}");
        Console.WriteLine($"Response: {modelResult?.Message}");
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
    private static IList<ChatCitation> GetCitations(ChatMessageContent chatMessageContent)
    {
        var message = chatMessageContent.InnerContent as OpenAI.Chat.ChatCompletion;
        var messageContext = message.GetMessageContext();

        return messageContext.Citations;
    }

    /// <summary>
    /// Returns a collection of <see cref="ChatCitation"/>.
    /// </summary>
    private static IList<ChatCitation>? GetCitations(StreamingChatMessageContent streamingContent)
    {
        var message = streamingContent.InnerContent as OpenAI.Chat.StreamingChatCompletionUpdate;
        var messageContext = message?.GetMessageContext();

        return messageContext?.Citations;
    }

    /// <summary>
    /// Outputs a collection of <see cref="ChatCitation"/>.
    /// </summary>
    private void OutputCitations(IList<ChatCitation>? citations)
    {
        if (citations is not null)
        {
            Console.WriteLine("Citations:");

            foreach (var citation in citations)
            {
                Console.WriteLine($"Chunk ID: {citation.ChunkId}");
                Console.WriteLine($"Title: {citation.Title}");
                Console.WriteLine($"File path: {citation.FilePath}");
                Console.WriteLine($"URL: {citation.Url}");
                Console.WriteLine($"Content: {citation.Content}");
            }
        }
    }

    /// <summary>
    /// Filter which performs the retry logic to answer user's question using different sources.
    /// Initially, if the model doesn't provide an answer, the filter will enable Azure Data Source and retry the same request.
    /// If Azure Data Source doesn't contain the requested information, the filter will disable it and enable function calling instead.
    /// If the answer is provided from the model itself or any source, it is returned back to the user.
    /// </summary>
    private sealed class FunctionInvocationRetryFilter : IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            // Retry logic for Azure Data Source and function calling is enabled only for Azure OpenAI prompt execution settings.
            if (context.Arguments.ExecutionSettings is not null &&
                context.Arguments.ExecutionSettings.TryGetValue(PromptExecutionSettings.DefaultServiceId, out var executionSettings) &&
                executionSettings is AzureOpenAIPromptExecutionSettings azureOpenAIPromptExecutionSettings)
            {
                // Store the initial data source and function calling configuration to reset it after filter execution.
                var initialAzureChatDataSource = azureOpenAIPromptExecutionSettings.AzureChatDataSource;
                var initialFunctionChoiceBehavior = azureOpenAIPromptExecutionSettings.FunctionChoiceBehavior;

                // Track which source of information was used during the execution to try both sources sequentially.
                var dataSourceUsed = initialAzureChatDataSource is not null;
                var functionCallingUsed = initialFunctionChoiceBehavior is not null;

                // Perform a request.
                await next(context);

                // Get and parse the result.
                var result = context.Result.GetValue<string>();
                var modelResult = ModelResult.Parse(result);

                // If the model could not answer the question, then retry the request using an alternate technique:
                // - If the Azure Data Source was used then disable it and enable function calling.
                // - If function calling was used then disable it and enable the Azure Data Source.
                while (modelResult?.IsAnswered is false || (!dataSourceUsed && !functionCallingUsed))
                {
                    // If Azure Data Source wasn't used - enable it.
                    if (azureOpenAIPromptExecutionSettings.AzureChatDataSource is null)
                    {
                        var dataSource = GetAzureSearchDataSource();

                        // Since Azure Data Source is enabled, the function calling should be disabled,
                        // because they are not supported together.
                        azureOpenAIPromptExecutionSettings.AzureChatDataSource = dataSource;
                        azureOpenAIPromptExecutionSettings.FunctionChoiceBehavior = null;

                        dataSourceUsed = true;
                    }
                    // Otherwise, if function calling wasn't used - enable it.
                    else if (azureOpenAIPromptExecutionSettings.FunctionChoiceBehavior is null)
                    {
                        // Since function calling is enabled, the Azure Data Source should be disabled,
                        // because they are not supported together.
                        azureOpenAIPromptExecutionSettings.AzureChatDataSource = null;
                        azureOpenAIPromptExecutionSettings.FunctionChoiceBehavior = FunctionChoiceBehavior.Auto();

                        functionCallingUsed = true;
                    }

                    // Perform a request.
                    await next(context);

                    // Get and parse the result.
                    result = context.Result.GetValue<string>();
                    modelResult = ModelResult.Parse(result);
                }

                // Reset prompt execution setting properties to the initial state.
                azureOpenAIPromptExecutionSettings.AzureChatDataSource = initialAzureChatDataSource;
                azureOpenAIPromptExecutionSettings.FunctionChoiceBehavior = initialFunctionChoiceBehavior;
            }
            // Otherwise, perform a default function invocation.
            else
            {
                await next(context);
            }
        }
    }

    /// <summary>
    /// Represents a model result with actual message and boolean flag which shows if user's question was answered or not.
    /// </summary>
    private sealed class ModelResult
    {
        public string Message { get; set; }

        public bool IsAnswered { get; set; }

        /// <summary>
        /// Parses model result.
        /// </summary>
        public static ModelResult? Parse(string? result)
        {
            if (string.IsNullOrWhiteSpace(result))
            {
                return null;
            }

            // With response format as "json_object", sometimes the JSON response string is coming together with annotation.
            // The following line normalizes the response string in order to deserialize it later.
            var normalized = result
                .Replace("```json", string.Empty)
                .Replace("```", string.Empty);

            return JsonSerializer.Deserialize<ModelResult>(normalized);
        }
    }

    /// <summary>
    /// Example of data plugin that provides a user information for demonstration purposes.
    /// </summary>
    private sealed class DataPlugin
    {
        private readonly Dictionary<string, string> _emails = new()
        {
            ["Emily"] = "emily@contoso.com",
            ["David"] = "david@contoso.com",
        };

        [KernelFunction]
        public List<string> GetEmails(List<string> users)
        {
            var emails = new List<string>();

            foreach (var user in users)
            {
                if (this._emails.TryGetValue(user, out var email))
                {
                    emails.Add(email);
                }
            }

            return emails;
        }
    }

#pragma warning restore AOAI001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
}
