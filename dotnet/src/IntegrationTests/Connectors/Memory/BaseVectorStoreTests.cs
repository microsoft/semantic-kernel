﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory;

/// <summary>
/// Base class for <see cref="IVectorStore"/> integration tests.
/// </summary>
public abstract class BaseVectorStoreTests<TKey, TRecord>(IVectorStore vectorStore)
    where TKey : notnull
{
    [Fact]
    public virtual async Task ItCanGetAListOfExistingCollectionNamesAsync()
    {
        // Arrange
        var expectedCollectionNames = new List<string> { "listcollectionnames1", "listcollectionnames2", "listcollectionnames3" };

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
