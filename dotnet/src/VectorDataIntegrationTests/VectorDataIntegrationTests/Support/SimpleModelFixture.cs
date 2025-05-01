// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Models;

namespace VectorDataSpecificationTests.Support;

public abstract class SimpleModelFixture<TKey> : VectorStoreCollectionFixture<TKey, SimpleRecord<TKey>>
    where TKey : notnull
{
    protected override List<SimpleRecord<TKey>> BuildTestData() =>
    [
        new()
        {
            Id = this.GenerateNextKey<TKey>(),
            Number = 1,
            Text = "UsedByGetTests",
            Floats = Enumerable.Repeat(0.1f, SimpleRecord<TKey>.DimensionCount).ToArray()
        },
        new()
        {
            Id = this.GenerateNextKey<TKey>(),
            Number = 2,
            Text = "UsedByUpdateTests",
            Floats = Enumerable.Repeat(0.2f, SimpleRecord<TKey>.DimensionCount).ToArray()
        },
        new()
        {
            Id = this.GenerateNextKey<TKey>(),
            Number = 3,
            Text = "UsedByDeleteTests",
            Floats = Enumerable.Repeat(0.3f, SimpleRecord<TKey>.DimensionCount).ToArray()
        },
        new()
        {
            Id = this.GenerateNextKey<TKey>(),
            Number = 4,
            Text = "UsedByDeleteBatchTests",
            Floats = Enumerable.Repeat(0.4f, SimpleRecord<TKey>.DimensionCount).ToArray()
        }
    ];

    public override VectorStoreRecordDefinition GetRecordDefinition()
        => new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(SimpleRecord<TKey>.Id), typeof(TKey)),
                new VectorStoreRecordVectorProperty(nameof(SimpleRecord<TKey>.Floats), typeof(ReadOnlyMemory<float>?), SimpleRecord<TKey>.DimensionCount)
                {
                    DistanceFunction = this.DistanceFunction,
                    IndexKind = this.IndexKind
                },

                new VectorStoreRecordDataProperty(nameof(SimpleRecord<TKey>.Number), typeof(int)) { IsIndexed = true },
                new VectorStoreRecordDataProperty(nameof(SimpleRecord<TKey>.Text), typeof(string)) { IsIndexed = true },
            ]
        };
}
