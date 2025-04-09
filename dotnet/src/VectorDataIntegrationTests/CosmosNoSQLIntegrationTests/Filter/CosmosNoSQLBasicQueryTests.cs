// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using CosmosNoSQLIntegrationTests.Support;
using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace CosmosNoSQLIntegrationTests.Filter;

public class CosmosNoSQLBasicQueryTests(CosmosNoSQLBasicQueryTests.Fixture fixture)
    : BasicQueryTests<string>(fixture), IClassFixture<CosmosNoSQLBasicQueryTests.Fixture>
{
    // CosmosDB supports ordering by multiple fields only when a composite index is created up-front:
    // https://learn.microsoft.com/en-us/azure/cosmos-db/index-policy#composite-indexes
    // The index requires the order to be also provided up front (ASC or DESC),
    // we don't expose API for such customization, so for now we just order by one field.
    protected override List<FilterRecord> GetOrderedRecords(IQueryable<FilterRecord> filtered)
        => filtered.OrderBy(r => r.Int2).ToList();

    protected override async Task<List<FilterRecord>> GetResults(IVectorStoreRecordCollection<string, FilterRecord> collection, Expression<Func<FilterRecord, bool>> filter, int top)
    {
        GetFilteredRecordOptions<FilterRecord> options = new();

        options.OrderBy.Ascending(r => r.Int2);

        return await collection.GetAsync(filter, top, options).ToListAsync();
    }

    public new class Fixture : BasicQueryTests<string>.QueryFixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }
}
