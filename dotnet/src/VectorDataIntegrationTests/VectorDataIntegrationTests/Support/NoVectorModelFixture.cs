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

    protected override async Task WaitForDataAsync()
    {
        for (var i = 0; i < 20; i++)
        {
            var results = await this.Collection.GetAsync([this.TestData[0].Id, this.TestData[1].Id, this.TestData[2].Id, this.TestData[3].Id]).ToArrayAsync();
            if (results.Length == 4 && results.All(r => r != null))
            {
                return;
            }

            await Task.Delay(TimeSpan.FromMilliseconds(100));
        }

        throw new InvalidOperationException("Data did not appear in the collection within the expected time.");
    }
}
