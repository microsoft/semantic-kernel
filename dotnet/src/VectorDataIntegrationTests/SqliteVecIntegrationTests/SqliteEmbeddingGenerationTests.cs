// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using SqliteVecIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace SqliteVecIntegrationTests;

public class SqliteEmbeddingGenerationTests(SqliteEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, SqliteEmbeddingGenerationTests.NativeVectorFixture nativeVectorFixture)
    : EmbeddingGenerationTests<string>(stringVectorFixture, nativeVectorFixture), IClassFixture<SqliteEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<SqliteEmbeddingGenerationTests.NativeVectorFixture>
{
    public new class StringVectorFixture : EmbeddingGenerationTests<string>.StringVectorFixture
    {
        public override TestStore TestStore => SqliteTestStore.Instance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
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

    public new class NativeVectorFixture : EmbeddingGenerationTests<string>.NativeVectorFixture
    {
        public override TestStore TestStore => SqliteTestStore.Instance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
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
