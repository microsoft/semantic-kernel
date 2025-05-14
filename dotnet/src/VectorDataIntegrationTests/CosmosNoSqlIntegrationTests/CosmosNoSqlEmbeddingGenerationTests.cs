// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSqlIntegrationTests.Support;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace CosmosNoSqlIntegrationTests;

public class CosmosNoSQLEmbeddingGenerationTests(CosmosNoSQLEmbeddingGenerationTests.Fixture fixture)
    : EmbeddingGenerationTests<string>(fixture), IClassFixture<CosmosNoSQLEmbeddingGenerationTests.Fixture>
{
    public new class Fixture : EmbeddingGenerationTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => CosmosNoSqlTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(CosmosNoSqlTestStore.Instance.Database)
                .AddCosmosNoSqlVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(CosmosNoSqlTestStore.Instance.Database)
                .AddCosmosNoSqlCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
