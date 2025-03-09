// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class VectorStoreBuilderTests
{
    [Fact]
    public void ConstructorWithInstanceSetsInnerStore()
    {
        // Arrange
        var innerStore = new Mock<IVectorStore>().Object;

        // Act
        var builder = new VectorStoreBuilder(innerStore);

        // Assert
        var builtStore = builder.Build();
        Assert.Same(innerStore, builtStore);
    }

    [Fact]
    public void ConstructorWithFactoryCallsFactoryOnBuild()
    {
        // Arrange
        var innerStore = new Mock<IVectorStore>().Object;
        var serviceProvider = new Mock<IServiceProvider>();
        IVectorStore Factory(IServiceProvider _) => innerStore;

        // Act
        var builder = new VectorStoreBuilder(Factory);
        var builtStore = builder.Build(serviceProvider.Object);

        // Assert
        Assert.Same(innerStore, builtStore);
    }

    [Fact]
    public void BuildWithMultipleFactoriesAppliesInReverseOrder()
    {
        // Arrange
        var innerStore = new Mock<IVectorStore>().Object;
        var mockStore1 = new Mock<IVectorStore>().Object;
        var mockStore2 = new Mock<IVectorStore>().Object;
        var builder = new VectorStoreBuilder(innerStore);

        builder.Use(s => mockStore1);
        builder.Use(s => mockStore2);

        // Act
        var builtStore = builder.Build();

        // Assert
        Assert.Same(mockStore1, builtStore);
    }

    [Fact]
    public void BuildWithNullReturningFactoryThrowsInvalidOperationException()
    {
        // Arrange
        var innerStore = new Mock<IVectorStore>().Object;
        var builder = new VectorStoreBuilder(innerStore);
        builder.Use((s, _) => null!);

        // Act & Assert
        var exception = Assert.Throws<InvalidOperationException>(() => builder.Build());
        Assert.Contains("returned null", exception.Message);
    }

    [Fact]
    public void BuildWithNullServiceProviderUsesEmptyServiceProvider()
    {
        // Arrange
        var innerStore = new Mock<IVectorStore>().Object;
        var builder = new VectorStoreBuilder(innerStore);

        // Act
        var builtStore = builder.Build(null);

        // Assert
        Assert.Same(innerStore, builtStore);
    }
}
