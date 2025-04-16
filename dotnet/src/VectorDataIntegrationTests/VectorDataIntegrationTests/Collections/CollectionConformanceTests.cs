// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Models;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.Collections;

public abstract class CollectionConformanceTests<TKey>(VectorStoreFixture fixture)
    where TKey : notnull
{
    [ConditionalFact]
    public async Task VectorStoreDeleteCollectionDeletesExistingCollection()
    {
        // Arrange.
        var collection = await this.GetNonExistingCollectionAsync<SimpleRecord<TKey>>();
        await collection.CreateCollectionAsync();
        Assert.True(await collection.CollectionExistsAsync());

        // Act.
        await fixture.TestStore.DefaultVectorStore.DeleteCollectionAsync(collection.Name);

        // Assert.
        Assert.False(await collection.CollectionExistsAsync());
    }

    [ConditionalFact]
    public async Task VectorStoreDeleteCollectionDoesNotThrowForNonExistingCollection()
    {
        await fixture.TestStore.DefaultVectorStore.DeleteCollectionAsync(fixture.GetUniqueCollectionName());
    }

    [ConditionalFact]
    public async Task VectorStoreCollectionExistsReturnsTrueForExistingCollection()
    {
        // Arrange.
        var collection = await this.GetNonExistingCollectionAsync<SimpleRecord<TKey>>();

        try
        {
            await collection.CreateCollectionAsync();

            // Act & Assert.
            Assert.True(await fixture.TestStore.DefaultVectorStore.CollectionExistsAsync(collection.Name));
        }
        finally
        {
            await collection.DeleteCollectionAsync();
        }
    }

    [ConditionalFact]
    public async Task VectorStoreCollectionExistsReturnsFalseForNonExistingCollection()
    {
        Assert.False(await fixture.TestStore.DefaultVectorStore.CollectionExistsAsync(fixture.GetUniqueCollectionName()));
    }

    [ConditionalTheory]
    [MemberData(nameof(UseDynamicMappingData))]
    public Task DeleteCollectionDoesNotThrowForNonExistingCollection(bool useDynamicMapping)
    {
        return useDynamicMapping ? Core<Dictionary<string, object?>>() : Core<SimpleRecord<TKey>>();

        async Task Core<TRecord>() where TRecord : notnull
        {
            var collection = await this.GetNonExistingCollectionAsync<TRecord>();

            await collection.DeleteCollectionAsync();
        }
    }

    [ConditionalTheory]
    [MemberData(nameof(UseDynamicMappingData))]
    public Task CreateCollectionCreatesTheCollection(bool useDynamicMapping)
    {
        return useDynamicMapping ? Core<Dictionary<string, object?>>() : Core<SimpleRecord<TKey>>();

        async Task Core<TRecord>() where TRecord : notnull
        {
            var collection = await this.GetNonExistingCollectionAsync<TRecord>();

            await collection.CreateCollectionAsync();

            try
            {
                Assert.True(await collection.CollectionExistsAsync());

                var collectionMetadata = collection.GetService(typeof(VectorStoreRecordCollectionMetadata)) as VectorStoreRecordCollectionMetadata;

                Assert.NotNull(collectionMetadata);
                Assert.NotNull(collectionMetadata.VectorStoreSystemName);
                Assert.NotNull(collectionMetadata.CollectionName);

                Assert.True(await fixture.TestStore.DefaultVectorStore.ListCollectionNamesAsync().ContainsAsync(collectionMetadata.CollectionName));
            }
            finally
            {
                await collection.DeleteCollectionAsync();
            }
        }
    }

    [ConditionalTheory]
    [MemberData(nameof(UseDynamicMappingData))]
    public Task CreateCollectionIfNotExistsCalledMoreThanOnceDoesNotThrow(bool useDynamicMapping)
    {
        return useDynamicMapping ? Core<Dictionary<string, object?>>() : Core<SimpleRecord<TKey>>();

        async Task Core<TRecord>() where TRecord : notnull
        {
            var collection = await this.GetNonExistingCollectionAsync<TRecord>();

            await collection.CreateCollectionIfNotExistsAsync();

            try
            {
                Assert.True(await collection.CollectionExistsAsync());

                var collectionMetadata = collection.GetService(typeof(VectorStoreRecordCollectionMetadata)) as VectorStoreRecordCollectionMetadata;

                Assert.NotNull(collectionMetadata);
                Assert.NotNull(collectionMetadata.VectorStoreSystemName);
                Assert.NotNull(collectionMetadata.CollectionName);

                Assert.True(await fixture.TestStore.DefaultVectorStore.ListCollectionNamesAsync().ContainsAsync(collectionMetadata.CollectionName));

                await collection.CreateCollectionIfNotExistsAsync();
            }
            finally
            {
                await collection.DeleteCollectionAsync();
            }
        }
    }

    [ConditionalTheory]
    [MemberData(nameof(UseDynamicMappingData))]
    public Task CreateCollectionCalledMoreThanOnceThrowsVectorStoreOperationException(bool useDynamicMapping)
    {
        return useDynamicMapping ? Core<Dictionary<string, object?>>() : Core<SimpleRecord<TKey>>();

        async Task Core<TRecord>() where TRecord : notnull
        {
            var collection = await this.GetNonExistingCollectionAsync<TRecord>();

            await collection.CreateCollectionAsync();

            try
            {
                Assert.True(await collection.CollectionExistsAsync());

                var collectionMetadata = collection.GetService(typeof(VectorStoreRecordCollectionMetadata)) as VectorStoreRecordCollectionMetadata;

                Assert.NotNull(collectionMetadata);
                Assert.NotNull(collectionMetadata.VectorStoreSystemName);
                Assert.NotNull(collectionMetadata.CollectionName);

                Assert.True(await fixture.TestStore.DefaultVectorStore.ListCollectionNamesAsync().ContainsAsync(collectionMetadata.CollectionName));

                await collection.CreateCollectionIfNotExistsAsync();

                await Assert.ThrowsAsync<VectorStoreOperationException>(() => collection.CreateCollectionAsync());
            }
            finally
            {
                await collection.DeleteCollectionAsync();
            }
        }
    }

    protected virtual async Task<IVectorStoreRecordCollection<TKey, TRecord>> GetNonExistingCollectionAsync<TRecord>() where TRecord : notnull
    {
        var definition = new VectorStoreRecordDefinition()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(SimpleRecord<object>.Id), typeof(TKey)) { StoragePropertyName = "key" },
                new VectorStoreRecordDataProperty(nameof(SimpleRecord<object>.Text), typeof(string)) { StoragePropertyName = "text" },
                new VectorStoreRecordDataProperty(nameof(SimpleRecord<object>.Number), typeof(int)) { StoragePropertyName = "number" },
                new VectorStoreRecordVectorProperty(nameof(SimpleRecord<object>.Floats), typeof(ReadOnlyMemory<float>), 10) { IndexKind = fixture.TestStore.DefaultIndexKind }
            ]
        };

        var collection = fixture.TestStore.DefaultVectorStore.GetCollection<TKey, TRecord>(fixture.GetUniqueCollectionName(), definition);
        await collection.DeleteCollectionAsync();
        return collection;
    }

    public static readonly IEnumerable<object[]> UseDynamicMappingData = [[false], [true]];
}
