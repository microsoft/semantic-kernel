// Copyright (c) Microsoft. All rights reserved.

using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

#pragma warning disable CA2000 // Dispose objects before losing scope

namespace SqlServerIntegrationTests;

public class SqlServerEmbeddingTypeTests(SqlServerEmbeddingTypeTests.Fixture fixture)
    : EmbeddingTypeTests<Guid>(fixture), IClassFixture<SqlServerEmbeddingTypeTests.Fixture>
{
    public new class Fixture : EmbeddingTypeTests<Guid>.Fixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;
    }
}
