// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace VectorDataSpecificationTests.Support;

public abstract class GenericDataModelFixture<TKey> : VectorStoreCollectionFixture<TKey, VectorStoreGenericDataModel<TKey>>
    where TKey : notnull
{
    public const string KeyPropertyName = "key";
    public const string StringPropertyName = "text";
    public const string IntegerPropertyName = "integer";
    public const string EmbeddingPropertyName = "embedding";
    public const int DimensionCount = 3;

    protected override VectorStoreRecordDefinition GetRecordDefinition()
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

    protected override List<VectorStoreGenericDataModel<TKey>> BuildTestData() =>
    [
        new(this.GenerateNextKey<TKey>())
        {
            Data =
            {
                [StringPropertyName] = "first",
                [IntegerPropertyName] = 1
            },
            Vectors =
            {
                [EmbeddingPropertyName] = new ReadOnlyMemory<float>(Enumerable.Repeat(0.1f, DimensionCount).ToArray())
            }
        },
        new(this.GenerateNextKey<TKey>())
        {
            Data =
            {
                [StringPropertyName] = "second",
                [IntegerPropertyName] = 2
            },
            Vectors =
            {
                [EmbeddingPropertyName] = new ReadOnlyMemory<float>(Enumerable.Repeat(0.2f, DimensionCount).ToArray())
            }
        },
        new(this.GenerateNextKey<TKey>())
        {
            Data =
            {
                [StringPropertyName] = "third",
                [IntegerPropertyName] = 3
            },
            Vectors =
            {
                [EmbeddingPropertyName] = new ReadOnlyMemory<float>(Enumerable.Repeat(0.3f, DimensionCount).ToArray())
            }
        },
        new(this.GenerateNextKey<TKey>())
        {
            Data =
            {
                [StringPropertyName] = "fourth",
                [IntegerPropertyName] = 4
            },
            Vectors =
            {
                [EmbeddingPropertyName] = new ReadOnlyMemory<float>(Enumerable.Repeat(0.4f, DimensionCount).ToArray())
            }
        }
    ];
}
