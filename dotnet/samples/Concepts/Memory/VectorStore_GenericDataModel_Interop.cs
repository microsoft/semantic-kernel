﻿// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Azure.Identity;
using Memory.VectorStoreFixtures;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Embeddings;
using Qdrant.Client;

namespace Memory;

/// <summary>
/// Semantic Kernel provides a generic data model for vector stores that can be used with any
/// schema. The schema still has to be provided in the form of a record definition, but no
/// custom data model is required.
///
/// The sample shows how to
/// 1. Upsert data using the generic data model and retrieve it from the vector store using a custom data model.
/// 2. Upsert data using a custom data model and retrieve it from the vector store using the generic data model.
/// </summary>
public class VectorStore_GenericDataModel_Interop(ITestOutputHelper output, VectorStoreQdrantContainerFixture qdrantFixture) : BaseTest(output), IClassFixture<VectorStoreQdrantContainerFixture>
{
    private static readonly JsonSerializerOptions s_indentedSerializerOptions = new() { WriteIndented = true };

    private static readonly VectorStoreRecordDefinition s_vectorStoreRecordDefinition = new()
    {
        Properties = new List<VectorStoreRecordProperty>
        {
            new VectorStoreRecordKeyProperty("Key", typeof(ulong)),
            new VectorStoreRecordDataProperty("Term", typeof(string)),
            new VectorStoreRecordDataProperty("Definition", typeof(string)),
            new VectorStoreRecordVectorProperty("DefinitionEmbedding", typeof(ReadOnlyMemory<float>)) { Dimensions = 1536 }
        }
    };

    [Fact]
    public async Task UpsertWithGenericRetrieveWithCustomAsync()
    {
        // Create an embedding generation service.
        var textEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                new AzureCliCredential());

        // Initiate the docker container and construct the vector store.
        await qdrantFixture.ManualInitializeAsync();
        var vectorStore = new QdrantVectorStore(new QdrantClient("localhost"));

        // Get and create collection if it doesn't exist using the generic data model and record definition that defines the schema.
        var genericDataModelCollection = vectorStore.GetCollection<ulong, VectorStoreGenericDataModel<ulong>>("skglossary", s_vectorStoreRecordDefinition);
        await genericDataModelCollection.CreateCollectionIfNotExistsAsync();

        // Create glossary entries and generate embeddings for them.
        var glossaryEntries = CreateGenericGlossaryEntries().ToList();
        var tasks = glossaryEntries.Select(entry => Task.Run(async () =>
        {
            entry.Vectors["DefinitionEmbedding"] = await textEmbeddingGenerationService.GenerateEmbeddingAsync((string)entry.Data["Definition"]!);
        }));
        await Task.WhenAll(tasks);

        // Upsert the glossary entries into the collection and return their keys.
        var upsertedKeysTasks = glossaryEntries.Select(x => genericDataModelCollection.UpsertAsync(x));
        var upsertedKeys = await Task.WhenAll(upsertedKeysTasks);

        // Get the collection using the custom data model.
        var customDataModelCollection = vectorStore.GetCollection<ulong, Glossary>("skglossary");

        // Retrieve one of the upserted records from the collection.
        var upsertedRecord = await customDataModelCollection.GetAsync(upsertedKeys.First(), new() { IncludeVectors = true });

        // Write upserted keys and one of the upserted records to the console.
        Console.WriteLine($"Upserted keys: {string.Join(", ", upsertedKeys)}");
        Console.WriteLine($"Upserted record: {JsonSerializer.Serialize(upsertedRecord, s_indentedSerializerOptions)}");
    }

    [Fact]
    public async Task UpsertWithCustomRetrieveWithGenericAsync()
    {
        // Create an embedding generation service.
        var textEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                new AzureCliCredential());

        // Initiate the docker container and construct the vector store.
        await qdrantFixture.ManualInitializeAsync();
        var vectorStore = new QdrantVectorStore(new QdrantClient("localhost"));

        // Get and create collection if it doesn't exist using the custom data model.
        var customDataModelCollection = vectorStore.GetCollection<ulong, Glossary>("skglossary");
        await customDataModelCollection.CreateCollectionIfNotExistsAsync();

        // Create glossary entries and generate embeddings for them.
        var glossaryEntries = CreateCustomGlossaryEntries().ToList();
        var tasks = glossaryEntries.Select(entry => Task.Run(async () =>
        {
            entry.DefinitionEmbedding = await textEmbeddingGenerationService.GenerateEmbeddingAsync(entry.Definition);
        }));
        await Task.WhenAll(tasks);

        // Upsert the glossary entries into the collection and return their keys.
        var upsertedKeysTasks = glossaryEntries.Select(x => customDataModelCollection.UpsertAsync(x));
        var upsertedKeys = await Task.WhenAll(upsertedKeysTasks);

        // Get the collection using the generic data model.
        var genericDataModelCollection = vectorStore.GetCollection<ulong, VectorStoreGenericDataModel<ulong>>("skglossary", s_vectorStoreRecordDefinition);

        // Retrieve one of the upserted records from the collection.
        var upsertedRecord = await genericDataModelCollection.GetAsync(upsertedKeys.First(), new() { IncludeVectors = true });

        // Write upserted keys and one of the upserted records to the console.
        Console.WriteLine($"Upserted keys: {string.Join(", ", upsertedKeys)}");
        Console.WriteLine($"Upserted record: {JsonSerializer.Serialize(upsertedRecord, s_indentedSerializerOptions)}");
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

        [VectorStoreRecordData]
        public string Term { get; set; }

        [VectorStoreRecordData]
        public string Definition { get; set; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> DefinitionEmbedding { get; set; }
    }

    /// <summary>
    /// Create some sample glossary entries using the custom data model.
    /// </summary>
    /// <returns>A list of sample glossary entries.</returns>
    private static IEnumerable<Glossary> CreateCustomGlossaryEntries()
    {
        yield return new Glossary
        {
            Key = 1,
            Term = "API",
            Definition = "Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data.",
        };

        yield return new Glossary
        {
            Key = 2,
            Term = "Connectors",
            Definition = "Connectors allow you to integrate with various services provide AI capabilities, including LLM, AudioToText, TextToAudio, Embedding generation, etc.",
        };

        yield return new Glossary
        {
            Key = 3,
            Term = "RAG",
            Definition = "Retrieval Augmented Generation - a term that refers to the process of retrieving additional data to provide as context to an LLM to use when generating a response (completion) to a user’s question (prompt).",
        };
    }

    /// <summary>
    /// Create some sample glossary entries using the generic data model.
    /// </summary>
    /// <returns>A list of sample glossary entries.</returns>
    private static IEnumerable<VectorStoreGenericDataModel<ulong>> CreateGenericGlossaryEntries()
    {
        yield return new VectorStoreGenericDataModel<ulong>(1)
        {
            Data = new Dictionary<string, object?>
            {
                ["Term"] = "API",
                ["Definition"] = "Application Programming Interface. A set of rules and specifications that allow software components to communicate and exchange data.",
            }
        };

        yield return new VectorStoreGenericDataModel<ulong>(2)
        {
            Data = new Dictionary<string, object?>
            {
                ["Term"] = "Connectors",
                ["Definition"] = "Connectors allow you to integrate with various services provide AI capabilities, including LLM, AudioToText, TextToAudio, Embedding generation, etc.",
            }
        };

        yield return new VectorStoreGenericDataModel<ulong>(3)
        {
            Data = new Dictionary<string, object?>
            {
                ["Term"] = "RAG",
                ["Definition"] = "Retrieval Augmented Generation - a term that refers to the process of retrieving additional data to provide as context to an LLM to use when generating a response (completion) to a user’s question (prompt).",
            }
        };
    }
}
