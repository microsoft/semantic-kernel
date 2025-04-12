// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using SqliteIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace SqliteIntegrationTests;

public class SqliteEmbeddingGenerationTests(SqliteEmbeddingGenerationTests.Fixture fixture)
    : EmbeddingGenerationTests<string>(fixture), IClassFixture<SqliteEmbeddingGenerationTests.Fixture>
{
    public new class Fixture : EmbeddingGenerationTests<string>.Fixture
    {
        public override TestStore TestStore => SqliteTestStore.Instance;

        public override IVectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => SqliteTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services.AddSqliteVectorStore(SqliteTestStore.Instance.ConnectionString)
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services.AddSqliteVectorStoreRecordCollection<string, RecordWithAttributes>(this.CollectionName, SqliteTestStore.Instance.ConnectionString)
        ];
    }
}
