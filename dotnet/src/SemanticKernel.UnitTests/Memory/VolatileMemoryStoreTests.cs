// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Memory.Storage;
using Xunit;

namespace SemanticKernel.UnitTests.Memory;

public class VolatileMemoryStoreTests
{
    private readonly VolatileMemoryStore<double> _db;

    public VolatileMemoryStoreTests()
    {
        this._db = new();
    }

    [Fact]
    public void InitializeDbConnectionSucceeds()
    {
        // Assert
        Assert.NotNull(this._db);
    }

#pragma warning disable CA5394 // Random is an insecure random number generator
    [Fact]
    public async Task PutAndRetrieveNoTimestampSucceedsAsync()
    {
        // Arrange
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        var embedding = new Embedding<double>(new double[] { 1, 1, 1 });
        var memory = new DoubleEmbeddingWithBasicMetadata(embedding, "1 1 1");

        // Act
        var key = await this._db.PutValueAsync(collection, memory);
        var actual = await this._db.GetValueAsync(collection, key);

        // Assert
        Assert.NotNull(actual);
        Assert.NotNull(key);
        Assert.Equal(memory, actual);
    }

    [Fact]
    public async Task PutAndRetrieveWithTimestampSucceedsAsync()
    {
        // Arrange
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        var embedding = new Embedding<double>(new double[] { 1, 2, 3 });
        var memory = new DoubleEmbeddingWithBasicMetadata(embedding, "1 2 3");
        DateTimeOffset timestamp = DateTimeOffset.UtcNow;

        // Act
        var key = await this._db.PutValueAsync(collection, memory, timestamp);
        var actual = await this._db.GetAsync(collection, key);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(memory, actual!.Value.Value);
        Assert.True(timestamp.Date.Equals(actual!.Value.Timestamp?.Date));
        Assert.True((int)timestamp.TimeOfDay.TotalSeconds == (int?)actual!.Value.Timestamp?.TimeOfDay.TotalSeconds);
    }

    [Fact]
    public async Task PutAndRetrieveDataEntryWithTimestampSucceedsAsync()
    {
        // Arrange
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        var embedding = new Embedding<double>(new double[] { 3, 2, 1 });
        var memory = new DoubleEmbeddingWithBasicMetadata(embedding, "3 2 1");
        DateTimeOffset timestamp = DateTimeOffset.UtcNow;
        var data = new DataEntry<IEmbeddingWithMetadata<double>>(null, memory, timestamp);

        // Act
        var key = await this._db.PutAsync(collection, data);
        DataEntry<IEmbeddingWithMetadata<double>>? actual = await this._db.GetAsync(collection, key);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(memory, actual!.Value.Value);
        Assert.True(timestamp.Date.Equals(actual!.Value.Timestamp?.Date));
        Assert.True((int)timestamp.TimeOfDay.TotalSeconds == (int?)actual!.Value.Timestamp?.TimeOfDay.TotalSeconds);
    }

    [Fact]
    public async Task PutAndDeleteDataEntrySucceedsAsync()
    {
        // Arrange
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        var embedding = new Embedding<double>(new double[] { -1, -1, -1 });
        var memory = new DoubleEmbeddingWithBasicMetadata(embedding, "-1 -1 -1");
        var data = new DataEntry<IEmbeddingWithMetadata<double>>(null, memory);

        // Act
        var key = await this._db.PutAsync(collection, data);
        await this._db.RemoveAsync(collection, key);

        // Assert
        Assert.Null(await this._db.GetAsync(collection, key));
    }

#pragma warning disable CA1851 // Possible multiple enumerations of 'IEnumerable' collection
    [Fact]
    public async Task ListAllDatabaseCollectionsSucceedsAsync()
    {
        // Arrange
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        var embedding = new Embedding<double>(new double[] { 0, 0, 0 });
        var memory = new DoubleEmbeddingWithBasicMetadata(embedding, "0 0 0");

        // Act
        var key = await this._db.PutValueAsync(collection, memory);
        var collections = this._db.GetCollectionsAsync().ToEnumerable();

        // Assert
        Assert.NotNull(collections);
        Assert.True(collections.Any(), "Collections is empty");
        Assert.True(collections.Contains(collection), "Collections do not contain the newly-created collection");
    }

    [Fact]
    public async Task GetAllSucceedsAsync()
    {
        // Arrange
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        var embedding = new Embedding<double>(new double[] { 0, 0, 0 });
        var memory = new DoubleEmbeddingWithBasicMetadata(embedding, "0 0 0");

        IList<string> keys = new List<string>();

        // Act
        for (int i = 0; i < 15; i++)
        {
            keys.Add(await this._db.PutValueAsync(collection, memory));
        }

        var getAllResults = this._db.GetAllAsync(collection).ToEnumerable();

        // Assert
        Assert.NotEmpty(keys);
        Assert.True(keys.Any(), "keys are empty");
        Assert.True(keys.Count() == 15, "keys should have 15 entries");
        Assert.NotNull(getAllResults);
        Assert.True(getAllResults.Any(), "Collections are empty");
        Assert.True(getAllResults.Count() == 15, "Collections should have 15 entries");
    }

    [Fact]
    public async Task GetNearestAsyncReturnsExpectedNoMinScoreAsync()
    {
        // Arrange
        var compareEmbedding = new Embedding<double>(new double[] { 1, 1, 1 });
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        int topN = 4;
        
        var memory = new DoubleEmbeddingWithBasicMetadata(new Embedding<double>(new double[] { 1, 1, 1 }), "1 ,1 ,1");
        _ = await this._db.PutValueAsync(collection, memory);
        
        memory = new DoubleEmbeddingWithBasicMetadata(new Embedding<double>(new double[] { -1, -1, -1 }), "-1 ,-1 ,-1");
        await this._db.PutValueAsync(collection, memory);
        
        memory = new DoubleEmbeddingWithBasicMetadata(new Embedding<double>(new double[] { 1, 2, 3 }), "1 ,2 ,3");
        _ = await this._db.PutValueAsync(collection, memory);
        
        memory = new DoubleEmbeddingWithBasicMetadata(new Embedding<double>(new double[] { -1, -2, -3 }), "-1 ,-2 ,-3");
        _ = await this._db.PutValueAsync(collection, memory);
        
        memory = new DoubleEmbeddingWithBasicMetadata(new Embedding<double>(new double[] { 1, -1, 2 }), "1 ,-1 ,2");
        _ = await this._db.PutValueAsync(collection, memory);

        // Act
        var topNResults = this._db.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: -1).ToEnumerable().ToArray();

        // Assert
        Assert.Equal(topN, topNResults.Length);
        for (int i = 0; i < topN - 1; i++)
        {
            int compare = topNResults[i].Item2.CompareTo(topNResults[i + 1].Item2);
            Assert.True(compare >= 0);
        }
    }

    [Fact]
    public async Task GetNearestAsyncReturnsExpectedWithMinScoreAsync()
    {
        // Arrange
        var compareEmbedding = new Embedding<double>(new double[] { 1, 1, 1 });
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        int topN = 4;
        
        var memory = new DoubleEmbeddingWithBasicMetadata(new Embedding<double>(new double[] { 1, 1, 1 }), "1 ,1 ,1");
        _ = await this._db.PutValueAsync(collection, memory);
        
        memory = new DoubleEmbeddingWithBasicMetadata(new Embedding<double>(new double[] { -1, -1, -1 }), "-1 ,-1 ,-1");
        _ = await this._db.PutValueAsync(collection, memory);
        
        memory = new DoubleEmbeddingWithBasicMetadata(new Embedding<double>(new double[] { 1, 2, 3 }), "1 ,2 ,3");
        _ = await this._db.PutValueAsync(collection, memory);
        
        memory = new DoubleEmbeddingWithBasicMetadata(new Embedding<double>(new double[] { -1, -2, -3 }), "-1 ,-2 ,-3");
        _ = await this._db.PutValueAsync(collection, memory);
        
        memory = new DoubleEmbeddingWithBasicMetadata(new Embedding<double>(new double[] { 1, -1, 2 }), "1 ,-1 ,2");
        _ = await this._db.PutValueAsync(collection, memory);

        // Act
        var topNResults = this._db.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: 0.75).ToEnumerable().ToArray();

        // Assert
        for (int i = 0; i < topNResults.Length; i++)
        {
            int compare = topNResults[i].Item2.CompareTo(0.75);
            Assert.True(compare >= 0);
        }
    }

    [Fact]
    public async Task GetNearestAsyncDifferentiatesIdenticalVectorsByKeyAsync()
    {
        // Arrange
        var compareEmbedding = new Embedding<double>(new double[] { 1, 1, 1 });
        int rand = Random.Shared.Next();
        string collection = "collection" + rand;
        int topN = 4;
        
        var memory = new DoubleEmbeddingWithBasicMetadata(new Embedding<double>(new double[] { 1, 1, 1 }), "1 ,2 ,3");
        _ = await this._db.PutValueAsync(collection, memory);

        for (int i = 0; i < 10; i++)
        {
            memory = new DoubleEmbeddingWithBasicMetadata(compareEmbedding, "1 ,1 ,1");
            _ = await this._db.PutValueAsync(collection, memory);
        }

        // Act
        var topNResults = this._db.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: 0.75).ToEnumerable().ToArray();

        // Assert
        Assert.Equal(topN, topNResults.Length);

        for (int i = 0; i < topNResults.Length; i++)
        {
            int compare = topNResults[i].Item2.CompareTo(0.75);
            Assert.True(compare >= 0);
        }
    }

    internal class DoubleEmbeddingWithBasicMetadata : IEmbeddingWithMetadata<double>
    {
        public Embedding<double> Embedding { get; }

        public string Metadata { get; }

        public DoubleEmbeddingWithBasicMetadata(Embedding<double> embedding, string metadata)
        {
            this.Embedding = embedding;
            this.Metadata = metadata;
        }
    }
}
