// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Xunit;

namespace SemanticKernel.Connectors.InMemory.UnitTests;

public class InMemoryVectorStoreExtensionsTests
{
    [Fact]
    public async Task SerializeAndDeserializeCollectionRoundtripWorks()
    {
        // Arrange
        using var vectorStore = new InMemoryVectorStore();
        var collectionName = "test-collection";
        var collection = vectorStore.GetCollection<Guid, TestRecord>(collectionName);

        var record1 = new TestRecord
        {
            Key = Guid.NewGuid(),
            Text = "First record",
            Embedding = new ReadOnlyMemory<float>(new float[] { 0.1f, 0.2f, 0.3f })
        };
        var record2 = new TestRecord
        {
            Key = Guid.NewGuid(),
            Text = "Second record",
            Embedding = new ReadOnlyMemory<float>(new float[] { 0.4f, 0.5f, 0.6f })
        };

        await collection.EnsureCollectionExistsAsync();
        await collection.UpsertAsync(new[] { record1, record2 });

        // Act
        using var memStream = new MemoryStream();
        await vectorStore.SerializeCollectionAsJsonAsync<Guid, TestRecord>(collectionName, memStream);
        memStream.Position = 0;

        // Simulate loading into a new store
        using var newVectorStore = new InMemoryVectorStore();
        var deserializedCollection = await newVectorStore.DeserializeCollectionFromJsonAsync<Guid, TestRecord>(memStream);

        // Assert
        Assert.NotNull(deserializedCollection);
        var loadedRecord1 = await deserializedCollection.GetAsync(record1.Key);
        var loadedRecord2 = await deserializedCollection.GetAsync(record2.Key);

        Assert.NotNull(loadedRecord1);
        Assert.NotNull(loadedRecord2);
        Assert.Equal(record1.Text, loadedRecord1.Text);
        Assert.Equal(record2.Text, loadedRecord2.Text);
        Assert.Equal(record1.Embedding, loadedRecord1.Embedding);
        Assert.Equal(record2.Embedding, loadedRecord2.Embedding);
    }

    [Fact]
    public async Task SerializeAndDeserializeCollectionRoundtripWithBuiltInEmbeddingGenerationWorks()
    {
        // Arrange
        using var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = new FakeEmbeddingGenerator() });
        var collectionName = "test-collection";
        var collection = vectorStore.GetCollection<Guid, TestRecordAutoEmbed>(collectionName);

        var record1 = new TestRecordAutoEmbed
        {
            Key = Guid.NewGuid(),
            Text = "First record",
        };
        var record2 = new TestRecordAutoEmbed
        {
            Key = Guid.NewGuid(),
            Text = "Second record",
        };

        await collection.EnsureCollectionExistsAsync();
        await collection.UpsertAsync(new[] { record1, record2 });

        // Act
        using var memStream = new MemoryStream();
        await vectorStore.SerializeCollectionAsJsonAsync<Guid, TestRecordAutoEmbed>(collectionName, memStream);
        memStream.Position = 0;

        // Simulate loading into a new store
        using var newVectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = new FakeEmbeddingGenerator() });
        var deserializedCollection = await newVectorStore.DeserializeCollectionFromJsonAsync<Guid, TestRecordAutoEmbed>(memStream);

        // Assert
        Assert.NotNull(deserializedCollection);
        var loadedRecord1 = await deserializedCollection.GetAsync(record1.Key);
        var loadedRecord2 = await deserializedCollection.GetAsync(record2.Key);

        Assert.NotNull(loadedRecord1);
        Assert.NotNull(loadedRecord2);
        Assert.Equal(record1.Text, loadedRecord1.Text);
        Assert.Equal(record2.Text, loadedRecord2.Text);
    }

    [Fact]
    public async Task DeserializeCollectionFromJsonAsyncThrowsOnInvalidJson()
    {
        using var vectorStore = new InMemoryVectorStore();
        using var memStream = new MemoryStream(System.Text.Encoding.UTF8.GetBytes("{ invalid json }"));

        await Assert.ThrowsAsync<JsonException>(async () =>
        {
            await vectorStore.DeserializeCollectionFromJsonAsync<Guid, TestRecord>(memStream);
        });
    }

    private sealed class TestRecord
    {
        [VectorStoreKey]
        public Guid Key { get; init; }

        [VectorStoreData]
        public string Text { get; init; } = string.Empty;

        [VectorStoreVector(3)]
        public ReadOnlyMemory<float> Embedding { get; init; }
    }

    private sealed class TestRecordAutoEmbed
    {
        [VectorStoreKey]
        public Guid Key { get; init; }

        [VectorStoreData]
        public string Text { get; init; } = string.Empty;

        [VectorStoreVector(3)]
        public string Embedding => this.Text;
    }

    private sealed class FakeEmbeddingGenerator() : IEmbeddingGenerator<string, Embedding<float>>
    {
        public Task<GeneratedEmbeddings<Embedding<float>>> GenerateAsync(
            IEnumerable<string> values,
            EmbeddingGenerationOptions? options = null,
            CancellationToken cancellationToken = default)
        {
            var results = new GeneratedEmbeddings<Embedding<float>>();

            foreach (var value in values)
            {
                results.Add(new Embedding<float>(new float[] { 0.1f, 0.2f, 0.3f }));
            }

            return Task.FromResult(results);
        }

        public object? GetService(Type serviceType, object? serviceKey = null)
            => null;

        public void Dispose()
        {
        }
    }
}
