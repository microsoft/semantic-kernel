// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class KeywordHybridSearchBuilderExtensionsTests
{
    [Fact]
    public void AsBuilderReturnsKeywordHybridSearchBuilder()
    {
        // Arrange
        var search = new Mock<IKeywordHybridSearch<string>>().Object;

        // Act
        var builder = search.AsBuilder();

        // Assert
        Assert.IsType<KeywordHybridSearchBuilder<string>>(builder);
        Assert.Same(search, builder.Build());
    }
}
