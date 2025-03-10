// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class VectorStoreBuilderExtensionsTests
{
    [Fact]
    public void AsBuilderReturnsVectorStoreBuilder()
    {
        // Arrange
        var store = new Mock<IVectorStore>().Object;

        // Act
        var builder = store.AsBuilder();

        // Assert
        Assert.IsType<VectorStoreBuilder>(builder);
        Assert.Same(store, builder.Build());
    }
}
