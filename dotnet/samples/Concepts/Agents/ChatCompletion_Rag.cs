// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Data;

namespace Agents;

#pragma warning disable SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> and
/// adding simple retrieval augmented generation (RAG) capabilities to it.
/// </summary>
/// <remarks>
/// This example shows how to use the <see cref="TextSearchStore{TKey}"/> class which is designed
/// to simplify the process of storing and searching text documents by having a built in schema.
/// If you want to control the schema yourself, you can use an implementation of <see cref="VectorStoreCollection{TKey, TRecord}"/>
/// with the <see cref="VectorStoreTextSearch{TRecord}"/> class instead.
/// </remarks>
public class ChatCompletion_Rag(ITestOutputHelper output) : BaseTest(output)
{
    private const string AgentName = "FriendlyAssistant";
    private const string AgentInstructions = "You are a friendly assistant";

    /// <summary>
    /// Shows how to do Retrieval Augmented Generation (RAG) with some basic text strings.
    /// </summary>
    [Fact]
    private async Task UseChatCompletionAgentWithBasicRag()
    {
        var embeddingGenerator = new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAIEmbeddings.Endpoint), new AzureCliCredential())
            .GetEmbeddingClient(TestConfiguration.AzureOpenAIEmbeddings.DeploymentName)
            .AsIEmbeddingGenerator(1536);

        // Create a vector store to store our documents.
        // Note that the embedding generator provided here must be able to generate embeddings matching the
        // number of dimensions configured for the TextSearchStore below.
        var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        // Create a store that uses a built in schema for storing text documents
        // and provides easy upload and search capabilities.
        // The data is stored in the `FinancialData` collection and embeddings have 1536 dimensions.
        // When searching results will be limited to those with the `group/g2` namespace.
        using var textSearchStore = new TextSearchStore<string>(vectorStore, collectionName: "FinancialData", vectorDimensions: 1536);

        // Upsert documents into the store.
        await textSearchStore.UpsertTextAsync(
            [
                "The financial results of Contoso Corp for 2024 is as follows:\nIncome EUR 154 000 000\nExpenses EUR 142 000 000",
                "The financial results of Contoso Corp for 2023 is as follows:\nIncome EUR 174 000 000\nExpenses EUR 152 000 000",
                "The financial results of Contoso Corp for 2022 is as follows:\nIncome EUR 184 000 000\nExpenses EUR 162 000 000",
                "The Contoso Corporation is a multinational business with its headquarters in Paris. The company is a manufacturing, sales, and support organization with more than 100,000 products.",
                "The financial results of AdventureWorks for 2021 is as follows:\nIncome USD 223 000 000\nExpenses USD 210 000 000",
                "AdventureWorks is a large American business that specializes in adventure parks and family entertainment.",
            ]);

        // Create our agent.
        Kernel kernel = this.CreateKernelWithChatCompletion();
        ChatCompletionAgent agent =
            new()
            {
                Name = AgentName,
                Instructions = AgentInstructions,
                Kernel = kernel,
            };

        // Create a thread for the agent.
        ChatHistoryAgentThread agentThread = new();

        // Create a text search provider that can automatically search the vector store
        // for documents that match the user's query and inject them into the agent's prompt.
        var textSearchProvider = new TextSearchProvider(textSearchStore);
        agentThread.AIContextProviders.Add(textSearchProvider);

        // Invoke and display assistant response
        ChatMessageContent message = await agent.InvokeAsync("Where is Contoso based?", agentThread).FirstAsync();
        Console.WriteLine(message.Content);

        message = await agent.InvokeAsync("What was its expenses for 2022?", agentThread).FirstAsync();
        Console.WriteLine(message.Content);
    }

    /// <summary>
    /// Shows how to do Retrieval Augmented Generation (RAG) with citations and filtering.
    /// </summary>
    [Fact]
    private async Task RagWithCitationsAndFiltering()
    {
        var embeddingGenerator = new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAIEmbeddings.Endpoint), new AzureCliCredential())
            .GetEmbeddingClient(TestConfiguration.AzureOpenAIEmbeddings.DeploymentName)
            .AsIEmbeddingGenerator(1536);

        // Create a vector store to store our documents.
        // Note that the embedding generator provided here must be able to generate embeddings matching the
        // number of dimensions configured for the TextSearchStore below.
        var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        // Create a store that uses a built in schema for storing text documents
        // and provides easy upload and search capabilities.
        // The data is stored in the `FinancialData` collection and embeddings have 1536 dimensions.
        // When searching results will be limited to those with the `group/g2` namespace.
        using var textSearchStore = new TextSearchStore<string>(vectorStore, collectionName: "FinancialData", vectorDimensions: 1536, new() { SearchNamespace = "group/g2" });

        // Upsert documents into the store.
        // Not that documents have different namespaces, and only the ones
        // with the `group/g2` namespace will be matched.
        await textSearchStore.UpsertDocumentsAsync(GetSampleDocuments());

        // Create our agent.
        Kernel kernel = this.CreateKernelWithChatCompletion();
        ChatCompletionAgent agent =
            new()
            {
                Name = AgentName,
                Instructions = AgentInstructions,
                Kernel = kernel,
            };

        // Create a thread for the agent.
        ChatHistoryAgentThread agentThread = new();

        // Create a text search provider that can automatically search the vector store
        // for documents that match the user's query and inject them into the agent's prompt.
        var textSearchProvider = new TextSearchProvider(textSearchStore);
        agentThread.AIContextProviders.Add(textSearchProvider);

        // Invoke and display assistant response
        ChatMessageContent message = await agent.InvokeAsync("What was the income of Contoso for 2023", agentThread).FirstAsync();
        Console.WriteLine(message.Content);
    }

    private static IEnumerable<TextSearchDocument> GetSampleDocuments()
    {
        yield return new TextSearchDocument
        {
            Text = "The financial results of Contoso Corp for 2024 is as follows:\nIncome EUR 154 000 000\nExpenses EUR 142 000 000",
            SourceName = "Contoso 2024 Financial Report",
            SourceLink = "https://www.consoso.com/reports/2024.pdf",
            Namespaces = ["group/g1"]
        };
        yield return new TextSearchDocument
        {
            Text = "The financial results of Contoso Corp for 2023 is as follows:\nIncome EUR 174 000 000\nExpenses EUR 152 000 000",
            SourceName = "Contoso 2023 Financial Report",
            SourceLink = "https://www.consoso.com/reports/2023.pdf",
            Namespaces = ["group/g2"]
        };
        yield return new TextSearchDocument
        {
            Text = "The financial results of Contoso Corp for 2022 is as follows:\nIncome EUR 184 000 000\nExpenses EUR 162 000 000",
            SourceName = "Contoso 2022 Financial Report",
            SourceLink = "https://www.consoso.com/reports/2022.pdf",
            Namespaces = ["group/g2"]
        };
        yield return new TextSearchDocument
        {
            Text = "The Contoso Corporation is a multinational business with its headquarters in Paris. The company is a manufacturing, sales, and support organization with more than 100,000 products.",
            SourceName = "About Contoso",
            SourceLink = "https://www.consoso.com/about-us",
            Namespaces = ["group/g2"]
        };
        yield return new TextSearchDocument
        {
            Text = "The financial results of AdventureWorks for 2021 is as follows:\nIncome USD 223 000 000\nExpenses USD 210 000 000",
            SourceName = "AdventureWorks 2021 Financial Report",
            SourceLink = "https://www.adventure-works.com/reports/2021.pdf",
            Namespaces = ["group/g1", "group/g2"]
        };
        yield return new TextSearchDocument
        {
            Text = "AdventureWorks is a large American business that specializes in adventure parks and family entertainment.",
            SourceName = "About AdventureWorks",
            SourceLink = "https://www.adventure-works.com/about-us",
            Namespaces = ["group/g1", "group/g2"]
        };
    }
}
