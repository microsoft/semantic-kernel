// Copyright (c) Microsoft. All rights reserved.

namespace VectorData.ConformanceTests.Support;

public abstract class VectorStoreCollectionFixture<TKey, TRecord> : VectorStoreCollectionFixtureBase<TKey, TRecord>
    where TKey : notnull
    where TRecord : TestRecord<TKey>
{
    public virtual async Task ReseedAsync()
    {
        // TODO: Use filtering delete, https://github.com/microsoft/semantic-kernel/issues/11830

        const int BatchSize = 100;

        TKey[] keys;
        do
        {
            keys = await this.Collection.GetAsync(r => true, top: BatchSize).Select(r => r.Key).ToArrayAsync();
            await this.Collection.DeleteAsync(keys);
        } while (keys.Length == BatchSize);

        await this.SeedAsync();
    }
}
