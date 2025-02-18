using System.Linq;
using Microsoft.Extensions.VectorData;
using SqlServerIntegrationTests.Support;
using Xunit;

namespace SqlServerIntegrationTests;

public class SqlServerVectorStoreTests
{
    [Fact]
    public async Task CanCreateAndDeleteTheCollections()
    {
        SqlServerTestStore testStore = new();

        await testStore.ReferenceCountingStartAsync();

        var collection = testStore.DefaultVectorStore.GetCollection<string, TestModel>("collection");

        try
        {
            Assert.False(await collection.CollectionExistsAsync());

            await collection.CreateCollectionAsync();

            Assert.True(await collection.CollectionExistsAsync());

            await collection.CreateCollectionIfNotExistsAsync();

            Assert.True(await collection.CollectionExistsAsync());

            await collection.DeleteCollectionAsync();

            Assert.False(await collection.CollectionExistsAsync());
        }
        finally
        {
            await collection.DeleteCollectionAsync();

            await testStore.ReferenceCountingStopAsync();
        }
    }

    [Fact]
    public async Task RecordCRUD()
    {
        SqlServerTestStore testStore = new();

        await testStore.ReferenceCountingStartAsync();

        var collection = testStore.DefaultVectorStore.GetCollection<string, TestModel>("other");

        try
        {
            await collection.CreateCollectionIfNotExistsAsync();

            TestModel inserted = new()
            {
                Id = "MyId",
                Number = 100,
                Floats = Enumerable.Range(0, 10).Select(i => (float)i).ToArray()
            };
            string key = await collection.UpsertAsync(inserted);
            Assert.Equal(inserted.Id, key);

            TestModel? received = await collection.GetAsync(inserted.Id);
            AssertEquality(inserted, received);

            TestModel updated = new()
            {
                Id = inserted.Id,
                Number = inserted.Number + 200, // change one property
                Floats = inserted.Floats
            };
            key = await collection.UpsertAsync(updated);
            Assert.Equal(inserted.Id, key);

            received = await collection.GetAsync(updated.Id);
            AssertEquality(updated, received);

            await collection.DeleteAsync(inserted.Id);

            Assert.Null(await collection.GetAsync(inserted.Id));
        }
        finally
        {
            await collection.DeleteCollectionAsync();

            await testStore.ReferenceCountingStopAsync();
        }
    }

    [Fact]
    public async Task BatchCRUD()
    {
        SqlServerTestStore testStore = new();

        await testStore.ReferenceCountingStartAsync();

        var collection = testStore.DefaultVectorStore.GetCollection<string, TestModel>("other");

        try
        {
            await collection.CreateCollectionIfNotExistsAsync();

            TestModel[] inserted = Enumerable.Range(0, 10).Select(i => new TestModel()
            {
                Id = $"MyId{i}",
                Number = 100 + i,
                Floats = Enumerable.Range(0, 10).Select(j => (float)(i + j)).ToArray()
            }).ToArray();

            string[] keys = await collection.UpsertBatchAsync(inserted).ToArrayAsync();
            for (int i = 0; i < inserted.Length; i++)
            {
                Assert.Equal(inserted[i].Id, keys[i]);
            }

            TestModel[] received = await collection.GetBatchAsync(keys).ToArrayAsync();
            for (int i = 0; i < inserted.Length; i++)
            {
                AssertEquality(inserted[i], received[i]);
            }

            TestModel[] updated = inserted.Select(i => new TestModel()
            {
                Id = i.Id,
                Number = i.Number + 200, // change one property
                Floats = i.Floats
            }).ToArray();

            keys = await collection.UpsertBatchAsync(updated).ToArrayAsync();
            for (int i = 0; i < updated.Length; i++)
            {
                Assert.Equal(updated[i].Id, keys[i]);
            }

            received = await collection.GetBatchAsync(keys).ToArrayAsync();
            for (int i = 0; i < updated.Length; i++)
            {
                AssertEquality(updated[i], received[i]);
            }

            await collection.DeleteBatchAsync(keys);

            Assert.False(await collection.GetBatchAsync(keys).AnyAsync());
        }
        finally
        {
            await collection.DeleteCollectionAsync();

            await testStore.ReferenceCountingStopAsync();
        }
    }

    private static void AssertEquality(TestModel inserted, TestModel? received)
    {
        Assert.NotNull(received);
        Assert.Equal(inserted.Number, received.Number);
        Assert.Equal(inserted.Id, received.Id);
        Assert.Equal(inserted.Floats, received.Floats);
        Assert.Null(received.Text); // testing DBNull code path
    }

    public sealed class TestModel
    {
        [VectorStoreRecordKey(StoragePropertyName = "key")]
        public string Id { get; set; }

        [VectorStoreRecordData(StoragePropertyName = "text")]
        public string? Text { get; set; }

        [VectorStoreRecordData(StoragePropertyName = "column")]
        public int Number { get; set; }

        [VectorStoreRecordVector(Dimensions: 10, StoragePropertyName = "embedding")]
        public ReadOnlyMemory<float> Floats { get; set; }
    }
}
