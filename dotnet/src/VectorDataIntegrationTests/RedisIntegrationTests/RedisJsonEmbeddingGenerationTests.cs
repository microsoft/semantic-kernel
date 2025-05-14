// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using RedisIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace RedisIntegrationTests;

public class RedisJsonEmbeddingGenerationTests(RedisJsonEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, RedisJsonEmbeddingGenerationTests.NativeVectorFixture nativeVectorFixture)
    : EmbeddingGenerationTests<string>(stringVectorFixture, nativeVectorFixture), IClassFixture<RedisJsonEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<RedisJsonEmbeddingGenerationTests.NativeVectorFixture>
{
    public new class StringVectorFixture : EmbeddingGenerationTests<string>.StringVectorFixture
    {
        public override TestStore TestStore => RedisTestStore.JsonInstance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => RedisTestStore.JsonInstance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(RedisTestStore.JsonInstance.Database)
                .AddRedisVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(RedisTestStore.JsonInstance.Database)
                .AddRedisJsonVectorStoreRecordCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class NativeVectorFixture : EmbeddingGenerationTests<string>.NativeVectorFixture
    {
        public override TestStore TestStore => RedisTestStore.JsonInstance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => RedisTestStore.JsonInstance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(RedisTestStore.JsonInstance.Database)
                .AddRedisVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(RedisTestStore.JsonInstance.Database)
                .AddRedisJsonVectorStoreRecordCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
