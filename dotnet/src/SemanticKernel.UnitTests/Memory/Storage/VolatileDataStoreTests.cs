// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Memory.Storage;
using Xunit;

namespace SemanticKernel.UnitTests.Memory.Storage;

/// <summary>
/// Unit tests of <see cref="VolatileDataStore{TValue}"/>.
/// </summary>
public class VolatileDataStoreTests
{
    private readonly VolatileDataStore<string> _db;

    public VolatileDataStoreTests()
    {
        this._db = new();
    }

    [Fact]
    public void ItSucceedsInitialization()
    {
        // Assert
        Assert.NotNull(this._db);
    }

#pragma warning disable CA5394 // Random is an insecure random number generator
    [Fact]
    public async Task ItWillPutAndRetrieveNoTimestampAsync()
    {
        // Arrange
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        string key = "key" + rand;
        string value = "value" + rand;

        // Act
        await this._db.PutValueAsync(collection, key, value);

        var actual = await this._db.GetValueAsync(collection, key);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(value, actual);
    }

    [Fact]
    public async Task ItWillPutAndRetrieveWithTimestampAsync()
    {
        // Arrange
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        string key = "key" + rand;
        string value = "value" + rand;
        DateTimeOffset timestamp = DateTimeOffset.UtcNow;

        // Act
        await this._db.PutValueAsync(collection, key, value, timestamp);
        var actual = await this._db.GetAsync(collection, key);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(value, actual!.Value.Value);
        Assert.True(timestamp.Date.Equals(actual!.Value.Timestamp?.Date));
        Assert.True((int)timestamp.TimeOfDay.TotalSeconds == (int?)actual!.Value.Timestamp?.TimeOfDay.TotalSeconds);
    }

    [Fact]
    public async Task ItWillPutAndRetrieveDataEntryWithTimestampAsync()
    {
        // Arrange
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        string key = "key" + rand;
        string value = "value" + rand;
        DateTimeOffset timestamp = DateTimeOffset.UtcNow;
        var data = DataEntry.Create(key, value, timestamp);

        // Act
        var placed = await this._db.PutAsync(collection, data);
        DataEntry<string>? actual = await this._db.GetAsync(collection, key);

        // Assert
        Assert.NotNull(actual);
        Assert.True(placed.Equals(data));
        Assert.Equal(value, actual!.Value.Value);
        Assert.True(timestamp.Date.Equals(actual!.Value.Timestamp?.Date));
        Assert.True((int)timestamp.TimeOfDay.TotalSeconds == (int?)actual!.Value.Timestamp?.TimeOfDay.TotalSeconds);
    }

    [Fact]
    public async Task ItWillPutAndDeleteDataEntryAsync()
    {
        // Arrange
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        string key = "key" + rand;
        string value = "value" + rand;
        var data = DataEntry.Create(key, value, DateTimeOffset.UtcNow);

        // Act
        await this._db.PutAsync(collection, data);
        await this._db.RemoveAsync(collection, key);
        var attempt = await this._db.GetAsync(collection, key);

        // Assert
        Assert.Null(attempt);
    }

#pragma warning disable CA1851 // Possible multiple enumerations of 'IEnumerable' collection
    [Fact]
    public async Task ItWillListAllDatabaseCollectionsAsync()
    {
        // Arrange
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        string key = "key" + rand;
        string value = "value" + rand;

        // Act
        await this._db.PutValueAsync(collection, key, value);
        var collections = this._db.GetCollectionsAsync().ToEnumerable();

        // Assert
        Assert.NotNull(collections);
        Assert.True(collections.Any(), "Collections is empty");
        Assert.True(collections.Contains(collection), "Collections do not contain the newly-created collection");
    }

    [Fact]
    public async Task ItWillGetAllCollectionEntriesAsync()
    {
        // Arrange
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        string key = "key" + rand;
        string value = "value" + rand;

        // Act
        for (int i = 0; i < 15; i++)
        {
            await this._db.PutValueAsync(collection, key + i, value);
        }

        var getAllResults = this._db.GetAllAsync(collection).ToEnumerable();

        // Assert
        Assert.NotNull(getAllResults);
        Assert.True(getAllResults.Any(), "Collections collection empty");
        Assert.True(getAllResults.Count() == 15, "Collections collection should have 15 entries");
    }

    [Fact]
    public async Task ItWillRetrieveNothingIfKeyDoesNotExistAsync()
    {
        // Arrange
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        string key = "key";
        string value = "value";

        // Act
        await this._db.PutValueAsync(collection, key, value);
        var attempt = await this._db.GetAsync(collection, key + "1");

        // Assert
        Assert.Null(attempt);
    }

    [Fact]
    public async Task ItWillOverwriteExistingValueAsync()
    {
        // Arrange
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        string key = "key";
        string value1 = "value1";
        string value2 = "value2";

        // Act
        await this._db.PutValueAsync(collection, key, value1);
        await this._db.PutValueAsync(collection, key, value2);
        var actual = await this._db.GetAsync(collection, key);

        // Assert
        Assert.NotNull(actual);
        Assert.NotEqual(value1, actual!.Value.Value);
        Assert.Equal(value2, actual!.Value.Value);
    }
}
