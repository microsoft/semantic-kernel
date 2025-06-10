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
    /// to enable contextual function selection based on the current invocation context.
    /// </summary>
    [Fact]
    private async Task SelectFunctionsRelevantToCurrentInvocationContext()
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
                loggerFactory: this.LoggerFactory
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
    /// Shows how to configure agent to use <see cref="ContextualFunctionProvider"/>
    /// to enable contextual function selection based on the previous and current invocation context.
    /// </summary>
    [Fact]
    private async Task SelectFunctionsBasedOnPreviousAndCurrentInvocationContext()
    {
        var embeddingGenerator = new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAIEmbeddings.Endpoint), new AzureCliCredential())
            .GetEmbeddingClient(TestConfiguration.AzureOpenAIEmbeddings.DeploymentName)
            .AsIEmbeddingGenerator(1536);

        // Create our agent.
        Kernel kernel = this.CreateKernelWithChatCompletion();
        ChatCompletionAgent agent =
            new()
            {
                Name = "AzureAssistant",
                Instructions = "You are a helpful assistant that helps with Azure resource management. " +
                               "Avoid including the phrase like 'If you need further assistance or have any additional tasks, feel free to let me know!' in any responses.",
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
                maxNumberOfFunctions: 1, // Instruct the provider to return only one relevant function
                loggerFactory: this.LoggerFactory,
                options: new ContextualFunctionProviderOptions
                {
                    NumberOfRecentMessagesInContext = 1 // Use only the last message from the previous agent invocation  
                }
            )
        );

        // Ask agent to provision a VM on Azure. The contextual function selection provider will return only one relevant function: `ProvisionVM`
        ChatMessageContent message = await agent.InvokeAsync("Please provision a VM on Azure", agentThread).FirstAsync();
        Console.WriteLine(message.Content);

        //Expected output: "A virtual machine has been successfully provisioned on Azure with the ID: 7f2aa1e4-13ac-4875-9e63-278ee82f3729."

        // Ask the agent to deploy the VM, intentionally referring to the VM as "it".  
        // This demonstrates that the contextual function selection provider uses the last message from the previous invocation
        // to infer that the user is referring to the VM provisioned in the invocation and not any other Azure resource.
        // The provider will return only one relevant function to deploy the VM: `DeployVM`
        message = await agent.InvokeAsync("Deploy it", agentThread).FirstAsync();
        Console.WriteLine(message.Content);

        //Expected output: "The virtual machine with ID: 7f2aa1e4-13ac-4875-9e63-278ee82f3729 has been successfully deployed."
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

        List<AIFunction> azureFunctions = [
            AIFunctionFactory.Create(() => $"Resource group provisioned: Id:{Guid.NewGuid()}", "ProvisionResourceGroup"),
            AIFunctionFactory.Create((Guid id) => $"Resource group deployed: Id:{id}", "DeployResourceGroup"),

            AIFunctionFactory.Create(() => $"Storage account provisioned: Id:{Guid.NewGuid()}", "ProvisionStorageAccount"),
            AIFunctionFactory.Create((Guid id) => $"Storage account deployed: Id:{id}", "DeployStorageAccount"),

            AIFunctionFactory.Create(() => $"VM provisioned: Id:{Guid.NewGuid()}", "ProvisionVM"),
            AIFunctionFactory.Create((Guid id) => $"VM deployed: Id:{id}", "DeployVM"),
        ];

        return [.. reviewFunctions, .. sentimentFunctions, .. summaryFunctions, .. communicationFunctions, .. dateTimeFunctions, .. azureFunctions];
    }
}
