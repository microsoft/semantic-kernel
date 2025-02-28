// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.CRUD;

public abstract class GenericDataModelConformanceTests<TKey>(VectorStoreFixture fixture)
    : ConformanceTestsBase<TKey, VectorStoreGenericDataModel<TKey>>(fixture) where TKey : notnull
{
    private const string KeyPropertyName = "key";
    private const string StringPropertyName = "text";
    private const string IntegerPropertyName = "integer";
    private const string EmbeddingPropertyName = "embedding";
    private const int DimensionCount = 10;

    protected override VectorStoreRecordDefinition? GetRecordDefinition()
        => new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(KeyPropertyName, typeof(TKey)),
                new VectorStoreRecordDataProperty(StringPropertyName, typeof(string)),
                new VectorStoreRecordDataProperty(IntegerPropertyName, typeof(int)),
                new VectorStoreRecordVectorProperty(EmbeddingPropertyName, typeof(ReadOnlyMemory<float>))
                {
                    Dimensions = DimensionCount
                }
            ]
        };

    [ConditionalFact]
    public async Task CanInsertUpdateAndDelete()
    {
        await this.ExecuteAsync(async collection =>
        {
            VectorStoreGenericDataModel<TKey> inserted = new(key: this.Fixture.GenerateNextKey<TKey>());
            inserted.Data.Add(StringPropertyName, "some");
            inserted.Data.Add(IntegerPropertyName, 123);
            inserted.Vectors.Add(EmbeddingPropertyName, new ReadOnlyMemory<float>(Enumerable.Repeat(0.1f, DimensionCount).ToArray()));

            TKey key = await collection.UpsertAsync(inserted);
            Assert.Equal(inserted.Key, key);

            VectorStoreGenericDataModel<TKey>? received = await collection.GetAsync(key, new() { IncludeVectors = true });
            Assert.NotNull(received);

            Assert.Equal(received.Key, key);
            foreach (var pair in inserted.Data)
            {
                Assert.Equal(pair.Value, received.Data[pair.Key]);
            }

            Assert.Equal(
                ((ReadOnlyMemory<float>)inserted.Vectors[EmbeddingPropertyName]!).ToArray(),
                ((ReadOnlyMemory<float>)received.Vectors[EmbeddingPropertyName]!).ToArray());

            await collection.DeleteAsync(key);

            received = await collection.GetAsync(key);
            Assert.Null(received);
        });
    }
}
