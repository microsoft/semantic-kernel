// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace VectorDataSpecificationTests.Support;

public abstract class DynamicDataModelFixture<TKey> : VectorStoreCollectionFixture<object, Dictionary<string, object?>>
{
    public const string KeyPropertyName = "key";
    public const string StringPropertyName = "text";
    public const string IntegerPropertyName = "integer";
    public const string EmbeddingPropertyName = "embedding";
    public const int DimensionCount = 3;

    public override VectorStoreRecordDefinition GetRecordDefinition()
        => new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(KeyPropertyName, typeof(TKey)),
                new VectorStoreRecordDataProperty(StringPropertyName, typeof(string)),
                new VectorStoreRecordDataProperty(IntegerPropertyName, typeof(int)),
                new VectorStoreRecordVectorProperty(EmbeddingPropertyName, typeof(ReadOnlyMemory<float>), DimensionCount)
            ]
        };

    protected override List<Dictionary<string, object?>> BuildTestData() =>
    [
        new()
        {
            [KeyPropertyName] = this.GenerateNextKey<TKey>(),
            [StringPropertyName] = "first",
            [IntegerPropertyName] = 1,
            [EmbeddingPropertyName] = new ReadOnlyMemory<float>(Enumerable.Repeat(0.1f, DimensionCount).ToArray())
        },
        new()
        {
            [KeyPropertyName] = this.GenerateNextKey<TKey>(),
            [StringPropertyName] = "second",
            [IntegerPropertyName] = 2,
            [EmbeddingPropertyName] = new ReadOnlyMemory<float>(Enumerable.Repeat(0.2f, DimensionCount).ToArray())
        },
        new()
        {
            [KeyPropertyName] = this.GenerateNextKey<TKey>(),
            [StringPropertyName] = "third",
            [IntegerPropertyName] = 3,
            [EmbeddingPropertyName] = new ReadOnlyMemory<float>(Enumerable.Repeat(0.3f, DimensionCount).ToArray())
        },
        new()
        {
            [KeyPropertyName] = this.GenerateNextKey<TKey>(),
            [StringPropertyName] = "fourth",
            [IntegerPropertyName] = 4,
            [EmbeddingPropertyName] = new ReadOnlyMemory<float>(Enumerable.Repeat(0.4f, DimensionCount).ToArray())
        }
    ];
}
