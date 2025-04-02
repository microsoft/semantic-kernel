// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Linq.Expressions;
using Microsoft.Extensions.VectorData;

namespace VectorDataSpecificationTests.Support;

#pragma warning disable CA1001 // Type owns disposable fields but is not disposable

public abstract class TestStore
{
    private readonly SemaphoreSlim _lock = new(1, 1);
    private int _referenceCount;

    public virtual string DefaultDistanceFunction => DistanceFunction.CosineSimilarity;
    public virtual string DefaultIndexKind => IndexKind.Flat;

    protected abstract Task StartAsync();

    protected virtual Task StopAsync()
        => Task.CompletedTask;

    public abstract IVectorStore DefaultVectorStore { get; }

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

    /// <summary>Loops until the expected number of records is visible in the given collection.</summary>
    /// <remarks>Some databases upsert asynchronously, meaning that our seed data may not be visible immediately to tests.</remarks>
    public virtual async Task WaitForDataAsync<TKey, TRecord>(
        IVectorStoreRecordCollection<TKey, TRecord> collection,
        int recordCount,
        Expression<Func<TRecord, bool>>? filter = null,
        int vectorSize = 3)
        where TKey : notnull
    {
        var vector = new float[vectorSize];
        for (var i = 0; i < vectorSize; i++)
        {
            vector[i] = 1.0f;
        }

        for (var i = 0; i < 20; i++)
        {
            var results = await collection.VectorizedSearchAsync(
                new ReadOnlyMemory<float>(vector),
                new()
                {
                    Top = recordCount,
                    // In some databases (Azure AI Search), the data shows up but the filtering index isn't yet updated,
                    // so filtered searches show empty results. Add a filter to the seed data check below.
                    Filter = filter
                });
            var count = await results.Results.CountAsync();
            if (count == recordCount)
            {
                return;
            }

            await Task.Delay(TimeSpan.FromMilliseconds(100));
        }

        throw new InvalidOperationException("Data did not appear in the collection within the expected time.");
    }
}
