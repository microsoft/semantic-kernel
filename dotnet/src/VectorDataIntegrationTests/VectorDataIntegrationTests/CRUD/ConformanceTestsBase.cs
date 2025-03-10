// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Models;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace VectorDataSpecificationTests.CRUD;

// TKey is a generic parameter because different connectors support different key types.
public abstract class ConformanceTestsBase<TKey, TRecord>(VectorStoreFixture fixture) where TKey : notnull
{
    protected VectorStoreFixture Fixture { get; } = fixture;

    protected virtual string GetUniqueCollectionName() => Guid.NewGuid().ToString();

    protected virtual VectorStoreRecordDefinition? GetRecordDefinition() => null;

    protected async Task ExecuteAsync(Func<IVectorStoreRecordCollection<TKey, TRecord>, Task> test, bool createCollection = true)
    {
        string collectionName = this.GetUniqueCollectionName();
        var collection = this.Fixture.TestStore.DefaultVectorStore.GetCollection<TKey, TRecord>(collectionName,
            this.GetRecordDefinition());

        if (createCollection)
        {
            await collection.CreateCollectionAsync();
        }

        try
        {
            await test(collection);
        }
        finally
        {
            await collection.DeleteCollectionAsync();
        }
    }

    protected virtual void AssertEqual(TRecord expected, TRecord? actual, bool includeVectors)
    {
        Assert.NotNull(actual);

        if (typeof(TRecord) == typeof(SimpleModel<TKey>))
        {
            var expectedSimple = (SimpleModel<TKey>)(object)expected!;
            var actualSimple = (SimpleModel<TKey>)(object)actual!;

            Assert.Equal(expectedSimple!.Id, actualSimple!.Id);
            Assert.Equal(expectedSimple.Text, actualSimple.Text);
            Assert.Equal(expectedSimple.Number, actualSimple.Number);

            if (includeVectors)
            {
                Assert.Equal(expectedSimple.Floats.ToArray(), actualSimple.Floats.ToArray());
            }
            else
            {
                Assert.Equal(0, actualSimple.Floats.Length);
            }
        }
        else if (typeof(TRecord) == typeof(VectorStoreGenericDataModel<TKey>))
        {
            var expectedGeneric = (VectorStoreGenericDataModel<TKey>)(object)expected!;
            var actualGeneric = (VectorStoreGenericDataModel<TKey>)(object)actual!;

            Assert.Equal(expectedGeneric!.Key, actualGeneric!.Key);

            foreach (var pair in expectedGeneric.Data)
            {
                Assert.Equal(pair.Value, actualGeneric.Data[pair.Key]);
            }

            foreach (var pair in expectedGeneric.Vectors)
            {
                if (includeVectors)
                {
                    Assert.Equal(
                        ((ReadOnlyMemory<float>)pair.Value!).ToArray(),
                        ((ReadOnlyMemory<float>)actualGeneric.Vectors[pair.Key]!).ToArray());
                }
                else
                {
                    Assert.Equal(0, ((ReadOnlyMemory<float>)actualGeneric.Vectors[pair.Key]!).Length);
                }
            }
        }
        else
        {
            throw new NotSupportedException($"Type {typeof(TRecord)} is not supported.");
        }
    }
}
