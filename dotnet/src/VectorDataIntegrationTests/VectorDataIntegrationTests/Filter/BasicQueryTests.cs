// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;

namespace VectorDataSpecificationTests.Filter;

public abstract class BasicQueryTests<TKey>(BasicQueryTests<TKey>.QueryFixture fixture)
    : BasicFilterTests<TKey>(fixture) where TKey : notnull
{
    // Not all of the connectors allow to sort by the Key, so we sort by the Int.
    protected override List<FilterRecord> GetOrderedRecords(IQueryable<FilterRecord> filtered)
        => filtered.OrderBy(r => r.Int).ToList();

    protected override async Task<List<FilterRecord>> GetResults(Expression<Func<FilterRecord, bool>> filter, int top)
        => (await fixture.Collection.QueryAsync(new() { Filter = filter, Top = top, OrderBy = r => r.Int }).ToListAsync());

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

        protected override string CollectionName => "QueryTests";

        /// <summary>
        /// In contrary to the filter tests, the query uses random vectors,
        /// just to make sure that the values don't matter for QueryAsync.
        /// </summary>
        protected override ReadOnlyMemory<float> GetVector(int count)
#pragma warning disable CA5394 // Do not use insecure randomness
            => new(Enumerable.Range(0, count).Select(_ => (float)s_random.NextDouble()).ToArray());
#pragma warning restore CA5394 // Do not use insecure randomness
    }
}
