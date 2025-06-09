// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace PgVector.ConformanceTests;

public class PostgresEmbeddingGenerationTests(PostgresEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, PostgresEmbeddingGenerationTests.RomOfFloatVectorFixture romOfFloatVectorFixture)
    : EmbeddingGenerationTests<int>(stringVectorFixture, romOfFloatVectorFixture), IClassFixture<PostgresEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<PostgresEmbeddingGenerationTests.RomOfFloatVectorFixture>
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
                .AddPostgresCollection<int, RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class RomOfFloatVectorFixture : EmbeddingGenerationTests<int>.RomOfFloatVectorFixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => PostgresTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(PostgresTestStore.Instance.DataSource)
                .AddPostgresVectorStore(),
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(PostgresTestStore.Instance.DataSource)
                .AddPostgresCollection<int, RecordWithAttributes>(this.CollectionName),
        ];
    }
}
