// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using Microsoft.Extensions.VectorData;
using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace QdrantIntegrationTests.Filter;

public class QdrantBasicQueryTests(QdrantBasicQueryTests.Fixture fixture)
    : BasicQueryTests<ulong>(fixture), IClassFixture<QdrantBasicQueryTests.Fixture>
{
    // Qdrant does not support ordering by multiple fields, so we order by only one field.
    protected override List<FilterRecord> GetOrderedRecords(IQueryable<FilterRecord> filtered)
        => filtered.OrderBy(r => r.Int2).ToList();

    protected override async Task<List<FilterRecord>> GetResults(IVectorStoreRecordCollection<ulong, FilterRecord> collection, Expression<Func<FilterRecord, bool>> filter, int top)
    {
        GetFilteredRecordOptions<FilterRecord> options = new();

        options.OrderBy.Ascending(r => r.Int2);

        return await collection.GetAsync(filter, top, options).ToListAsync();
    }

    public new class Fixture : BasicQueryTests<ulong>.QueryFixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;

        // Qdrant doesn't support the default Flat index kind
        protected override string IndexKind => Microsoft.Extensions.VectorData.IndexKind.Hnsw;
    }
}
