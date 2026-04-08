// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace CosmosNoSql.ConformanceTests;

public class CosmosNoSqlEmbeddingGenerationTests(CosmosNoSqlEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, CosmosNoSqlEmbeddingGenerationTests.RomOfFloatVectorFixture romOfFloatVectorFixture)
    : EmbeddingGenerationTests<string>(stringVectorFixture, romOfFloatVectorFixture), IClassFixture<CosmosNoSqlEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<CosmosNoSqlEmbeddingGenerationTests.RomOfFloatVectorFixture>
{
    public new class StringVectorFixture : EmbeddingGenerationTests<string>.StringVectorFixture
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
                .AddCosmosNoSqlCollection<string, RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class RomOfFloatVectorFixture : EmbeddingGenerationTests<string>.RomOfFloatVectorFixture
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
                .AddCosmosNoSqlCollection<string, RecordWithAttributes>(this.CollectionName)
        ];
    }
}
