// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using Qdrant.Client.Grpc;
using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace QdrantIntegrationTests.Filter;

public class QdrantBasicQueryTests(QdrantBasicQueryTests.Fixture fixture)
    : BasicQueryTests<ulong>(fixture), IClassFixture<QdrantBasicQueryTests.Fixture>
{
    protected override async Task<List<FilterRecord>> GetResults(Expression<Func<FilterRecord, bool>> filter, int top)
        // TODO adsitnik: find a way to create an index that supports ordering
        => (await fixture.Collection.QueryAsync(new() { Filter = filter, Top = top }).ToListAsync()).OrderBy(r => r.Key).ToList();

    public new class Fixture : BasicQueryTests<ulong>.QueryFixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;

        // Qdrant doesn't support the default Flat index kind
        protected override string IndexKind => Microsoft.Extensions.VectorData.IndexKind.Hnsw;

        protected override async Task CreateIndex()
        {
            await QdrantTestStore.NamedVectorsInstance.Client.CreatePayloadIndexAsync(
                this.CollectionName,
                fieldName: "id",
                PayloadSchemaType.Integer,
                ordering: WriteOrderingType.Strong);
        }
    }
}
