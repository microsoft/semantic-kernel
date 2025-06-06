// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace CosmosNoSql.ConformanceTests;

public class CosmosNoSQLEmbeddingGenerationTests(CosmosNoSQLEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, CosmosNoSQLEmbeddingGenerationTests.RomOfFloatVectorFixture romOfFloatVectorFixture)
    : EmbeddingGenerationTests<string>(stringVectorFixture, romOfFloatVectorFixture), IClassFixture<CosmosNoSQLEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<CosmosNoSQLEmbeddingGenerationTests.RomOfFloatVectorFixture>
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
                .AddCosmosNoSqlCollection<RecordWithAttributes>(this.CollectionName)
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
                .AddCosmosNoSqlCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
