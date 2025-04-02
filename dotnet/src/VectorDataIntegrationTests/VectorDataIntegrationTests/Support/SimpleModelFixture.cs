// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Models;

namespace VectorDataSpecificationTests.Support;

public abstract class SimpleModelFixture<TKey> : VectorStoreCollectionFixture<TKey, SimpleModel<TKey>>
    where TKey : notnull
{
    protected override List<SimpleModel<TKey>> BuildTestData() =>
    [
        new()
        {
            Id = this.GenerateNextKey<TKey>(),
            Number = 1,
            Text = "UsedByGetTests",
            Floats = Enumerable.Repeat(0.1f, SimpleModel<TKey>.DimensionCount).ToArray()
        },
        new()
        {
            Id = this.GenerateNextKey<TKey>(),
            Number = 2,
            Text = "UsedByUpdateTests",
            Floats = Enumerable.Repeat(0.2f, SimpleModel<TKey>.DimensionCount).ToArray()
        },
        new()
        {
            Id = this.GenerateNextKey<TKey>(),
            Number = 3,
            Text = "UsedByDeleteTests",
            Floats = Enumerable.Repeat(0.3f, SimpleModel<TKey>.DimensionCount).ToArray()
        },
        new()
        {
            Id = this.GenerateNextKey<TKey>(),
            Number = 4,
            Text = "UsedByDeleteBatchTests",
            Floats = Enumerable.Repeat(0.4f, SimpleModel<TKey>.DimensionCount).ToArray()
        }
    ];

    protected override VectorStoreRecordDefinition GetRecordDefinition()
        => new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(SimpleModel<TKey>.Id), typeof(TKey))
                {
                    StoragePropertyName = "i d" // intentionally with a space
                },
                new VectorStoreRecordVectorProperty(nameof(SimpleModel<TKey>.Floats), typeof(ReadOnlyMemory<float>?))
                {
                    Dimensions = SimpleModel<TKey>.DimensionCount,
                    DistanceFunction = this.DistanceFunction,
                    IndexKind = this.IndexKind,
                    StoragePropertyName = "embed\"ding" // intentionally with quotes
                },
                new VectorStoreRecordDataProperty(nameof(SimpleModel<TKey>.Number), typeof(int))
                {
                    IsFilterable = true,
                    StoragePropertyName = "num'ber" // intentionally with a single quote

                },
                new VectorStoreRecordDataProperty(nameof(SimpleModel<TKey>.Text), typeof(string))
                {
                    IsFilterable = true,
                    StoragePropertyName = "te]xt" // intentionally with a character that requires escaping for Sql Server
                }
            ]
        };
}
