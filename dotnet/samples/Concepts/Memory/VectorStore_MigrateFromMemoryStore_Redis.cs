// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Azure.Identity;
using Memory.VectorStoreFixtures;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Memory;
using StackExchange.Redis;

namespace Memory;

/// <summary>
/// Example showing how to migrate from the memory store abstractions to the vector store abstractions when using Redis.
/// </summary>
/// <remarks>
/// The IMemoryStore abstraction has limitations that constrain its use in many scenarios
/// e.g. it only supports a single fixed schema and does not allow search filtering.
/// To provide more flexibility, the Vector Store abstraction has been introduced.
///
/// For most databases, it is possible to use the vector store abstractions to directly consume data that was uploaded
/// using the memory store abstractions, as long as the appropriate data model is provided.
/// See <see cref="VectorStore_ConsumeFromMemoryStore_Redis"/> for an example of this using Redis.
/// In some cases, it may be desirable to migrate data to a different schema than what was created by the memory store.
/// Redis is such an example, where metadata is stored as a json string, making it impossible to filter on metadata fields.
/// Separating the metadata into separate fields on the data model could allow for filtering on these fields.
///
/// To run this sample, you need a local instance of Docker running, since the associated fixture will try and start a Redis container in the local docker instance to run against.
/// </remarks>
[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public class VectorStore_MigrateFromMemoryStore_Redis(ITestOutputHelper output, VectorStoreRedisContainerFixture redisFixture) : BaseTest(output), IClassFixture<VectorStoreRedisContainerFixture>
{
    private const int VectorSize = 1536;
    private const string MemoryStoreCollectionName = "memorystorecollection";
    private const string VectorStoreCollectionName = "vectorstorecollection";
    private readonly static JsonSerializerOptions s_consoleFormatting = new() { WriteIndented = true };

    [Fact]
    public async Task MigrateExampleAsync()
    {
        // Setup the supporting infra and embedding generation.
        await redisFixture.ManualInitializeAsync();
        var textEmbeddingService = new AzureOpenAITextEmbeddingGenerationService(
            TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
            TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
            new AzureCliCredential());

        // Construct a legacy MemoryStore.
        var memoryStore = new RedisMemoryStore("localhost:6379", VectorSize);

        // Construct a VectorStore.
        var vectorStore = new RedisVectorStore(
            ConnectionMultiplexer.Connect("localhost:6379").GetDatabase(),
            new() { StorageType = RedisStorageType.HashSet });

        // Build a collection with sample data using the MemoryStore abstraction.
        await memoryStore.CreateCollectionAsync(MemoryStoreCollectionName);
        await foreach (var memoryRecord in CreateSampleDataAsync(textEmbeddingService))
        {
            await memoryStore.UpsertAsync(MemoryStoreCollectionName, memoryRecord);
        }

        // Create a replacement collection using the VectorStore abstraction and the new data model.
        var collection = vectorStore.GetCollection<string, VectorStoreRecord>(VectorStoreCollectionName);
        await collection.CreateCollectionIfNotExistsAsync();

        // Migrate data from the old collection to the new collection by querying the old collection for all records,
        // mapping them to the new data model, and upserting them into the new collection.
        var memoryStoreResults = memoryStore.GetNearestMatchesAsync(
            MemoryStoreCollectionName,
            new float[VectorSize],  // Since we want to get all records, and we don't care about similarity here, we can just pass in any vector.
            limit: 10000,           // Since we want to get all records, pass in the largest possible limit.
            minRelevanceScore: -1,  // Since we want to get all records, and Qdrant is using cosine similarity, pass in -1 to avoid filtering out anything.
            withEmbeddings: true);

        await foreach (var memoryStoreResult in memoryStoreResults)
        {
            var memoryStoreRecord = memoryStoreResult.Item1;

            // Map from MemoryRecord to VectorStoreRecord.
            var vectorStoreRecord = new VectorStoreRecord
            {
                Key = memoryStoreRecord.Key,
                Description = memoryStoreRecord.Metadata.Description,
                Text = memoryStoreRecord.Metadata.Text,
                IsReference = memoryStoreRecord.Metadata.IsReference,
                ExternalSourceName = memoryStoreRecord.Metadata.ExternalSourceName,
                AdditionalMetadata = memoryStoreRecord.Metadata.AdditionalMetadata,
                Embedding = memoryStoreRecord.Embedding
            };

            await collection.UpsertAsync(vectorStoreRecord);
        }

        // Show that the data has been migrated successfully.
        var record1 = await collection.GetAsync("11111111-1111-1111-1111-111111111111");
        var record2 = await collection.GetAsync("22222222-2222-2222-2222-222222222222");
        var record3 = await collection.GetAsync("33333333-3333-3333-3333-333333333333", new() { IncludeVectors = true });

        Console.WriteLine($"Record 1: {JsonSerializer.Serialize(record1, s_consoleFormatting)}");
        Console.WriteLine($"Record 2: {JsonSerializer.Serialize(record2, s_consoleFormatting)}");
        Console.WriteLine($"Record 3: {JsonSerializer.Serialize(record3, s_consoleFormatting)}");
    }

    /// <summary>
    /// Data model with Vector Store attributes that contains all properties from the <see cref="MemoryRecord"/> class.
    /// </summary>
    private sealed class VectorStoreRecord
    {
        [VectorStoreRecordKey]
        public string Key { get; set; }

        [VectorStoreRecordData]
        public string Description { get; set; }

        [VectorStoreRecordData]
        public string Text { get; set; }

        [VectorStoreRecordData]
        public bool IsReference { get; set; }

        [VectorStoreRecordData]
        public string ExternalSourceName { get; set; }

        [VectorStoreRecordData]
        public string AdditionalMetadata { get; set; }

        [VectorStoreRecordVector(VectorSize)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }

    private static async IAsyncEnumerable<MemoryRecord> CreateSampleDataAsync(ITextEmbeddingGenerationService textEmbeddingService)
    {
        var dateTimeOffset = new DateTimeOffset(2023, 10, 10, 0, 0, 0, TimeSpan.Zero);

        // Record 1.
        var text1 = """
            The Semantic Kernel Vector Store connectors use a model first approach to interacting with databases.
            This means that the first step is to define a data model that maps to the storage schema.
            To help the connectors create collections of records and map to the storage schema, the model can
            be annotated to indicate the function of each property.
            """;
        var embedding1 = await textEmbeddingService.GenerateEmbeddingAsync(text1);

        yield return new MemoryRecord(
            new MemoryRecordMetadata(
                isReference: false,
                id: "11111111-1111-1111-1111-111111111111",
                text: text1,
                description: "Describes the model first approach of Vector Store abstractions in SK.",
                externalSourceName: string.Empty,
                additionalMetadata: "sample: 1"),
            embedding1,
            key: "11111111-1111-1111-1111-111111111111");

        // Record 2.
        var text2 = """The underlying implementation of what a collection is, will vary by connector and is influenced by how each database groups and indexes records.""";
        var embedding2 = await textEmbeddingService.GenerateEmbeddingAsync(text2);

        yield return new MemoryRecord(
            new MemoryRecordMetadata(
                isReference: true,
                id: "22222222-2222-2222-2222-222222222222",
                text: string.Empty,
                description: "Describes how collections are mapped in different stores.",
                externalSourceName: "https://learn.microsoft.com/en-us/semantic-kernel/concepts/vector-store-connectors/data-architecture#collections-in-different-databases",
                additionalMetadata: "sample: 2"),
            embedding2,
            key: "22222222-2222-2222-2222-222222222222");

        // Record 3.
        var text3 = """
            The Semantic Kernel Vector Store connectors use a model first approach to interacting with databases.
            All methods to upsert or get records use strongly typed model classes. The properties on these classes are decorated with attributes that indicate the purpose of each property.
            """;
        var embedding3 = await textEmbeddingService.GenerateEmbeddingAsync(text3);

        yield return new MemoryRecord(
            new MemoryRecordMetadata(
                isReference: true,
                id: "33333333-3333-3333-3333-333333333333",
                text: string.Empty,
                description: "Describes the strong typing of Vector Store connectors.",
                externalSourceName: "https://learn.microsoft.com/en-us/semantic-kernel/concepts/vector-store-connectors/defining-your-data-model#overview",
                additionalMetadata: "sample: 3"),
            embedding3,
            key: "33333333-3333-3333-3333-333333333333");
    }
}
