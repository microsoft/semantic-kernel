// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace PostgresIntegrationTests;

public class PostgresEmbeddingGenerationTests(PostgresEmbeddingGenerationTests.Fixture fixture)
    : EmbeddingGenerationTests<int>(fixture), IClassFixture<PostgresEmbeddingGenerationTests.Fixture>
{
    public new class Fixture : EmbeddingGenerationTests<int>.Fixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;

        public override IVectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => PostgresTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(PostgresTestStore.Instance.DataSource)
                .AddPostgresVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(PostgresTestStore.Instance.DataSource)
                .AddPostgresVectorStoreRecordCollection<int, RecordWithAttributes>(this.CollectionName)
        ];
    }
}
