// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests;

public class WeaviateEmbeddingGenerationTests(WeaviateEmbeddingGenerationTests.StringVectorFixture fixture, WeaviateEmbeddingGenerationTests.RomOfFloatVectorFixture romOfFloatVectorFixture)
    : EmbeddingGenerationTests<Guid>(fixture, romOfFloatVectorFixture), IClassFixture<WeaviateEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<WeaviateEmbeddingGenerationTests.RomOfFloatVectorFixture>
{
    public new class StringVectorFixture : EmbeddingGenerationTests<Guid>.StringVectorFixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => WeaviateTestStore.NamedVectorsInstance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(WeaviateTestStore.NamedVectorsInstance.Client)
                .AddWeaviateVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(WeaviateTestStore.NamedVectorsInstance.Client)
                .AddWeaviateCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class RomOfFloatVectorFixture : EmbeddingGenerationTests<Guid>.RomOfFloatVectorFixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => WeaviateTestStore.NamedVectorsInstance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(WeaviateTestStore.NamedVectorsInstance.Client)
                .AddWeaviateVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(WeaviateTestStore.NamedVectorsInstance.Client)
                .AddWeaviateCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
