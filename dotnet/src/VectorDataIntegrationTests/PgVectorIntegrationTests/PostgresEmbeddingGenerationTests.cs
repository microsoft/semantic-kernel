﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Npgsql;
using PgVectorIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace PgVectorIntegrationTests;

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
                .AddPostgresVectorStoreRecordCollection<int, RecordWithAttributes>(this.CollectionName)
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
            services => services
                .AddTransient<NpgsqlDataSource>(_ =>
                {
                    NpgsqlDataSourceBuilder builder = new(PostgresTestStore.Instance.ConnectionString);
                    builder.UseVector();
                    return builder.Build();
                })
                .AddPostgresVectorStore(lifetime: ServiceLifetime.Transient),
            services => services
                .AddPostgresVectorStore(PostgresTestStore.Instance.ConnectionString),
            services => services
                .AddPostgresVectorStore(_ => PostgresTestStore.Instance.ConnectionString),
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(PostgresTestStore.Instance.DataSource)
                .AddPostgresCollection<int, RecordWithAttributes>(this.CollectionName),
            services => services
                .AddTransient<NpgsqlDataSource>(_ =>
                {
                    NpgsqlDataSourceBuilder builder = new(PostgresTestStore.Instance.ConnectionString);
                    builder.UseVector();
                    return builder.Build();
                })
                .AddPostgresCollection<int, RecordWithAttributes>(this.CollectionName, lifetime: ServiceLifetime.Transient),
            services => services
                .AddPostgresCollection<int, RecordWithAttributes>(this.CollectionName, PostgresTestStore.Instance.ConnectionString),
            services => services
                .AddPostgresCollection<int, RecordWithAttributes>(this.CollectionName, _ => PostgresTestStore.Instance.ConnectionString)
        ];
    }
}
