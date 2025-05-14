// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests;

public class WeaviateEmbeddingGenerationTests(WeaviateEmbeddingGenerationTests.StringVectorFixture fixture, WeaviateEmbeddingGenerationTests.NativeVectorFixture nativeVectorFixture)
    : EmbeddingGenerationTests<Guid>(fixture, nativeVectorFixture), IClassFixture<WeaviateEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<WeaviateEmbeddingGenerationTests.NativeVectorFixture>
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
                .AddWeaviateVectorStoreRecordCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class NativeVectorFixture : EmbeddingGenerationTests<Guid>.NativeVectorFixture
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
                .AddWeaviateVectorStoreRecordCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
