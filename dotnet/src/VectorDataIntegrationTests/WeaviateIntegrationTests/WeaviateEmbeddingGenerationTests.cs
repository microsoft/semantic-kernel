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

public class WeaviateEmbeddingGenerationTests(WeaviateEmbeddingGenerationTests.Fixture fixture)
    : EmbeddingGenerationTests<Guid>(fixture), IClassFixture<WeaviateEmbeddingGenerationTests.Fixture>
{
    public new class Fixture : EmbeddingGenerationTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;

        public override IVectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
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
