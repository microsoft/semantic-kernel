// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests.VectorStorage;

public class DelegatingVectorStoreTests
{
    private readonly Mock<IVectorStore> _mockInnerStore;
    private readonly FakeVectorStore _delegatingStore;

    public DelegatingVectorStoreTests()
    {
        this._mockInnerStore = new Mock<IVectorStore>();
        this._delegatingStore = new FakeVectorStore(this._mockInnerStore.Object);
    }

    [Fact]
    public void ConstructorWithNullInnerStoreThrowsArgumentNullException()
    {
        Assert.Throws<ArgumentNullException>(() => new FakeVectorStore(null!));
    }

    [Fact]
    public void GetCollectionCallsInnerStore()
    {
        var collectionName = "test-collection";
        var recordDefinition = new VectorStoreRecordDefinition();
        var mockCollection = new Mock<IVectorStoreRecordCollection<string, object>>().Object;

        this._mockInnerStore.Setup(s => s.GetCollection<string, object>(collectionName, recordDefinition))
            .Returns(mockCollection);

        var result = this._delegatingStore.GetCollection<string, object>(collectionName, recordDefinition);

        Assert.Equal(mockCollection, result);
        this._mockInnerStore.Verify(x => x.GetCollection<string, object>(collectionName, recordDefinition), Times.Once);
    }

    [Fact]
    public async Task ListCollectionNamesCallsInnerStoreAsync()
    {
        var collectionNames = new[] { "collection1", "collection2" };

        this._mockInnerStore.Setup(s => s.ListCollectionNamesAsync(default))
            .Returns(collectionNames.ToAsyncEnumerable());

        var result = await this._delegatingStore.ListCollectionNamesAsync().ToListAsync();

        Assert.Equal(collectionNames, result);
        this._mockInnerStore.Verify(x => x.ListCollectionNamesAsync(default), Times.Once);
    }

    private sealed class FakeVectorStore : DelegatingVectorStore
    {
        public FakeVectorStore(IVectorStore innerStore) : base(innerStore) { }
    }
}
