// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace SqlServerIntegrationTests;

public class SqlServerEmbeddingGenerationTests(SqlServerEmbeddingGenerationTests.Fixture fixture)
    : EmbeddingGenerationTests<int>(fixture), IClassFixture<SqlServerEmbeddingGenerationTests.Fixture>
{
    public new class Fixture : EmbeddingGenerationTests<int>.Fixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => SqlServerTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services.AddSqlServerVectorStore(sp => SqlServerTestEnvironment.ConnectionString!)
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services.AddSqlServerCollection<int, RecordWithAttributes>(this.CollectionName, sp => SqlServerTestEnvironment.ConnectionString!),
            services => services.AddSqlServerCollection<int, RecordWithAttributes>(this.CollectionName, SqlServerTestEnvironment.ConnectionString!),
        ];
    }
}
