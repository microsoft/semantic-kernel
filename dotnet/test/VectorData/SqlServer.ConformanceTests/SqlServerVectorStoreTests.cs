// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;
using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace SqlServer.ConformanceTests;

public class SqlServerVectorStoreTests(SqlServerFixture fixture) : IClassFixture<SqlServerFixture>
{
    // this test may be once executed by multiple users against a shared db instance
    private static string GetUniqueCollectionName() => Guid.NewGuid().ToString();

    [ConditionalFact]
    public async Task CollectionCRUD()
    {
        string collectionName = GetUniqueCollectionName();
        var testStore = fixture.TestStore;
        var collection = testStore.DefaultVectorStore.GetCollection<string, TestModel>(collectionName);

        try
        {
            Assert.False(await collection.CollectionExistsAsync());

            Assert.False(await testStore.DefaultVectorStore.ListCollectionNamesAsync().ContainsAsync(collectionName));

            await collection.EnsureCollectionExistsAsync();

            Assert.True(await collection.CollectionExistsAsync());
            Assert.True(await testStore.DefaultVectorStore.ListCollectionNamesAsync().ContainsAsync(collectionName));

            await collection.EnsureCollectionExistsAsync();

            Assert.True(await collection.CollectionExistsAsync());

            await collection.EnsureCollectionDeletedAsync();

            Assert.False(await collection.CollectionExistsAsync());
            Assert.False(await testStore.DefaultVectorStore.ListCollectionNamesAsync().ContainsAsync(collectionName));
        }
        finally
        {
            await collection.EnsureCollectionDeletedAsync();
        }
    }

    [ConditionalFact]
    public async Task RecordCRUD()
    {
        string collectionName = GetUniqueCollectionName();
        var testStore = fixture.TestStore;
        var collection = testStore.DefaultVectorStore.GetCollection<string, TestModel>(collectionName);

        try
        {
            await collection.EnsureCollectionExistsAsync();

            TestModel inserted = new()
            {
                Id = "MyId",
                Number = 100,
                Floats = Enumerable.Range(0, 10).Select(i => (float)i).ToArray()
            };
            await collection.UpsertAsync(inserted);

            TestModel? received = await collection.GetAsync(inserted.Id, new() { IncludeVectors = true });
            AssertEquality(inserted, received);

            TestModel updated = new()
            {
                Id = inserted.Id,
                Number = inserted.Number + 200, // change one property
                Floats = inserted.Floats
            };
            await collection.UpsertAsync(updated);

            received = await collection.GetAsync(updated.Id, new() { IncludeVectors = true });
            AssertEquality(updated, received);

            VectorSearchResult<TestModel> vectorSearchResult = await (collection.SearchAsync(inserted.Floats, top: 3, new()
            {
                VectorProperty = r => r.Floats,
                IncludeVectors = true
            })).SingleAsync();
            AssertEquality(updated, vectorSearchResult.Record);

            vectorSearchResult = await (collection.SearchAsync(inserted.Floats, top: 3, new()
            {
                VectorProperty = r => r.Floats,
                IncludeVectors = false
            })).SingleAsync();
            // Make sure the vectors are not included in the result.
            Assert.Equal(0, vectorSearchResult.Record.Floats.Length);

            await collection.DeleteAsync(inserted.Id);

            Assert.Null(await collection.GetAsync(inserted.Id));
        }
        finally
        {
            await collection.EnsureCollectionDeletedAsync();
        }
    }

    [ConditionalFact]
    public async Task WrongModels()
    {
        string collectionName = GetUniqueCollectionName();
        var testStore = fixture.TestStore;
        var collection = testStore.DefaultVectorStore.GetCollection<string, TestModel>(collectionName);

        try
        {
            await collection.EnsureCollectionExistsAsync();

            TestModel inserted = new()
            {
                Id = "MyId",
                Text = "NotAnInt",
                Number = 100,
                Floats = Enumerable.Range(0, 10).Select(i => (float)i).ToArray()
            };
            await collection.UpsertAsync(inserted);

            // Let's use a model with different storage names to trigger an SQL exception
            // which should be mapped to VectorStoreException.
            var differentNamesCollection = testStore.DefaultVectorStore.GetCollection<string, DifferentStorageNames>(collectionName);
            VectorStoreException operationEx = await Assert.ThrowsAsync<VectorStoreException>(() => differentNamesCollection.GetAsync(inserted.Id));
            Assert.IsType<SqlException>(operationEx.InnerException);

            // Let's use a model with the same storage names, but different types
            // to trigger a mapping exception (casting a string to an int).
            var sameNameDifferentModelCollection = testStore.DefaultVectorStore.GetCollection<string, SameStorageNameButDifferentType>(collectionName);
            InvalidOperationException mappingEx = await Assert.ThrowsAsync<InvalidOperationException>(() => sameNameDifferentModelCollection.GetAsync(inserted.Id));
            Assert.IsType<InvalidCastException>(mappingEx.InnerException);

            // Let's use a model with the same storage names, but different types
            // to trigger a mapping exception (deserializing a string to Memory<float>).
            var invalidJsonCollection = testStore.DefaultVectorStore.GetCollection<string, SameStorageNameButInvalidVector>(collectionName);
            await Assert.ThrowsAsync<InvalidOperationException>(() => invalidJsonCollection.GetAsync(inserted.Id, new() { IncludeVectors = true }));
        }
        finally
        {
            await collection.EnsureCollectionDeletedAsync();
        }
    }

    [ConditionalFact]
    public async Task BatchCRUD()
    {
        string collectionName = GetUniqueCollectionName();
        var testStore = fixture.TestStore;
        var collection = testStore.DefaultVectorStore.GetCollection<string, TestModel>(collectionName);

        try
        {
            await collection.EnsureCollectionExistsAsync();

            var keys = Enumerable.Range(0, 10).Select(i => $"MyId{i}").ToArray();
            TestModel[] inserted = Enumerable.Range(0, 10).Select(i => new TestModel()
            {
                Id = keys[i],
                Number = 100 + i,
                Floats = Enumerable.Range(0, 10).Select(j => (float)(i + j)).ToArray()
            }).ToArray();

            await collection.UpsertAsync(inserted);

            TestModel[] received = await collection.GetAsync(keys, new() { IncludeVectors = true }).ToArrayAsync();
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

            await collection.UpsertAsync(updated);

            received = await collection.GetAsync(keys, new() { IncludeVectors = true }).ToArrayAsync();
            for (int i = 0; i < updated.Length; i++)
            {
                AssertEquality(updated[i], received[i]);
            }

            await collection.DeleteAsync(keys);

            Assert.False(await collection.GetAsync(keys).AnyAsync());
        }
        finally
        {
            await collection.EnsureCollectionDeletedAsync();
        }
    }

    private static void AssertEquality(TestModel inserted, TestModel? received)
    {
        Assert.NotNull(received);
        Assert.Equal(inserted.Number, received.Number);
        Assert.Equal(inserted.Id, received.Id);
        Assert.Equal(inserted.Floats.ToArray(), received.Floats.ToArray());
        Assert.Null(received.Text); // testing DBNull code path
    }

    public sealed class TestModel
    {
        [VectorStoreKey(StorageName = "key")]
        public string? Id { get; set; }

        [VectorStoreData(StorageName = "text")]
        public string? Text { get; set; }

        [VectorStoreData(StorageName = "column")]
        public int Number { get; set; }

        [VectorStoreVector(Dimensions: 10, StorageName = "embedding")]
        public ReadOnlyMemory<float> Floats { get; set; }
    }

    public sealed class SameStorageNameButDifferentType
    {
        [VectorStoreKey(StorageName = "key")]
        public string? Id { get; set; }

        [VectorStoreData(StorageName = "text")]
        public int Number { get; set; }
    }

    public sealed class SameStorageNameButInvalidVector
    {
        [VectorStoreKey(StorageName = "key")]
        public string? Id { get; set; }

        [VectorStoreVector(Dimensions: 10, StorageName = "text")]
        public ReadOnlyMemory<float> Floats { get; set; }
    }

    public sealed class DifferentStorageNames
    {
        [VectorStoreKey(StorageName = "key")]
        public string? Id { get; set; }

        [VectorStoreData(StorageName = "text2")]
        public string? Text { get; set; }

        [VectorStoreData(StorageName = "column2")]
        public int Number { get; set; }

        [VectorStoreVector(Dimensions: 10, StorageName = "embedding2")]
        public ReadOnlyMemory<float> Floats { get; set; }
    }

#if NETFRAMEWORK
    [ConditionalFact]
    public void TimeSpanIsNotSupported()
    {
        string collectionName = GetUniqueCollectionName();
        var testStore = fixture.TestStore;

        Assert.Throws<NotSupportedException>(() => testStore.DefaultVectorStore.GetCollection<string, TimeModel>(collectionName));
    }
#else
    [ConditionalFact]
    public async Task TimeOnlyIsSupported()
    {
        string collectionName = GetUniqueCollectionName();
        var testStore = fixture.TestStore;

        var collection = testStore.DefaultVectorStore.GetCollection<string, TimeModel>(collectionName);

        try
        {
            await collection.EnsureCollectionExistsAsync();

            TimeModel inserted = new()
            {
                Id = "MyId",
                Time = new TimeOnly(12, 34, 56)
            };
            await collection.UpsertAsync(inserted);

            TimeModel? received = await collection.GetAsync(inserted.Id, new() { IncludeVectors = true });
            Assert.NotNull(received);
            Assert.Equal(inserted.Time, received.Time);
        }
        finally
        {
            await collection.EnsureCollectionDeletedAsync();
        }
    }
#endif

    public sealed class TimeModel
    {
        [VectorStoreKey(StorageName = "key")]
        public string? Id { get; set; }

        [VectorStoreData(StorageName = "time")]
#if NETFRAMEWORK
        public TimeSpan Time { get; set; }
#else
        public TimeOnly Time { get; set; }
#endif
    }

    [ConditionalFact]
    public Task CanUseFancyModels_Int() => this.CanUseFancyModels<int>();

    [ConditionalFact]
    public Task CanUseFancyModels_Long() => this.CanUseFancyModels<long>();

    [ConditionalFact]
    public Task CanUseFancyModels_Guid() => this.CanUseFancyModels<Guid>();

    private async Task CanUseFancyModels<TKey>() where TKey : notnull
    {
        string collectionName = GetUniqueCollectionName();
        var testStore = fixture.TestStore;
        var collection = testStore.DefaultVectorStore.GetCollection<TKey, FancyTestModel<TKey>>(collectionName);

        try
        {
            await collection.EnsureCollectionExistsAsync();

            var key = testStore.GenerateKey<TKey>(1);
            FancyTestModel<TKey> inserted = new()
            {
                Id = key,
                Number8 = byte.MaxValue,
                Number16 = short.MaxValue,
                Number32 = int.MaxValue,
                Number64 = long.MaxValue,
                Floats = Enumerable.Range(0, 10).Select(i => (float)i).ToArray(),
                Bytes = [1, 2, 3],
            };
            await collection.UpsertAsync(inserted);

            FancyTestModel<TKey>? received = await collection.GetAsync(key, new() { IncludeVectors = true });
            AssertEquality(inserted, received, key);

            FancyTestModel<TKey> updated = new()
            {
                Id = key,
                Number16 = short.MinValue, // change one property
                Floats = inserted.Floats
            };
            await collection.UpsertAsync(updated);

            received = await collection.GetAsync(updated.Id, new() { IncludeVectors = true });
            AssertEquality(updated, received, key);

            await collection.DeleteAsync(key);

            Assert.Null(await collection.GetAsync(key));
        }
        finally
        {
            await collection.EnsureCollectionDeletedAsync();
        }

        void AssertEquality(FancyTestModel<TKey> expected, FancyTestModel<TKey>? received, TKey expectedKey)
        {
            Assert.NotNull(received);
            Assert.Equal(expectedKey, received.Id);
            Assert.Equal(expected.Number8, received.Number8);
            Assert.Equal(expected.Number16, received.Number16);
            Assert.Equal(expected.Number32, received.Number32);
            Assert.Equal(expected.Number64, received.Number64);
            Assert.Equal(expected.Floats.ToArray(), received.Floats.ToArray());
            Assert.Equal(expected.Bytes, received.Bytes);
        }
    }

    public sealed class FancyTestModel<TKey>
    {
        [VectorStoreKey(StorageName = "key")]
        public TKey? Id { get; set; }

        [VectorStoreData(StorageName = "byte")]
        public byte Number8 { get; set; }

        [VectorStoreData(StorageName = "short")]
        public short Number16 { get; set; }

        [VectorStoreData(StorageName = "int")]
        public int Number32 { get; set; }

        [VectorStoreData(StorageName = "long")]
        public long Number64 { get; set; }

        [VectorStoreData(StorageName = "bytes")]
#pragma warning disable CA1819 // Properties should not return arrays
        public byte[]? Bytes { get; set; }
#pragma warning restore CA1819 // Properties should not return arrays

        [VectorStoreVector(Dimensions: 10, StorageName = "embedding")]
        public ReadOnlyMemory<float> Floats { get; set; }
    }
}
