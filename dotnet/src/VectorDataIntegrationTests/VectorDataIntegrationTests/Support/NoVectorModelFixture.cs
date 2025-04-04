// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Models;

namespace VectorDataSpecificationTests.Support;

/// <summary>
/// Provides data and configuration for a model without a vector, which is supported by some connectors.
/// </summary>
public abstract class NoVectorModelFixture<TKey> : VectorStoreCollectionFixture<TKey, NoVectorModel<TKey>>
    where TKey : notnull
{
    protected override List<NoVectorModel<TKey>> BuildTestData() =>
    [
        new()
        {
            Id = this.GenerateNextKey<TKey>(),
            Text = "UsedByGetTests",
        },
        new()
        {
            Id = this.GenerateNextKey<TKey>(),
            Text = "UsedByUpdateTests",
        },
        new()
        {
            Id = this.GenerateNextKey<TKey>(),
            Text = "UsedByDeleteTests",
        },
        new()
        {
            Id = this.GenerateNextKey<TKey>(),
            Text = "UsedByDeleteBatchTests",
        }
    ];

    protected override VectorStoreRecordDefinition GetRecordDefinition()
        => new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(NoVectorModel<TKey>.Id), typeof(TKey)),
                new VectorStoreRecordDataProperty(nameof(NoVectorModel<TKey>.Text), typeof(string)) { IsFilterable = true },
            ]
        };

    protected override Task WaitForDataAsync()
    {
        // Don't do anything, since vector search is not suported with this model.
        return Task.CompletedTask;
    }
}
