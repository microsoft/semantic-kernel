﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace Redis.ConformanceTests.TypeTests;

public class RedisJsonKeyTypeTests(RedisJsonKeyTypeTests.Fixture fixture)
    : KeyTypeTests(fixture), IClassFixture<RedisJsonKeyTypeTests.Fixture>
{
    [ConditionalFact]
    public virtual Task String() => this.Test<string>("foo");

    public new class Fixture : KeyTypeTests.Fixture
    {
        private int _collectionCounter;

        public override TestStore TestStore => RedisTestStore.JsonInstance;

        // Redis doesn't seem to reliably delete the collection: when running multiple tests that delete and recreate the collection with different key types,
        // we seem to get key values from the previous collection despite having deleted and recreated it. So we uniquify the collection name instead.
        public override VectorStoreCollection<TKey, Record<TKey>> CreateCollection<TKey>()
            => this.TestStore.DefaultVectorStore.GetCollection<TKey, Record<TKey>>(this.CollectionName + (++this._collectionCounter), this.CreateRecordDefinition<TKey>());
    }
}
