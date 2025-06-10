// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Redis.ConformanceTests;

public class RedisJsonEmbeddingGenerationTests(RedisJsonEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, RedisJsonEmbeddingGenerationTests.RomOfFloatVectorFixture romOfFloatVectorFixture)
    : EmbeddingGenerationTests<string>(stringVectorFixture, romOfFloatVectorFixture), IClassFixture<RedisJsonEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<RedisJsonEmbeddingGenerationTests.RomOfFloatVectorFixture>
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
                .AddRedisJsonCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class RomOfFloatVectorFixture : EmbeddingGenerationTests<string>.RomOfFloatVectorFixture
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
                .AddRedisJsonCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
