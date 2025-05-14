// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDBIntegrationTests.Support;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace CosmosMongoDBIntegrationTests;

public class CosmosMongoEmbeddingGenerationTests(CosmosMongoEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, CosmosMongoEmbeddingGenerationTests.NativeVectorFixture nativeVectorFixture)
    : EmbeddingGenerationTests<string>(stringVectorFixture, nativeVectorFixture), IClassFixture<CosmosMongoEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<CosmosMongoEmbeddingGenerationTests.NativeVectorFixture>
{
    public new class StringVectorFixture : EmbeddingGenerationTests<string>.StringVectorFixture
    {
        public override TestStore TestStore => CosmosMongoTestStore.Instance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => CosmosMongoTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(CosmosMongoTestStore.Instance.Database)
                .AddCosmosMongoVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(CosmosMongoTestStore.Instance.Database)
                .AddCosmosMongoVectorStoreRecordCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class NativeVectorFixture : EmbeddingGenerationTests<string>.NativeVectorFixture
    {
        public override TestStore TestStore => CosmosMongoTestStore.Instance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => CosmosMongoTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(CosmosMongoTestStore.Instance.Database)
                .AddCosmosMongoVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(CosmosMongoTestStore.Instance.Database)
                .AddCosmosMongoVectorStoreRecordCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
