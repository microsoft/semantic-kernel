// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class VectorStoreRecordCollectionBuilderExtensionsTests
{
    [Fact]
    public void AsBuilderReturnsVectorStoreRecordCollectionBuilder()
    {
        // Arrange
        var collection = new Mock<IVectorStoreRecordCollection<string, object>>().Object;

        // Act
        var builder = collection.AsBuilder();

        // Assert
        Assert.IsType<VectorStoreRecordCollectionBuilder<string, object>>(builder);
        Assert.Same(collection, builder.Build());
    }
}
