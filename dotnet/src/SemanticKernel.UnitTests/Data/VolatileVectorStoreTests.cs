// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

/// <summary>
/// Contains tests for the <see cref="VolatileVectorStore"/> class.
/// </summary>
[Obsolete("The VolatileVectorStore is obsolete so these tests are as well.")]
public class VolatileVectorStoreTests
{
    private const string TestCollectionName = "testcollection";

    [Fact]
    public void GetCollectionReturnsCollection()
    {
        // Arrange.
        var sut = new VolatileVectorStore();

        // Act.
        var actual = sut.GetCollection<string, SinglePropsModel<string>>(TestCollectionName);

        // Assert.
        Assert.NotNull(actual);
        Assert.IsType<VolatileVectorStoreRecordCollection<string, SinglePropsModel<string>>>(actual);
    }

    [Fact]
    public void GetCollectionReturnsCollectionWithNonStringKey()
    {
        // Arrange.
        var sut = new VolatileVectorStore();

        // Act.
        var actual = sut.GetCollection<int, SinglePropsModel<int>>(TestCollectionName);

        // Assert.
        Assert.NotNull(actual);
        Assert.IsType<VolatileVectorStoreRecordCollection<int, SinglePropsModel<int>>>(actual);
    }

    [Fact]
    public async Task ListCollectionNamesReadsDictionaryAsync()
    {
        // Arrange.
        var collectionStore = new ConcurrentDictionary<string, ConcurrentDictionary<object, object>>();
        collectionStore.TryAdd("collection1", new ConcurrentDictionary<object, object>());
        collectionStore.TryAdd("collection2", new ConcurrentDictionary<object, object>());
        var sut = new VolatileVectorStore(collectionStore);

        // Act.
        var collectionNames = sut.ListCollectionNamesAsync();

        // Assert.
        var collectionNamesList = await collectionNames.ToListAsync();
        Assert.Equal(new[] { "collection1", "collection2" }, collectionNamesList);
    }

<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    public sealed class SinglePropsModel<TKey>
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    public sealed class SinglePropsModel<TKey>
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    public sealed class SinglePropsModel<TKey>
=======
>>>>>>> Stashed changes
=======
    public sealed class SinglePropsModel<TKey>
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
=======
>>>>>>> upstream/main
    [Fact]
    public async Task GetCollectionDoesNotAllowADifferentDataTypeThanPreviouslyUsedAsync()
    {
        // Arrange.
        var sut = new VolatileVectorStore();
        var stringKeyCollection = sut.GetCollection<string, SinglePropsModel<string>>(TestCollectionName);
        await stringKeyCollection.CreateCollectionAsync();

        // Act and assert.
        var exception = Assert.Throws<InvalidOperationException>(() => sut.GetCollection<string, SecondModel>(TestCollectionName));
        Assert.Equal($"Collection '{TestCollectionName}' already exists and with data type 'SinglePropsModel`1' so cannot be re-created with data type 'SecondModel'.", exception.Message);
    }

#pragma warning disable CA1812 // Classes are used as generic arguments
    private sealed class SinglePropsModel<TKey>
<<<<<<< main
=======
    public sealed class SinglePropsModel<TKey>
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
    {
        [VectorStoreRecordKey]
        public required TKey Key { get; set; }

        [VectorStoreRecordData]
        public string Data { get; set; } = string.Empty;

        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string? NotAnnotated { get; set; }
    }
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
=======
>>>>>>> upstream/main

    private sealed class SecondModel
    {
        [VectorStoreRecordKey]
        public required int Key { get; set; }

        [VectorStoreRecordData]
        public string Data { get; set; } = string.Empty;
    }
#pragma warning restore CA1812
<<<<<<< main
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
}
