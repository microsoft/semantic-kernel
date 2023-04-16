// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.IO.IsolatedStorage;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Sqlite;
using Microsoft.SemanticKernel.Memory;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Memory;
public abstract class MemoryStorageTestBase
{
    //private int _collectionID = 0;
    protected virtual string CreateRandomCollectionName()
    {
        return $"Collection_{Guid.NewGuid()}";
    }

    protected abstract Task WithStorageAsync(Func<IMemoryStore, Task> factAsync);
    

    [Fact]
    public virtual Task ItCanCreateAndGetCollectionAsync()
    {
        
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            string collection = this.CreateRandomCollectionName();

            // Act
            await db.CreateCollectionAsync(collection);
            var collections = db.GetCollectionsAsync();

            // Assert
            Assert.NotEmpty(collections.ToEnumerable());
            Assert.True(await collections.ContainsAsync(collection));
        });
        
    }

    [Fact]
    public virtual Task ItCanCheckIfCollectionExistsAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            string collection = this.CreateRandomCollectionName();

            // Act
            await db.CreateCollectionAsync(collection);

            // Assert
            Assert.True(await db.DoesCollectionExistAsync(collection));
            Assert.False(await db.DoesCollectionExistAsync(this.CreateRandomCollectionName()));
        });
        
    }
}
