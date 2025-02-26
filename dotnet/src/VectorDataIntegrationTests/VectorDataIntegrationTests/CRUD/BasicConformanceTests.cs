// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.CRUD;

public abstract class BasicConformanceTests(VectorStoreFixture fixture)
{
    protected virtual string GetUniqueCollectionName() => Guid.NewGuid().ToString();

    [ConditionalFact]
    public async Task UpsertBatchAsync_EmptyBatch_DoesNotThrow()
    {
        await this.ExecuteAsync(async collection =>
        {
            Assert.Empty(await collection.UpsertBatchAsync([]).ToArrayAsync());
        });
    }

    [ConditionalFact]
    public async Task DeleteBatchAsync_EmptyBatch_DoesNotThrow()
    {
        await this.ExecuteAsync(async collection =>
        {
            await collection.DeleteBatchAsync([]);
        });
    }

    [ConditionalFact]
    public async Task GetBatchAsync_EmptyBatch_DoesNotThrow()
    {
        await this.ExecuteAsync(async collection =>
        {
            Assert.Empty(await collection.GetBatchAsync([]).ToArrayAsync());
        });
    }

    [ConditionalFact]
    public async Task UpsertBatchAsync_NullBatch_ThrowsArgumentNullException()
    {
        await this.ExecuteAsync(async collection =>
        {
            ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => collection.UpsertBatchAsync(records: null!).ToArrayAsync().AsTask());
            Assert.Equal("records", ex.ParamName);
        });
    }

    [ConditionalFact]
    public async Task DeleteBatchAsync_NullKeys_ThrowsArgumentNullException()
    {
        await this.ExecuteAsync(async collection =>
        {
            ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => collection.DeleteBatchAsync(keys: null!));
            Assert.Equal("keys", ex.ParamName);
        });
    }

    [ConditionalFact]
    public async Task GetBatchAsync_NullKeys_ThrowsArgumentNullException()
    {
        await this.ExecuteAsync(async collection =>
        {
            ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => collection.GetBatchAsync(keys: null!).ToArrayAsync().AsTask());
            Assert.Equal("keys", ex.ParamName);
        });
    }

    private async Task ExecuteAsync(Func<IVectorStoreRecordCollection<string, TestModel>, Task> test)
    {
        string collectionName = this.GetUniqueCollectionName();
        var collection = fixture.TestStore.DefaultVectorStore.GetCollection<string, TestModel>(collectionName);

        await collection.CreateCollectionAsync();

        try
        {
            await test(collection);
        }
        finally
        {
            await collection.DeleteCollectionAsync();
        }
    }

    public sealed class TestModel
    {
        [VectorStoreRecordKey(StoragePropertyName = "key")]
        public string? Id { get; set; }

        [VectorStoreRecordData(StoragePropertyName = "text")]
        public string? Text { get; set; }

        [VectorStoreRecordData(StoragePropertyName = "number")]
        public int Number { get; set; }

        [VectorStoreRecordVector(Dimensions: 10, StoragePropertyName = "embedding")]
        public ReadOnlyMemory<float> Floats { get; set; }
    }
}
