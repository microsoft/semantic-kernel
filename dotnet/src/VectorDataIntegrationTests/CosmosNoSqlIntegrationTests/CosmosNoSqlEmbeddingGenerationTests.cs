// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSqlIntegrationTests.Support;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace CosmosNoSqlIntegrationTests;

public class CosmosNoSQLEmbeddingGenerationTests(CosmosNoSQLEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, CosmosNoSQLEmbeddingGenerationTests.NativeVectorFixture nativeVectorFixture)
    : EmbeddingGenerationTests<string>(stringVectorFixture, nativeVectorFixture), IClassFixture<CosmosNoSQLEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<CosmosNoSQLEmbeddingGenerationTests.NativeVectorFixture>
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
                .AddCosmosNoSqlVectorStoreRecordCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class NativeVectorFixture : EmbeddingGenerationTests<string>.NativeVectorFixture
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
                .AddCosmosNoSqlVectorStoreRecordCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
