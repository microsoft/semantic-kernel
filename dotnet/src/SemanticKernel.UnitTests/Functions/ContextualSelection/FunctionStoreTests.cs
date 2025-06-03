// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Functions;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public sealed class FunctionStoreTests
{
    private readonly Mock<VectorStore> _vectorStoreMock;
    private readonly Mock<VectorStoreCollection<object, Dictionary<string, object?>>> _collectionMock;

    public FunctionStoreTests()
    {
        this._vectorStoreMock = new Mock<VectorStore>(MockBehavior.Strict);
        this._collectionMock = new Mock<VectorStoreCollection<object, Dictionary<string, object?>>>(MockBehavior.Strict);

        this._vectorStoreMock
            .Setup(vs => vs.GetDynamicCollection(It.IsAny<string>(), It.IsAny<VectorStoreCollectionDefinition>()))
            .Returns(this._collectionMock.Object);

        this._collectionMock
            .Setup(c => c.CollectionExistsAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        this._collectionMock
            .Setup(c => c.EnsureCollectionExistsAsync(It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        this._collectionMock
            .Setup(c => c.UpsertAsync(It.IsAny<IEnumerable<Dictionary<string, object?>>>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        this._collectionMock
            .Setup(c => c.SearchAsync(It.IsAny<string>(), It.IsAny<int>(), null, It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<VectorSearchResult<Dictionary<string, object?>>>());
    }

    [Fact]
    public void ConstructorShouldThrowOnNullArguments()
    {
        var functions = new List<AIFunction> { CreateFunction("f1") };

        Assert.Throws<ArgumentNullException>(() => new FunctionStore(null!, "col", 1, functions, 3));
        Assert.Throws<ArgumentException>(() => new FunctionStore(this._vectorStoreMock.Object, "", 1, functions, 3));
        Assert.Throws<ArgumentException>(() => new FunctionStore(this._vectorStoreMock.Object, "col", 0, functions, 3));
        Assert.Throws<ArgumentNullException>(() => new FunctionStore(this._vectorStoreMock.Object, "col", 1, null!, 3));
    }

    [Fact]
    public async Task SaveAsyncShouldUpsertsFunctions()
    {
        // Arrange
        var functions = new List<AIFunction>
        {
            CreateFunction("f1", "desc1"),
            CreateFunction("f2", "desc2")
        };

        this._collectionMock.Setup(c => c.UpsertAsync(It.IsAny<IEnumerable<Dictionary<string, object?>>>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask)
            .Verifiable();

        var store = new FunctionStore(this._vectorStoreMock.Object, "col", 3, functions, 3);

        // Act
        await store.SaveAsync();

        // Assert
        this._collectionMock.Verify(c => c.EnsureCollectionExistsAsync(It.IsAny<CancellationToken>()), Times.Once);
        this._collectionMock.Verify(c => c.UpsertAsync(It.Is<IEnumerable<Dictionary<string, object?>>>(records =>
            records.Count() == 2 &&
            records.Any(r => (r["Name"] as string) == "f1") &&
            records.Any(r => (r["Name"] as string) == "f2")
        ), It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task SearchAsyncShouldReturnMatchingFunctions()
    {
        // Arrange
        var functions = new List<AIFunction>
        {
            CreateFunction("f1", "desc1"),
            CreateFunction("f2", "desc2"),
            CreateFunction("f3", "desc3")
        };

        var searchResults = new List<VectorSearchResult<Dictionary<string, object?>>>
        {
            new(new Dictionary<string, object?> { ["Name"] = "f3" }, 0.3),
            new(new Dictionary<string, object?> { ["Name"] = "f2" }, 0.2),
            new(new Dictionary<string, object?> { ["Name"] = "f1" }, 0.1)
        };

        this._collectionMock.Setup(c => c.SearchAsync(It.IsAny<string>(), It.IsAny<int>(), null, It.IsAny<CancellationToken>()))
            .Returns(searchResults.ToAsyncEnumerable());

        var store = new FunctionStore(this._vectorStoreMock.Object, "col", 3, functions, 3);

        // Act
        var result = await store.SearchAsync("desc3");

        // Assert
        var resultList = result.ToList();
        Assert.Equal(3, resultList.Count);
        Assert.Equal("f3", resultList[0].Name);
        Assert.Equal("f2", resultList[1].Name);
        Assert.Equal("f1", resultList[2].Name);
    }

    [Fact]
    public async Task SearchAsyncShouldThrowIfCollectionDoesNotExist()
    {
        // Arrange
        var functions = new List<AIFunction> { CreateFunction("f1") };

        this._collectionMock.Setup(c => c.CollectionExistsAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(false);

        var store = new FunctionStore(this._vectorStoreMock.Object, "col", 3, functions, 3);

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() => store.SearchAsync("query"));
    }

    private static AIFunction CreateFunction(string name, string description = "desc")
    {
        return AIFunctionFactory.Create(() => { }, name, description);
    }
}
