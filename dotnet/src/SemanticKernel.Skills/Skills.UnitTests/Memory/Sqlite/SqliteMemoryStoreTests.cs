// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Memory.Storage;
using Microsoft.SemanticKernel.Skills.Memory.Sqlite;
using Xunit;

namespace SemanticKernel.Skills.UnitTests.Memory.Sqlite;

/// <summary>
/// Unit tests of <see cref="SqliteDataStore{TValue}"/>.
/// </summary>
public class SqliteDataStoreTests : IDisposable
{
    private const string DatabaseFile = "SqliteDataStoreTests.db";
    private SqliteDataStore<string>? _db = null;
    private bool _disposedValue;

    public SqliteDataStoreTests()
    {
        File.Delete(DatabaseFile);
    }

    [Fact]
    public async Task InitializeDbConnectionSucceedsAsync()
    {
        this._db ??= await SqliteDataStore<string>.ConnectAsync(DatabaseFile);
        // Assert
        Assert.NotNull(this._db);
    }

    [Fact]
    public async Task PutAndRetrieveNoTimestampSucceedsAsync()
    {
        // Arrange
        int rand = RandomNumberGenerator.GetInt32(int.MaxValue);
        string collection = "collection" + rand;
        string key = "key" + rand;
        string value = "value" + rand;

        // Act
        this._db ??= await SqliteDataStore<string>.ConnectAsync(DatabaseFile);
        await this._db.PutValueAsync(collection, key, value);

        string? actual = await this._db.GetValueAsync(collection, key);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(value, actual);
    }

    [Fact]
    public async Task PutAndRetrieveWithTimestampSucceedsAsync()
    {
        // Arrange
        int rand = RandomNumberGenerator.GetInt32(int.MaxValue);
        string collection = "collection" + rand;
        string key = "key" + rand;
        string value = "value" + rand;
        DateTimeOffset timestamp = DateTimeOffset.UtcNow;

        // Act
        this._db ??= await SqliteDataStore<string>.ConnectAsync(DatabaseFile);
        await this._db.PutValueAsync(collection, key, value, timestamp);
        DataEntry<string>? actual = await this._db.GetAsync(collection, key);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(value, actual!.Value.Value);
        Assert.True(timestamp.Date.Equals(actual!.Value.Timestamp?.Date));
        Assert.True((int)timestamp.TimeOfDay.TotalSeconds == (int?)actual!.Value.Timestamp?.TimeOfDay.TotalSeconds);
    }

    [Fact]
    public async Task PutAndRetrieveDataEntryWithTimestampSucceedsAsync()
    {
        // Arrange
        int rand = RandomNumberGenerator.GetInt32(int.MaxValue);
        string collection = "collection" + rand;
        string key = "key" + rand;
        string value = "value" + rand;
        DateTimeOffset timestamp = DateTimeOffset.UtcNow;
        var data = DataEntry.Create(key, value, timestamp);

        // Act
        this._db ??= await SqliteDataStore<string>.ConnectAsync(DatabaseFile);
        await this._db.PutAsync(collection, data);
        DataEntry<string>? actual = await this._db.GetAsync(collection, key);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(value, actual!.Value.Value);
        Assert.True(timestamp.Date.Equals(actual!.Value.Timestamp?.Date));
        Assert.True((int)timestamp.TimeOfDay.TotalSeconds == (int?)actual!.Value.Timestamp?.TimeOfDay.TotalSeconds);
    }

    [Fact]
    public async Task PutAndDeleteDataEntrySucceedsAsync()
    {
        // Arrange
        int rand = RandomNumberGenerator.GetInt32(int.MaxValue);
        string collection = "collection" + rand;
        string key = "key" + rand;
        string value = "value" + rand;
        var data = DataEntry.Create(key, value, DateTimeOffset.UtcNow);

        // Act
        this._db ??= await SqliteDataStore<string>.ConnectAsync(DatabaseFile);
        await this._db.PutAsync(collection, data);
        await this._db.RemoveAsync(collection, key);

        // Assert
        var retrieved = await this._db.GetAsync(collection, key);
        Assert.Null(retrieved);
    }

    [Fact]
    public async Task ListAllDatabaseCollectionsSucceedsAsync()
    {
        // Arrange
        int rand = RandomNumberGenerator.GetInt32(int.MaxValue);
        string collection = "collection" + rand;
        string key = "key" + rand;
        string value = "value" + rand;

        // Act
        this._db ??= await SqliteDataStore<string>.ConnectAsync(DatabaseFile);
        await this._db.PutValueAsync(collection, key, value);
        var collections = this._db.GetCollectionsAsync();

        // Assert
        Assert.NotNull(collections);
        Assert.True(await collections.AnyAsync(), "Collections is empty");
        Assert.True(await collections.ContainsAsync(collection), "Collections do not contain the newly-created collection");
    }

    [Fact]
    public async Task GetAllSucceedsAsync()
    {
        // Arrange
        int rand = RandomNumberGenerator.GetInt32(int.MaxValue);
        string collection = "collection" + rand;
        string key = "key" + rand;
        string value = "value" + rand;
        int quantity = 15;

        // Act
        this._db ??= await SqliteDataStore<string>.ConnectAsync(DatabaseFile);
        for (int i = 0; i < quantity; i++)
        {
            await this._db.PutValueAsync(collection, key + i, value);
        }

        var getAllResults = this._db.GetAllAsync(collection);

        // Assert
        Assert.NotNull(getAllResults);
        Assert.True(await getAllResults.AnyAsync(), "Collections is empty");
        Assert.True(await getAllResults.CountAsync() == quantity, "Collections should have 15 entries");
    }

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            if (disposing)
            {
                this._db?.Dispose();
                File.Delete(DatabaseFile);
            }

            this._disposedValue = true;
        }
    }

    public void Dispose()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }
}
