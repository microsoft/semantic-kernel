// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Data;

namespace Memory;

public class VectorStore_HelloWorld(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task UpsertGetVolatileAsync()
    {
        var kernel = Kernel
            .CreateBuilder()
            .AddVolatileVectorStore()
            .Build();

        var vectorStore = kernel.GetRequiredService<IVectorStore>();

        var collection = vectorStore.GetCollection<string, StringKeyModel>("mycollection");

        await collection.CreateCollectionIfNotExistsAsync();

        var upsertedId = await collection.UpsertAsync(new StringKeyModel { Key = "key1", SomeStringData = "the string payload", Embedding = new ReadOnlyMemory<float>(new float[4] { 1.1f, 2.2f, 3.3f, 4.4f }) });
        Console.WriteLine(upsertedId);

        var retrievedData = await collection.GetAsync(upsertedId, new() { IncludeVectors = true });
        Console.WriteLine(retrievedData);
    }

    [Fact]
    public async Task UpsertGetQdrantAsync()
    {
        var kernel = Kernel
            .CreateBuilder()
            .AddQdrantVectorStore("localhost")
            .Build();

        var vectorStore = kernel.GetRequiredService<IVectorStore>();

        var collection = vectorStore.GetCollection<Guid, GuidKeyModel>("mycollection");

        await collection.CreateCollectionIfNotExistsAsync();

        var upsertedId = await collection.UpsertAsync(new GuidKeyModel { Key = Guid.NewGuid(), SomeStringData = "the string payload", Embedding = new ReadOnlyMemory<float>(new float[4] { 1.1f, 2.2f, 3.3f, 4.4f }) });
        Console.WriteLine(upsertedId);

        var retrievedData = await collection.GetAsync(upsertedId, new() { IncludeVectors = true });
        Console.WriteLine(retrievedData);
    }

    [Fact]
    public async Task UpsertGetRedisAsync()
    {
        var kernel = Kernel
            .CreateBuilder()
            .AddRedisVectorStore("localhost:6379")
            .Build();

        var vectorStore = kernel.GetRequiredService<IVectorStore>();

        var collection = vectorStore.GetCollection<string, StringKeyModel>("mycollection");

        await collection.CreateCollectionIfNotExistsAsync();

        var upsertedId = await collection.UpsertAsync(new StringKeyModel { Key = "key1", SomeStringData = "the string payload", Embedding = new ReadOnlyMemory<float>(new float[4] { 1.1f, 2.2f, 3.3f, 4.4f }) });
        Console.WriteLine(upsertedId);

        var retrievedData = await collection.GetAsync(upsertedId, new() { IncludeVectors = true });
        Console.WriteLine(retrievedData);
    }

    private sealed class StringKeyModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; }

        [VectorStoreRecordData]
        public string SomeStringData { get; set; }

        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }

    private sealed class GuidKeyModel
    {
        [VectorStoreRecordKey]
        public Guid Key { get; set; }

        [VectorStoreRecordData]
        public string SomeStringData { get; set; }

        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
}
