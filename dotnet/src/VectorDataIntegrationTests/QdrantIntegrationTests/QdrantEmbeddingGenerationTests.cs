// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace QdrantIntegrationTests;

public class QdrantEmbeddingGenerationTests(QdrantEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, QdrantEmbeddingGenerationTests.NativeVectorFixture nativeVectorFixture)
    : EmbeddingGenerationTests<Guid>(stringVectorFixture, nativeVectorFixture), IClassFixture<QdrantEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<QdrantEmbeddingGenerationTests.NativeVectorFixture>
{
    public new class StringVectorFixture : EmbeddingGenerationTests<Guid>.StringVectorFixture
    {
        public override TestStore TestStore => QdrantTestStore.UnnamedVectorInstance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => QdrantTestStore.UnnamedVectorInstance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(QdrantTestStore.UnnamedVectorInstance.Client)
                .AddQdrantVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(QdrantTestStore.UnnamedVectorInstance.Client)
                .AddQdrantVectorStoreRecordCollection<Guid, RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class NativeVectorFixture : EmbeddingGenerationTests<Guid>.NativeVectorFixture
    {
        public override TestStore TestStore => QdrantTestStore.UnnamedVectorInstance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => QdrantTestStore.UnnamedVectorInstance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(QdrantTestStore.UnnamedVectorInstance.Client)
                .AddQdrantVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(QdrantTestStore.UnnamedVectorInstance.Client)
                .AddQdrantVectorStoreRecordCollection<Guid, RecordWithAttributes>(this.CollectionName)
        ];
    }
}
