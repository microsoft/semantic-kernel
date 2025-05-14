// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using PgVectorIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace PgVectorIntegrationTests;

public class PostgresEmbeddingGenerationTests(PostgresEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, PostgresEmbeddingGenerationTests.NativeVectorFixture nativeVectorFixture)
    : EmbeddingGenerationTests<int>(stringVectorFixture, nativeVectorFixture), IClassFixture<PostgresEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<PostgresEmbeddingGenerationTests.NativeVectorFixture>
{
    public new class StringVectorFixture : EmbeddingGenerationTests<int>.StringVectorFixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
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

    public new class NativeVectorFixture : EmbeddingGenerationTests<int>.NativeVectorFixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
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
