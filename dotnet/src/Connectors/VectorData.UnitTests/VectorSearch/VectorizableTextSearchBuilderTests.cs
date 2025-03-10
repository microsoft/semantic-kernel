// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class VectorizableTextSearchBuilderTests
{
    [Fact]
    public void ConstructorWithInstanceSetsInnerSearch()
    {
        // Arrange
        var innerSearch = new Mock<IVectorizableTextSearch<string>>().Object;

        // Act
        var builder = new VectorizableTextSearchBuilder<string>(innerSearch);

        // Assert
        var builtSearch = builder.Build();
        Assert.Same(innerSearch, builtSearch);
    }

    [Fact]
    public void ConstructorWithFactoryCallsFactoryOnBuild()
    {
        // Arrange
        var innerSearch = new Mock<IVectorizableTextSearch<string>>().Object;
        var serviceProvider = new Mock<IServiceProvider>();
        IVectorizableTextSearch<string> Factory(IServiceProvider _) => innerSearch;

        // Act
        var builder = new VectorizableTextSearchBuilder<string>(Factory);
        var builtSearch = builder.Build(serviceProvider.Object);

        // Assert
        Assert.Same(innerSearch, builtSearch);
    }

    [Fact]
    public void BuildWithMultipleFactoriesAppliesInReverseOrder()
    {
        // Arrange
        var innerSearch = new Mock<IVectorizableTextSearch<string>>().Object;
        var mockSearch1 = new Mock<IVectorizableTextSearch<string>>().Object;
        var mockSearch2 = new Mock<IVectorizableTextSearch<string>>().Object;
        var builder = new VectorizableTextSearchBuilder<string>(innerSearch);

        builder.Use(s => mockSearch1);
        builder.Use(s => mockSearch2);

        // Act
        var builtSearch = builder.Build();

        // Assert
        Assert.Same(mockSearch1, builtSearch);
    }

    [Fact]
    public void BuildWithNullReturningFactoryThrowsInvalidOperationException()
    {
        // Arrange
        var innerSearch = new Mock<IVectorizableTextSearch<string>>().Object;
        var builder = new VectorizableTextSearchBuilder<string>(innerSearch);
        builder.Use((s, _) => null!);

        // Act & Assert
        var exception = Assert.Throws<InvalidOperationException>(() => builder.Build());
        Assert.Contains("returned null", exception.Message);
    }

    [Fact]
    public void BuildWithNullServiceProviderUsesEmptyServiceProvider()
    {
        // Arrange
        var innerSearch = new Mock<IVectorizableTextSearch<string>>().Object;
        var builder = new VectorizableTextSearchBuilder<string>(innerSearch);

        // Act
        var builtSearch = builder.Build(null);

        // Assert
        Assert.Same(innerSearch, builtSearch);
    }
}
