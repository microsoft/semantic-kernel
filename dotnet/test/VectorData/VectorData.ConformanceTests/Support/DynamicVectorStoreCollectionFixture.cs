// Copyright (c) Microsoft. All rights reserved.

namespace VectorData.ConformanceTests.Support;

public abstract class DynamicVectorStoreCollectionFixture<TKey> : VectorStoreCollectionFixtureBase<object, Dictionary<string, object?>>
    where TKey : notnull
{
    protected abstract string KeyPropertyName { get; }

    public virtual async Task ReseedAsync()
    {
        // TODO: Use filtering delete, https://github.com/microsoft/semantic-kernel/issues/11830

        const int BatchSize = 100;

        List<TKey> keys = [];
        do
        {
            await foreach (var record in this.Collection.GetAsync(r => true, top: BatchSize))
            {
                // TODO: We don't use batching delete because of https://github.com/microsoft/semantic-kernel/issues/13303
                await this.Collection.DeleteAsync((TKey)record[this.KeyPropertyName]!);
            }
        } while (keys.Count == BatchSize);

        await this.SeedAsync();
    }
}
