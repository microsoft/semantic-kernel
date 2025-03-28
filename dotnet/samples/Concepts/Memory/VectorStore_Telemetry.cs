// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Embeddings;

namespace Memory;

/// <summary>
/// A simple example showing how to ingest data into a vector store and then use vector search to find related records to a given string
/// with enabled telemetry.
/// </summary>
public class VectorStore_Telemetry(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task LoggingManualRegistrationAsync()
    {
        // Create an embedding generation service.
        var textEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                new AzureCliCredential());

        // Manually construct an InMemory vector store with enabled logging.
        var vectorStore = new InMemoryVectorStore()
            .AsBuilder()
            .UseLogging(this.LoggerFactory)
            .Build();

        await RunExampleAsync(textEmbeddingGenerationService, vectorStore);

        // Output:
        // CreateCollectionIfNotExistsAsync invoked.
        // CreateCollectionIfNotExistsAsync completed.
        // UpsertAsync invoked.
        // UpsertAsync completed.
        // UpsertAsync invoked.
        // UpsertAsync completed.
        // UpsertAsync invoked.
        // UpsertAsync completed.
        // VectorizedSearchAsync invoked.
        // VectorizedSearchAsync completed.

        // Search string: What is an Application Programming Interface
        // Result: Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data.
    }

    [Fact]
    public async Task LoggingDependencyInjectionAsync()
    {
        var serviceCollection = new ServiceCollection();

        // Add an embedding generation service.
        serviceCollection.AddAzureOpenAITextEmbeddingGeneration(
            TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
            TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
            new AzureCliCredential());

        // Add InMemory vector store
        serviceCollection.AddInMemoryVectorStore();

        // Register InMemoryVectorStore with enabled logging.
        serviceCollection
            .AddVectorStore(s => s.GetRequiredService<InMemoryVectorStore>())
            .UseLogging(this.LoggerFactory);

        var services = serviceCollection.BuildServiceProvider();

        var vectorStore = services.GetRequiredService<IVectorStore>();
        var textEmbeddingGenerationService = services.GetRequiredService<ITextEmbeddingGenerationService>();

        await RunExampleAsync(textEmbeddingGenerationService, vectorStore);

        // Output:
        // CreateCollectionIfNotExistsAsync invoked.
        // CreateCollectionIfNotExistsAsync completed.
        // UpsertAsync invoked.
        // UpsertAsync completed.
        // UpsertAsync invoked.
        // UpsertAsync completed.
        // UpsertAsync invoked.
        // UpsertAsync completed.
        // VectorizedSearchAsync invoked.
        // VectorizedSearchAsync completed.

        // Search string: What is an Application Programming Interface
        // Result: Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data.
    }

    private async Task RunExampleAsync(
        ITextEmbeddingGenerationService textEmbeddingGenerationService,
        IVectorStore vectorStore)
    {
        // Get and create collection if it doesn't exist.
        var collection = vectorStore.GetCollection<ulong, Glossary>("skglossary");
        await collection.CreateCollectionIfNotExistsAsync();

        // Create glossary entries and generate embeddings for them.
        var glossaryEntries = CreateGlossaryEntries().ToList();
        var tasks = glossaryEntries.Select(entry => Task.Run(async () =>
        {
            entry.DefinitionEmbedding = await textEmbeddingGenerationService.GenerateEmbeddingAsync(entry.Definition);
        }));
        await Task.WhenAll(tasks);

        // Upsert the glossary entries into the collection and return their keys.
        var upsertedKeysTasks = glossaryEntries.Select(x => collection.UpsertAsync(x));
        var upsertedKeys = await Task.WhenAll(upsertedKeysTasks);

        // Search the collection using a vector search.
        var searchString = "What is an Application Programming Interface";
        var searchVector = await textEmbeddingGenerationService.GenerateEmbeddingAsync(searchString);
        var searchResult = await collection.VectorizedSearchAsync(searchVector, new() { Top = 1 });
        var resultRecords = await searchResult.Results.ToListAsync();

        Console.WriteLine("Search string: " + searchString);
        Console.WriteLine("Result: " + resultRecords.First().Record.Definition);
        Console.WriteLine();
    }

    /// <summary>
    /// Sample model class that represents a glossary entry.
    /// </summary>
    /// <remarks>
    /// Note that each property is decorated with an attribute that specifies how the property should be treated by the vector store.
    /// This allows us to create a collection in the vector store and upsert and retrieve instances of this class without any further configuration.
    /// </remarks>
    private sealed class Glossary
    {
        [VectorStoreRecordKey]
        public ulong Key { get; set; }

        [VectorStoreRecordData(IsFilterable = true)]
        public string Category { get; set; }

        [VectorStoreRecordData]
        public string Term { get; set; }

        [VectorStoreRecordData]
        public string Definition { get; set; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> DefinitionEmbedding { get; set; }
    }

    /// <summary>
    /// Create some sample glossary entries.
    /// </summary>
    /// <returns>A list of sample glossary entries.</returns>
    private static IEnumerable<Glossary> CreateGlossaryEntries()
    {
        yield return new Glossary
        {
            Key = 1,
            Category = "External Definitions",
            Term = "API",
            Definition = "Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data."
        };

        yield return new Glossary
        {
            Key = 2,
            Category = "Core Definitions",
            Term = "Connectors",
            Definition = "Connectors allow you to integrate with various services provide AI capabilities, including LLM, AudioToText, TextToAudio, Embedding generation, etc."
        };

        yield return new Glossary
        {
            Key = 3,
            Category = "External Definitions",
            Term = "RAG",
            Definition = "Retrieval Augmented Generation - a term that refers to the process of retrieving additional data to provide as context to an LLM to use when generating a response (completion) to a user’s question (prompt)."
        };
    }
}
