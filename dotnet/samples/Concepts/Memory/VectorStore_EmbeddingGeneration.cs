// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using Memory.VectorStoreEmbeddingGeneration;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.InMemory;

namespace Memory;

/// <summary>
/// This sample shows how to abstract embedding generation away from usage by
/// using the decorator pattern.
///
/// In the sample we create an <see cref="InMemoryVectorStore"/> and then using
/// an extension method <see cref="TextEmbeddingVectorStoreExtensions.UseTextEmbeddingGeneration(IVectorStore, Microsoft.SemanticKernel.Embeddings.ITextEmbeddingGenerationService)"/>
/// we wrap the <see cref="InMemoryVectorStore"/> with a <see cref="TextEmbeddingVectorStore"/> that will automatically generate embeddings for properties
/// that have the <see cref="GenerateTextEmbeddingAttribute"/> attribute.
///
/// The decorated vector store also adds the additional <see cref="IVectorizableTextSearch{TRecord}"/> interface to the collection
/// which allows us to search the collection using a text string without having to manually generate the embeddings.
///
/// Note that the <see cref="TextEmbeddingVectorStore"/> demonstrated here are part of this sample and not part of the Semantic Kernel libraries.
/// To use it, you will need to copy it to your own project.
/// </summary>
public class VectorStore_EmbeddingGeneration(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task UseEmbeddingGenerationViaDecoratorAsync()
    {
        // Create an embedding generation service.
        var textEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                new AzureCliCredential());

        // Construct an InMemory vector store with embedding generation.
        // The UseTextEmbeddingGeneration method adds an embedding generation
        // decorator class to the vector store that will automatically generate
        // embeddings for properties that are decorated with the GenerateTextEmbeddingAttribute.
        var vectorStore = new InMemoryVectorStore().UseTextEmbeddingGeneration(textEmbeddingGenerationService);

        // Get and create collection if it doesn't exist.
        var collection = vectorStore.GetCollection<ulong, Glossary>("skglossary");
        await collection.CreateCollectionIfNotExistsAsync();

        // Create and upsert glossary entries into the collection.
        await collection.UpsertBatchAsync(CreateGlossaryEntries()).ToListAsync();

        // Search the collection using a vectorizable text search.
        var search = collection as IVectorizableTextSearch<Glossary>;
        var searchString = "What is an Application Programming Interface";
        var searchResult = await search!.VectorizableTextSearchAsync(searchString, new() { Top = 1 });
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
    ///
    /// The <see cref="Glossary.DefinitionEmbedding"/> property is also decorated with the <see cref="GenerateTextEmbeddingAttribute"/> attribute which
    /// allows the vector store to automatically generate an embedding for the property when the record is upserted.
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

        [GenerateTextEmbedding(nameof(Definition))]
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
