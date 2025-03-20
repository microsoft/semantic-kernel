// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class VectorizedSearchBuilderExtensionsTests
{
    [Fact]
    public void AsBuilderReturnsVectorizedSearchBuilder()
    {
        // Arrange
        var search = new Mock<IVectorizedSearch<string>>().Object;

        // Act
        var builder = search.AsBuilder();

        // Assert
        Assert.IsType<VectorizedSearchBuilder<string>>(builder);
        Assert.Same(search, builder.Build());
    }
}
