// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Linq.Expressions;
using Microsoft.Extensions.VectorData;

namespace VectorData.ConformanceTests.Support;

#pragma warning disable CA1001 // Type owns disposable fields but is not disposable

public abstract class TestStore
{
    private readonly SemaphoreSlim _lock = new(1, 1);
    private int _referenceCount;
    private VectorStore? _defaultVectorStore;

    /// <summary>
    /// Some databases modify vectors on upsert, e.g. normalizing them, so vectors
    /// returned cannot be compared with the original ones.
    /// </summary>
    public virtual bool VectorsComparable => true;

    /// <summary>
    /// Whether the database supports filtering by score threshold in vector search.
    /// </summary>
    public virtual bool SupportsScoreThreshold => true;

    public virtual string DefaultDistanceFunction => DistanceFunction.CosineSimilarity;
    public virtual string DefaultIndexKind => IndexKind.Flat;

    protected abstract Task StartAsync();

    protected virtual Task StopAsync()
        => Task.CompletedTask;

    public VectorStore DefaultVectorStore
    {
        get => this._defaultVectorStore ?? throw new InvalidOperationException("Not initialized");
        set => this._defaultVectorStore = value;
    }

    public virtual async Task ReferenceCountingStartAsync()
    {
        await this._lock.WaitAsync();
        try
        {
            if (this._referenceCount++ == 0)
            {
                await this.StartAsync();
            }
        }
        finally
        {
            this._lock.Release();
        }
    }

    public virtual async Task ReferenceCountingStopAsync()
    {
        await this._lock.WaitAsync();
        try
        {
            if (--this._referenceCount == 0)
            {
                await this.StopAsync();
                this._defaultVectorStore?.Dispose();
            }
        }
        finally
        {
            this._lock.Release();
        }
    }

    public virtual TKey GenerateKey<TKey>(int value)
        => typeof(TKey) switch
        {
            _ when typeof(TKey) == typeof(int) => (TKey)(object)value,
            _ when typeof(TKey) == typeof(long) => (TKey)(object)(long)value,
            _ when typeof(TKey) == typeof(ulong) => (TKey)(object)(ulong)value,
            _ when typeof(TKey) == typeof(string) => (TKey)(object)value.ToString(CultureInfo.InvariantCulture),
            _ when typeof(TKey) == typeof(Guid) => (TKey)(object)new Guid($"00000000-0000-0000-0000-00{value:0000000000}"),

            _ => throw new NotSupportedException($"Unsupported key of type '{typeof(TKey).Name}', override {nameof(TestStore)}.{nameof(this.GenerateKey)}")
        };

    /// <summary>
    /// Applies any provider-specific rules to collection names (e.g. all-lowercase).
    /// </summary>
    /// <param name="baseName"></param>
    /// <returns></returns>
    public virtual string AdjustCollectionName(string baseName)
        => baseName;

    /// <summary>
    /// Creates a collection for the given name and definition.
    /// Override this to provide provider-specific collection options (e.g., partition key configuration).
    /// </summary>
    public virtual VectorStoreCollection<TKey, TRecord> CreateCollection<TKey, TRecord>(
        string name,
        VectorStoreCollectionDefinition definition)
        where TKey : notnull
        where TRecord : class
        => this.DefaultVectorStore.GetCollection<TKey, TRecord>(name, definition);

    /// <summary>
    /// Creates a dynamic collection for the given name and definition.
    /// Override this to provide provider-specific collection options (e.g., partition key configuration).
    /// </summary>
    public virtual VectorStoreCollection<object, Dictionary<string, object?>> CreateDynamicCollection(
        string name,
        VectorStoreCollectionDefinition definition)
        => this.DefaultVectorStore.GetDynamicCollection(name, definition);

    /// <summary>Loops until the expected number of records is visible in the given collection.</summary>
    /// <remarks>Some databases upsert asynchronously, meaning that our seed data may not be visible immediately to tests.</remarks>
    public virtual async Task WaitForDataAsync<TKey, TRecord>(
        VectorStoreCollection<TKey, TRecord> collection,
        int recordCount,
        Expression<Func<TRecord, bool>>? filter = null,
        Expression<Func<TRecord, object?>>? vectorProperty = null,
        int? vectorSize = null,
        object? dummyVector = null)
        where TKey : notnull
        where TRecord : class
    {
        if (vectorSize is not null && dummyVector is not null)
        {
            throw new ArgumentException("vectorSize or dummyVector can't both be set");
        }

        var vector = dummyVector ?? new ReadOnlyMemory<float>(Enumerable.Range(0, vectorSize ?? 3).Select(i => (float)i).ToArray());

        for (var i = 0; i < 200; i++)
        {
            // Note that we very intentionally use SearchAsync and not filtering GetAsync, as we want to wait until the data is visible
            // specifically via vector search (some databases may show data via filtering before they are indexed for vector search).
            var results = collection.SearchAsync(
                vector,
                top: recordCount is 0 ? 1 : recordCount,
                new()
                {
                    Filter = filter,
                    VectorProperty = vectorProperty
                });
            var count = await results.CountAsync();
            if (count == recordCount)
            {
                return;
            }

            await Task.Delay(TimeSpan.FromMilliseconds(100));
        }

        throw new InvalidOperationException("Data did not appear in the collection within the expected time.");
    }
}
