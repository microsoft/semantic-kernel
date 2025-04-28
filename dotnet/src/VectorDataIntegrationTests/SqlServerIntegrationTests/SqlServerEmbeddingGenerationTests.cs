// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace SqlServerIntegrationTests;

public class SqlServerEmbeddingGenerationTests(SqlServerEmbeddingGenerationTests.Fixture fixture)
    : EmbeddingGenerationTests<int>(fixture), IClassFixture<SqlServerEmbeddingGenerationTests.Fixture>
{
    public new class Fixture : EmbeddingGenerationTests<int>.Fixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;

        public override IVectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => SqlServerTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            // TODO: Implement DI registration for SqlServer (https://github.com/microsoft/semantic-kernel/issues/10948)
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            // TODO: Implement DI registration for SqlServer (https://github.com/microsoft/semantic-kernel/issues/10948)
        ];
    }
}
