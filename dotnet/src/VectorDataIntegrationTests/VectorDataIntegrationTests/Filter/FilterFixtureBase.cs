// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace VectorDataSpecificationTests.Filter;

public abstract class FilterFixtureBase<TKey> : IAsyncLifetime
    where TKey : notnull
{
    private int _nextKeyValue = 1;
    private List<FilterRecord<TKey>>? _testData;

    protected virtual string StoreName => "FilterTests";

    protected abstract TestStore TestStore { get; }

    protected virtual string DistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineSimilarity;
    protected virtual string IndexKind => Microsoft.Extensions.VectorData.IndexKind.Flat;

    public virtual async Task InitializeAsync()
    {
        await this.TestStore.ReferenceCountingStartAsync();

        this.Collection = this.TestStore.DefaultVectorStore.GetCollection<TKey, FilterRecord<TKey>>(this.StoreName, this.GetRecordDefinition());

        if (await this.Collection.CollectionExistsAsync())
        {
            await this.Collection.DeleteCollectionAsync();
        }

        await this.Collection.CreateCollectionAsync();
        await this.SeedAsync();

        // Some databases upsert asynchronously, meaning that our seed data may not be visible immediately to tests.
        // Check and loop until it is.
        for (var i = 0; i < 20; i++)
        {
            var results = await this.Collection.VectorizedSearchAsync(
                new ReadOnlyMemory<float>([1, 2, 3]),
                new()
                {
                    Top = this.TestData.Count,
                    NewFilter = r => r.Int > 0
                });
            var count = await results.Results.CountAsync();
            if (count == this.TestData.Count)
            {
                break;
            }

            await Task.Delay(TimeSpan.FromMilliseconds(100));
        }
    }

    protected virtual VectorStoreRecordDefinition GetRecordDefinition()
        => new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(FilterRecord<TKey>.Key), typeof(TKey)),
                new VectorStoreRecordVectorProperty(nameof(FilterRecord<TKey>.Vector), typeof(ReadOnlyMemory<float>?))
                {
                    Dimensions = 3,
                    DistanceFunction = this.DistanceFunction,
                    IndexKind = this.IndexKind
                },

                new VectorStoreRecordDataProperty(nameof(FilterRecord<TKey>.Int), typeof(int)) { IsFilterable = true },
                new VectorStoreRecordDataProperty(nameof(FilterRecord<TKey>.String), typeof(string)) { IsFilterable = true },
                new VectorStoreRecordDataProperty(nameof(FilterRecord<TKey>.Bool), typeof(bool)) { IsFilterable = true },
                new VectorStoreRecordDataProperty(nameof(FilterRecord<TKey>.Int2), typeof(int)) { IsFilterable = true },
                new VectorStoreRecordDataProperty(nameof(FilterRecord<TKey>.StringArray), typeof(string[])) { IsFilterable = true },
                new VectorStoreRecordDataProperty(nameof(FilterRecord<TKey>.StringList), typeof(List<string>)) { IsFilterable = true }
            ]
        };

    public virtual IVectorStoreRecordCollection<TKey, FilterRecord<TKey>> Collection { get; private set; } = null!;

    public List<FilterRecord<TKey>> TestData => this._testData ??= this.BuildTestData();

    protected virtual List<FilterRecord<TKey>> BuildTestData()
    {
        // All records have the same vector - this fixture is about testing criteria filtering only
        var vector = new ReadOnlyMemory<float>([1, 2, 3]);

        return
        [
            new()
            {
                Key = this.GenerateNextKey(),
                Int = 8,
                String = "foo",
                Bool = true,
                Int2 = 80,
                StringArray = ["x", "y"],
                StringList = ["x", "y"],
                Vector = vector
            },
            new()
            {
                Key = this.GenerateNextKey(),
                Int = 9,
                String = "bar",
                Bool = false,
                Int2 = 90,
                StringArray = ["a", "b"],
                StringList = ["a", "b"],
                Vector = vector
            },
            new()
            {
                Key = this.GenerateNextKey(),
                Int = 9,
                String = "foo",
                Bool = true,
                Int2 = 9,
                StringArray = ["x"],
                StringList = ["x"],
                Vector = vector
            },
            new()
            {
                Key = this.GenerateNextKey(),
                Int = 10,
                String = null,
                Bool = false,
                Int2 = 100,
                StringArray = ["x", "y", "z"],
                StringList = ["x", "y", "z"],
                Vector = vector
            },
            new()
            {
                Key = this.GenerateNextKey(),
                Int = 11,
                Bool = true,
                String = """with some special"characters'and\stuff""",
                Int2 = 101,
                StringArray = ["y", "z"],
                StringList = ["y", "z"],
                Vector = vector
            }
        ];
    }

    protected virtual async Task SeedAsync()
    {
        // TODO: UpsertBatchAsync returns IAsyncEnumerable<TKey> (to support server-generated keys?), but this makes it quite hard to use:
        await foreach (var _ in this.Collection.UpsertBatchAsync(this.TestData))
        {
        }
    }

    protected virtual TKey GenerateNextKey()
        => typeof(TKey) switch
        {
            _ when typeof(TKey) == typeof(int) => (TKey)(object)this._nextKeyValue++,
            _ when typeof(TKey) == typeof(long) => (TKey)(object)(long)this._nextKeyValue++,
            _ when typeof(TKey) == typeof(ulong) => (TKey)(object)(ulong)this._nextKeyValue++,
            _ when typeof(TKey) == typeof(string) => (TKey)(object)(this._nextKeyValue++).ToString(CultureInfo.InvariantCulture),
            _ when typeof(TKey) == typeof(Guid) => (TKey)(object)new Guid($"00000000-0000-0000-0000-00{this._nextKeyValue++:0000000000}"),

            _ => throw new NotSupportedException($"Unsupported key of type '{typeof(TKey).Name}', override {nameof(this.GenerateNextKey)}")
        };

    public virtual Task DisposeAsync()
        => this.TestStore.ReferenceCountingStopAsync();
}

#pragma warning disable CS1819 // Properties should not return arrays
#pragma warning disable CA1819 // Properties should not return arrays
public class FilterRecord<TKey>
{
    public TKey Key { get; init; } = default!;
    public ReadOnlyMemory<float>? Vector { get; set; }

    public int Int { get; set; }
    public string? String { get; set; }
    public bool Bool { get; set; }
    public int Int2 { get; set; }
    public string[] StringArray { get; set; } = null!;
    public List<string> StringList { get; set; } = null!;
}
#pragma warning restore CA1819 // Properties should not return arrays
#pragma warning restore CS1819
