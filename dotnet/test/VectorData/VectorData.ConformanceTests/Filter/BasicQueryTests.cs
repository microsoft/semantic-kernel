// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;

namespace VectorDataSpecificationTests.Filter;

public abstract class BasicQueryTests<TKey>(BasicQueryTests<TKey>.QueryFixture fixture)
    : BasicFilterTests<TKey>(fixture) where TKey : notnull
{
    protected override async Task<List<FilterRecord>> GetRecords(Expression<Func<FilterRecord, bool>> filter, int top, ReadOnlyMemory<float> vector)
        => (await fixture.Collection.GetAsync(filter, top).ToListAsync()).OrderBy(r => r.Key).ToList();

    protected override async Task<List<Dictionary<string, object?>>> GetDynamicRecords(Expression<Func<Dictionary<string, object?>, bool>> dynamicFilter, int top, ReadOnlyMemory<float> vector)
        => (await fixture.DynamicCollection.GetAsync(dynamicFilter, top).ToListAsync()).OrderBy(r => r[nameof(FilterRecord.Key)]!).ToList();

    [Obsolete("Not used by derived types")]
    public sealed override Task Legacy_And() => Task.CompletedTask;

    [Obsolete("Not used by derived types")]
    public sealed override Task Legacy_equality() => Task.CompletedTask;

    [Obsolete("Not used by derived types")]
    public sealed override Task Legacy_AnyTagEqualTo_array() => Task.CompletedTask;

    [Obsolete("Not used by derived types")]
    public sealed override Task Legacy_AnyTagEqualTo_List() => Task.CompletedTask;

    public abstract class QueryFixture : BasicFilterTests<TKey>.Fixture
    {
        private static readonly Random s_random = new();

        public override string CollectionName => "QueryTests";

        /// <summary>
        /// Use random vectors to make sure that the values don't matter for GetAsync.
        /// </summary>
        protected override ReadOnlyMemory<float> GetVector(int count)
#pragma warning disable CA5394 // Do not use insecure randomness
            => new(Enumerable.Range(0, count).Select(_ => (float)s_random.NextDouble()).ToArray());
#pragma warning restore CA5394 // Do not use insecure randomness
    }
}
