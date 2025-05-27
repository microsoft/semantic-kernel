// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Functions;

namespace Agents;

#pragma warning disable SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

/// <summary>
/// Demonstrates the creation of a <see cref="ChatCompletionAgent"/> and adding capabilities
/// for contextual function selection to it. Contextual function selection involves using
/// Retrieval-Augmented Generation (RAG) to identify and select the most relevant functions
/// based on the current context. The provider vectorizes the function names and descriptions,
/// stores them in a specified vector store, and performs a vector search to find and provide
/// the most pertinent functions to the AI model/agent for a given context.
/// </summary>
public class ChatCompletion_ContextualFunctionSelection(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Shows how to configure agent to use <see cref="ContextualFunctionProvider"/>
    /// to enable contextual function selection.
    /// </summary>
    [Fact]
    private async Task SelectFunctionsRelevantToContext()
    {
        var embeddingGenerator = new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAIEmbeddings.Endpoint), new AzureCliCredential())
            .GetEmbeddingClient(TestConfiguration.AzureOpenAIEmbeddings.DeploymentName)
            .AsIEmbeddingGenerator(1536);

        // Create our agent.
        Kernel kernel = this.CreateKernelWithChatCompletion();
        ChatCompletionAgent agent =
            new()
            {
                Name = "ReviewGuru",
                Instructions = "You are a friendly assistant that summarizes key points and sentiments from customer reviews. " +
                               "For each response, list available functions",
                Kernel = kernel,
                Arguments = new(new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new FunctionChoiceBehaviorOptions { RetainArgumentTypes = true }) })
            };

        // Create a thread and register context based function selection provider that will do RAG on
        // provided functions to advertise only those that are relevant to the current context.
        ChatHistoryAgentThread agentThread = new();

        var allAvailableFunctions = GetAvailableFunctions();

        agentThread.AIContextProviders.Add(
            new ContextualFunctionProvider(
                vectorStore: new InMemoryVectorStore(new InMemoryVectorStoreOptions() { EmbeddingGenerator = embeddingGenerator }),
                vectorDimensions: 1536,
                functions: allAvailableFunctions,
                maxNumberOfFunctions: 3, // Instruct the provider to return a maximum of 3 relevant functions
                contextSize: 2 // Use the last 2 messages as context for function selection
            )
        );

        // Invoke and display assistant response
        ChatMessageContent message = await agent.InvokeAsync("Get and summarize customer review.", agentThread).FirstAsync();
        Console.WriteLine(message.Content);

        //Expected output:
        /*  
            Retrieves and summarizes customer reviews.  
  
            ### Customer Reviews:  
            1. **John D.** - ★★★★★  
                *Comment:* Great product and fast shipping!  
                *Date:* 2023-10-01  
            2. **Jane S.** - ★★★★  
                *Comment:* Good quality, but delivery was a bit slow.  
                *Date:* 2023-09-28  
            3. **Mike J.** - ★★★  
                *Comment:* Average. Works as expected.  
                *Date:* 2023-09-25  
  
            ### Summary:  
            The reviews indicate overall customer satisfaction, with highlights on product quality and shipping efficiency.  
            While some customers experienced excellent service, others mentioned areas for improvement, particularly regarding delivery times.  
  
            If you need further analysis or insights, feel free to ask!  
  
            Available functions:  
            - Tools-GetCustomerReviews  
            - Tools-Summarize  
            - Tools-CollectSentiments  
         */
    }

    /// <summary>
    /// Returns a list of functions that belong to different categories.
    /// Some categories/functions are related to the prompt, while others
    /// are not. This is intentionally done to demonstrate the contextual
    /// function selection capabilities of the provider.
    /// </summary>
    private IReadOnlyList<AIFunction> GetAvailableFunctions()
    {
        List<AIFunction> reviewFunctions = [
            AIFunctionFactory.Create(() => """
            [  
                {  
                    "reviewer": "John D.",  
                    "date": "2023-10-01",  
                    "rating": 5,  
                    "comment": "Great product and fast shipping!"  
                },  
                {  
                    "reviewer": "Jane S.",  
                    "date": "2023-09-28",  
                    "rating": 4,  
                    "comment": "Good quality, but delivery was a bit slow."  
                },  
                {  
                    "reviewer": "Mike J.",  
                    "date": "2023-09-25",  
                    "rating": 3,  
                    "comment": "Average. Works as expected."  
                }  
            ]
            """
            , "GetCustomerReviews"),
        ];

        List<AIFunction> sentimentFunctions = [
            AIFunctionFactory.Create((string text) => "The collected sentiment is mostly positive with a few neutral and negative opinions.", "CollectSentiments"),
            AIFunctionFactory.Create((string text) => "Sentiment trend identified: predominantly positive with increasing positive feedback.", "IdentifySentimentTrend"),
        ];

        List<AIFunction> summaryFunctions = [
            AIFunctionFactory.Create((string text) => "Summary generated based on input data: key points include market growth and customer satisfaction.", "Summarize"),
            AIFunctionFactory.Create((string text) => "Extracted themes: innovation, efficiency, customer satisfaction.", "ExtractThemes"),
        ];

        List<AIFunction> communicationFunctions = [
            AIFunctionFactory.Create((string address, string content) => "Email sent.", "SendEmail"),
            AIFunctionFactory.Create((string number, string text) => "Message sent.", "SendSms"),
            AIFunctionFactory.Create(() => "user@domain.com", "MyEmail"),
        ];

        List<AIFunction> dateTimeFunctions = [
            AIFunctionFactory.Create(() => DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"), "GetCurrentDateTime"),
            AIFunctionFactory.Create(() => DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm:ss"), "GetCurrentUtcDateTime"),
        ];

        return [.. reviewFunctions, .. sentimentFunctions, .. summaryFunctions, .. communicationFunctions, .. dateTimeFunctions];
    }
}
