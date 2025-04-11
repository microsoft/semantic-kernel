// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory;

/// <summary>
/// Base class for <see cref="IVectorStore"/> integration tests.
/// </summary>
public abstract class BaseVectorStoreTests<TKey, TRecord>(IVectorStore vectorStore)
    where TKey : notnull
    where TRecord : notnull
{
    protected virtual IEnumerable<string> CollectionNames => ["listcollectionnames1", "listcollectionnames2", "listcollectionnames3"];

    [VectorStoreFact]
    public virtual async Task ItCanGetAListOfExistingCollectionNamesAsync()
    {
        // Arrange
        var expectedCollectionNames = this.CollectionNames;

        foreach (var collectionName in expectedCollectionNames)
        {
            var collection = vectorStore.GetCollection<TKey, TRecord>(collectionName);

            await collection.CreateCollectionIfNotExistsAsync();
        }

        // Act
        var actualCollectionNames = await vectorStore.ListCollectionNamesAsync().ToListAsync();

        // Assert
        var expected = expectedCollectionNames.Select(l => l.ToUpperInvariant()).ToList();
        var actual = actualCollectionNames.Select(l => l.ToUpperInvariant()).ToList();

        expected.ForEach(item => Assert.Contains(item, actual));

        // Cleanup
        foreach (var collectionName in expectedCollectionNames)
        {
            var collection = vectorStore.GetCollection<TKey, TRecord>(collectionName);

            await collection.DeleteCollectionAsync();
        }
    }
}
