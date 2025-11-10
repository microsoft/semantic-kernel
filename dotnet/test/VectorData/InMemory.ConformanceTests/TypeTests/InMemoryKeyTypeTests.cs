// Copyright (c) Microsoft. All rights reserved.

using InMemory.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace InMemory.ConformanceTests.TypeTests;

public class InMemoryKeyTypeTests(InMemoryKeyTypeTests.Fixture fixture)
    : KeyTypeTests(fixture), IClassFixture<InMemoryKeyTypeTests.Fixture>
{
    // The InMemory provider supports all .NET types as keys; below are just a few basic tests.

    [ConditionalFact]
    public virtual Task Int() => this.Test<int>(8, 9);

    [ConditionalFact]
    public virtual Task Long() => this.Test<long>(8L, 9L);

    [ConditionalFact]
    public virtual Task String() => this.Test<string>("foo", "bar");

    protected override async Task Test<TKey>(TKey keyValue, TKey differentKey)
    {
        await base.Test(keyValue, differentKey);

        // For InMemory, delete the collection, otherwise the next test that runs will fail because the collection
        // already exists but with the previous key type.
        using var collection = fixture.CreateCollection<TKey>();
        await collection.EnsureCollectionDeletedAsync();
    }

    public new class Fixture : KeyTypeTests.Fixture
    {
        public override TestStore TestStore => InMemoryTestStore.Instance;
    }
}
