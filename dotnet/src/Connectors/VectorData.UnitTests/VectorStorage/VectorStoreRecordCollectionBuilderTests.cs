// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class VectorStoreRecordCollectionBuilderTests
{
    [Fact]
    public void ConstructorWithInstanceSetsInnerCollection()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>().Object;

        // Act
        var builder = new VectorStoreRecordCollectionBuilder<string, object>(innerCollection);

        // Assert
        var builtCollection = builder.Build();
        Assert.Same(innerCollection, builtCollection);
    }

    [Fact]
    public void ConstructorWithFactoryCallsFactoryOnBuild()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>().Object;
        var serviceProvider = new Mock<IServiceProvider>();
        IVectorStoreRecordCollection<string, object> Factory(IServiceProvider _) => innerCollection;

        // Act
        var builder = new VectorStoreRecordCollectionBuilder<string, object>(Factory);
        var builtCollection = builder.Build(serviceProvider.Object);

        // Assert
        Assert.Same(innerCollection, builtCollection);
    }

    [Fact]
    public void BuildWithMultipleFactoriesAppliesInReverseOrder()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>().Object;
        var mockCollection1 = new Mock<IVectorStoreRecordCollection<string, object>>().Object;
        var mockCollection2 = new Mock<IVectorStoreRecordCollection<string, object>>().Object;
        var builder = new VectorStoreRecordCollectionBuilder<string, object>(innerCollection);

        builder.Use(c => mockCollection1);
        builder.Use(c => mockCollection2);

        // Act
        var builtCollection = builder.Build();

        // Assert
        Assert.Same(mockCollection1, builtCollection);
    }

    [Fact]
    public void BuildWithNullReturningFactoryThrowsInvalidOperationException()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>().Object;
        var builder = new VectorStoreRecordCollectionBuilder<string, object>(innerCollection);
        builder.Use((c, _) => null!);

        // Act & Assert
        var exception = Assert.Throws<InvalidOperationException>(() => builder.Build());
        Assert.Contains("returned null", exception.Message);
    }

    [Fact]
    public void BuildWithNullServiceProviderUsesEmptyServiceProvider()
    {
        // Arrange
        var innerCollection = new Mock<IVectorStoreRecordCollection<string, object>>().Object;
        var builder = new VectorStoreRecordCollectionBuilder<string, object>(innerCollection);

        // Act
        var builtCollection = builder.Build(null);

        // Assert
        Assert.Same(innerCollection, builtCollection);
    }
}
