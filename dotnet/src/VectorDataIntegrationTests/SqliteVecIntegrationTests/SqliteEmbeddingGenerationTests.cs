// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using SqliteVecIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace SqliteVecIntegrationTests;

public class SqliteEmbeddingGenerationTests(SqliteEmbeddingGenerationTests.Fixture fixture)
    : EmbeddingGenerationTests<string>(fixture), IClassFixture<SqliteEmbeddingGenerationTests.Fixture>
{
    public new class Fixture : EmbeddingGenerationTests<string>.Fixture
    {
        public override TestStore TestStore => SqliteTestStore.Instance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => SqliteTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services.AddSqliteVectorStore(_ => SqliteTestStore.Instance.ConnectionString)
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services.AddSqliteCollection<string, RecordWithAttributes>(this.CollectionName, SqliteTestStore.Instance.ConnectionString),
            services => services.AddSqliteCollection<string, RecordWithAttributes>(this.CollectionName, _ => SqliteTestStore.Instance.ConnectionString)
        ];
    }
}
