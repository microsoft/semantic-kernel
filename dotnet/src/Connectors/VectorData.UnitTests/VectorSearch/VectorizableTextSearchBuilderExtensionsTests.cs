// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class VectorizableTextSearchBuilderExtensionsTests
{
    [Fact]
    public void AsBuilderReturnsVectorizableTextSearchBuilder()
    {
        // Arrange
        var search = new Mock<IVectorizableTextSearch<string>>().Object;

        // Act
        var builder = search.AsBuilder();

        // Assert
        Assert.IsType<VectorizableTextSearchBuilder<string>>(builder);
        Assert.Same(search, builder.Build());
    }
}
