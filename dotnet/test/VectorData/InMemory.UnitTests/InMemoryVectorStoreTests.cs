// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;
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
        using var sut = new InMemoryVectorStore();

        // Act.
        var actual = sut.GetCollection<string, SinglePropsModel<string>>(TestCollectionName);

        // Assert.
        Assert.NotNull(actual);
        Assert.IsType<InMemoryCollection<string, SinglePropsModel<string>>>(actual);
    }

    [Fact]
    public void GetCollectionReturnsCollectionWithNonStringKey()
    {
        // Arrange.
        using var sut = new InMemoryVectorStore();

        // Act.
        var actual = sut.GetCollection<int, SinglePropsModel<int>>(TestCollectionName);

        // Assert.
        Assert.NotNull(actual);
        Assert.IsType<InMemoryCollection<int, SinglePropsModel<int>>>(actual);
    }

    [Fact]
    public void InMemoryModelBuilderExposesKeyTypeValidationCompatibilityMethod()
    {
        // Arrange.
        var method = typeof(InMemoryModelBuilder).GetMethod(
            "IsKeyPropertyTypeValid",
            BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.DeclaredOnly);
        var sut = new InMemoryModelBuilder();
        var args = new object?[] { typeof(string), null };

        // Act.
        var isSupported = (bool?)method?.Invoke(sut, args);

        // Assert.
        Assert.NotNull(method);
        Assert.True(isSupported);
        Assert.Null(args[1]);
    }

    [Fact]
    public async Task GetCollectionDoesNotAllowADifferentDataTypeThanPreviouslyUsedAsync()
    {
        // Arrange.
        using var sut = new InMemoryVectorStore();
        var stringKeyCollection = sut.GetCollection<string, SinglePropsModel<string>>(TestCollectionName);
        await stringKeyCollection.EnsureCollectionExistsAsync();

        // Act and assert.
        var exception = Assert.Throws<InvalidOperationException>(() => sut.GetCollection<string, SecondModel>(TestCollectionName));
        Assert.Equal($"Collection '{TestCollectionName}' already exists and with data type 'SinglePropsModel`1' so cannot be re-created with data type 'SecondModel'.", exception.Message);
    }

#pragma warning disable CA1812 // Classes are used as generic arguments
    private sealed class SinglePropsModel<TKey>
    {
        [VectorStoreKey]
        public required TKey Key { get; set; }

        [VectorStoreData]
        public string Data { get; set; } = string.Empty;

        [VectorStoreVector(4)]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string? NotAnnotated { get; set; }
    }

    private sealed class SecondModel
    {
        [VectorStoreKey]
        public required int Key { get; set; }

        [VectorStoreData]
        public string Data { get; set; } = string.Empty;
    }
#pragma warning restore CA1812
}
