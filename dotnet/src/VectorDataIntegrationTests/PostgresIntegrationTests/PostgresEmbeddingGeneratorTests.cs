// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace PostgresIntegrationTests;

public class PostgresEmbeddingGeneratorTests(PostgresEmbeddingGeneratorTests.Fixture fixture)
    : EmbeddingGeneratorTests<int>(fixture), IClassFixture<PostgresEmbeddingGeneratorTests.Fixture>
{
    public new class Fixture : EmbeddingGeneratorTests<int>.Fixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;

        protected override IVectorStore CreateVectorStore(object? embeddingGenerator)
            => PostgresTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });
    }
}
