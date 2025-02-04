// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using Microsoft.Extensions.VectorData;
using Xunit;

namespace VectorDataSpecificationTests.Filter;

public abstract class FilterFixtureBase<TKey> : IAsyncLifetime
    where TKey : notnull
{
    private int _nextKeyValue = 1;
    private List<FilterRecord<TKey>>? _testData;

    public virtual async Task InitializeAsync()
    {
        var vectorStore = this.GetVectorStore();
        this.Collection = vectorStore.GetCollection<TKey, FilterRecord<TKey>>(this.StoreName, this.GetRecordDefinition());

        if (await this.Collection.CollectionExistsAsync())
        {
            await this.Collection.DeleteCollectionAsync();
        }

        await this.Collection.CreateCollectionAsync();
        await this.SeedAsync();
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
                new VectorStoreRecordDataProperty(nameof(FilterRecord<TKey>.Int2), typeof(int)) { IsFilterable = true },
                new VectorStoreRecordDataProperty(nameof(FilterRecord<TKey>.Strings), typeof(string[])) { IsFilterable = true },
            ]
        };

    protected virtual string DistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineSimilarity;
    protected virtual string IndexKind => Microsoft.Extensions.VectorData.IndexKind.Flat;

    public virtual IVectorStoreRecordCollection<TKey, FilterRecord<TKey>> Collection { get; private set; } = null!;

    protected abstract IVectorStore GetVectorStore();

    public List<FilterRecord<TKey>> TestData => this._testData ??= this.GetTestData();

    protected virtual List<FilterRecord<TKey>> GetTestData()
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
                Int2 = 80,
                Strings = ["x", "y"],
                Vector = vector
            },
            new()
            {
                Key = this.GenerateNextKey(),
                Int = 9,
                String = "bar",
                Int2 = 90,
                Strings = ["a", "b"],
                Vector = vector
            },
            new()
            {
                Key = this.GenerateNextKey(),
                Int = 9,
                String = "foo",
                Int2 = 9,
                Strings = ["x"],
                Vector = vector
            },
            new()
            {
                Key = this.GenerateNextKey(),
                Int = 10,
                String = null,
                Int2 = 100,
                Strings = ["x", "y", "z"],
                Vector = vector
            },
            new()
            {
                Key = this.GenerateNextKey(),
                Int = 11,
                String = """with some special"characters'and\stuff""",
                Int2 = 101,
                Strings = ["y", "z"],
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

    protected virtual string StoreName => "FilterTests";

    public virtual Task DisposeAsync() => Task.CompletedTask;
}

public class FilterRecord<TKey>
{
    public TKey Key { get; init; }
    public ReadOnlyMemory<float>? Vector { get; set; }

    public int Int { get; set; }
    public string? String { get; set; }
    public int Int2 { get; set; }
    public string[] Strings { get; set; }
}
