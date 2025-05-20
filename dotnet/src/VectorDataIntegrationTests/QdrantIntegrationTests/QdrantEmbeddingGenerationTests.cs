// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace QdrantIntegrationTests;

public class QdrantEmbeddingGenerationTests(QdrantEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, QdrantEmbeddingGenerationTests.RomOfFloatVectorFixture romOfFloatVectorFixture)
    : EmbeddingGenerationTests<Guid>(stringVectorFixture, romOfFloatVectorFixture), IClassFixture<QdrantEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<QdrantEmbeddingGenerationTests.RomOfFloatVectorFixture>
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
                .AddQdrantCollection<Guid, RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class RomOfFloatVectorFixture : EmbeddingGenerationTests<Guid>.RomOfFloatVectorFixture
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
                .AddQdrantCollection<Guid, RecordWithAttributes>(this.CollectionName)
        ];
    }
}
