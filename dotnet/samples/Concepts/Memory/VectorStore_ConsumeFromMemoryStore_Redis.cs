// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using Memory.VectorStoreFixtures;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Memory;
using StackExchange.Redis;

namespace Memory;

/// <summary>
/// An example showing how use the VectorStore abstractions to consume data from a Redis data store,
/// that was created using the MemoryStore abstractions.
/// </summary>
/// <remarks>
/// The IMemoryStore abstraction has limitations that constrain its use in many scenarios
/// e.g. it only supports a single fixed schema and does not allow search filtering.
/// To provide more flexibility, the Vector Store abstraction has been introduced.
///
/// To run this sample, you need a local instance of Docker running, since the associated fixture
/// will try and start a Redis container in the local docker instance to run against.
/// </remarks>
[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public class VectorStore_ConsumeFromMemoryStore_Redis(ITestOutputHelper output, VectorStoreRedisContainerFixture redisFixture) : BaseTest(output), IClassFixture<VectorStoreRedisContainerFixture>
{
    private const int VectorSize = 1536;
    private const string MemoryStoreCollectionName = "memorystorecollection";

    [Fact]
    public async Task ConsumeExampleAsync()
    {
        // Setup the supporting infra and embedding generation.
        await redisFixture.ManualInitializeAsync();
        var textEmbeddingService = new AzureOpenAITextEmbeddingGenerationService(
            TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
            TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
            new AzureCliCredential());

        // Construct a legacy MemoryStore.
        var memoryStore = new RedisMemoryStore("localhost:6379", VectorSize);

        // Construct a VectorStore and indicate that we want to use hashes
        // since the legacy memory store uses hashes to store memory records.
        var vectorStore = new RedisVectorStore(
            ConnectionMultiplexer.Connect("localhost:6379").GetDatabase(),
            new() { StorageType = RedisStorageType.HashSet });

        // Build a collection with sample data using the MemoryStore abstraction.
        await VectorStore_ConsumeFromMemoryStore_Common.CreateCollectionAndAddSampleDataAsync(
            memoryStore,
            MemoryStoreCollectionName,
            textEmbeddingService);

        // Connect to the same collection using the VectorStore abstraction.
        var collection = vectorStore.GetCollection<string, VectorStoreRecord>(MemoryStoreCollectionName);
        await collection.CreateCollectionIfNotExistsAsync();

        // Show that the data can be read using the VectorStore abstraction.
        var record1 = await collection.GetAsync("11111111-1111-1111-1111-111111111111");
        var record2 = await collection.GetAsync("22222222-2222-2222-2222-222222222222");
        var record3 = await collection.GetAsync("33333333-3333-3333-3333-333333333333", new() { IncludeVectors = true });

        Console.WriteLine($"Record 1: Key: {record1!.Key} Timestamp: {DateTimeOffset.FromUnixTimeMilliseconds(record1.Timestamp)} Metadata: {record1.Metadata} Embedding {record1.Embedding}");
        Console.WriteLine($"Record 2: Key: {record2!.Key} Timestamp: {DateTimeOffset.FromUnixTimeMilliseconds(record2.Timestamp)} Metadata: {record2.Metadata} Embedding {record2.Embedding}");
        Console.WriteLine($"Record 3: Key: {record3!.Key} Timestamp: {DateTimeOffset.FromUnixTimeMilliseconds(record3.Timestamp)} Metadata: {record3.Metadata} Embedding {record3.Embedding}");
    }

    /// <summary>
    /// A data model with Vector Store attributes that matches the storage representation of
    /// <see cref="MemoryRecord"/> objects as created by <see cref="RedisMemoryStore"/>.
    /// </summary>
    private sealed class VectorStoreRecord
    {
        [VectorStoreRecordKey]
        public string Key { get; set; }

        [VectorStoreRecordData(StoragePropertyName = "metadata")]
        public string Metadata { get; set; }

        [VectorStoreRecordData(StoragePropertyName = "timestamp")]
        public long Timestamp { get; set; }

        [VectorStoreRecordVector(VectorSize, StoragePropertyName = "embedding")]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
}
