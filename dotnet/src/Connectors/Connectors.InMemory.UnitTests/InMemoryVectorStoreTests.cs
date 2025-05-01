// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Xunit;

namespace SemanticKernel.Connectors.InMemory.UnitTests;

/// <summary>
/// Contains tests for the <see cref="InMemoryVectorStore"/> class.
/// </summary>
public class InMemoryVectorStoreTests
{
    private const string TestCollectionName = "testcollection";

    [Fact]
    public void GetCollectionReturnsCollection()
    {
        // Arrange.
        var sut = new InMemoryVectorStore();

        // Act.
        var actual = sut.GetCollection<string, SinglePropsModel<string>>(TestCollectionName);

        // Assert.
        Assert.NotNull(actual);
        Assert.IsType<InMemoryVectorStoreRecordCollection<string, SinglePropsModel<string>>>(actual);
    }

    [Fact]
    public void GetCollectionReturnsCollectionWithNonStringKey()
    {
        // Arrange.
        var sut = new InMemoryVectorStore();

        // Act.
        var actual = sut.GetCollection<int, SinglePropsModel<int>>(TestCollectionName);

        // Assert.
        Assert.NotNull(actual);
        Assert.IsType<InMemoryVectorStoreRecordCollection<int, SinglePropsModel<int>>>(actual);
    }

    [Fact]
    public async Task GetCollectionDoesNotAllowADifferentDataTypeThanPreviouslyUsedAsync()
    {
        // Arrange.
        var sut = new InMemoryVectorStore();
        var stringKeyCollection = sut.GetCollection<string, SinglePropsModel<string>>(TestCollectionName);
        await stringKeyCollection.CreateCollectionAsync();

        // Act and assert.
        var exception = Assert.Throws<InvalidOperationException>(() => sut.GetCollection<string, SecondModel>(TestCollectionName));
        Assert.Equal($"Collection '{TestCollectionName}' already exists and with data type 'SinglePropsModel`1' so cannot be re-created with data type 'SecondModel'.", exception.Message);
    }

#pragma warning disable CA1812 // Classes are used as generic arguments
    private sealed class SinglePropsModel<TKey>
    {
        [VectorStoreRecordKey]
        public required TKey Key { get; set; }

        [VectorStoreRecordData]
        public string Data { get; set; } = string.Empty;

        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string? NotAnnotated { get; set; }
    }

    private sealed class SecondModel
    {
        [VectorStoreRecordKey]
        public required int Key { get; set; }

        [VectorStoreRecordData]
        public string Data { get; set; } = string.Empty;
    }
#pragma warning restore CA1812
}
