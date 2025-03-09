// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class VectorStoreBuilderServiceCollectionExtensionsTests
{
    [Fact]
    public void AddVectorStoreWithInstanceReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var store = new Mock<IVectorStore>().Object;

        // Act
        var builder = services.AddVectorStore(store);
        var provider = services.BuildServiceProvider();
        var resolvedStore = provider.GetService<IVectorStore>();

        // Assert
        Assert.IsType<VectorStoreBuilder>(builder);
        Assert.Same(store, resolvedStore);
        Assert.Single(services, d => d.ServiceType == typeof(IVectorStore) && d.Lifetime == ServiceLifetime.Singleton);
    }

    [Fact]
    public void AddVectorStoreWithFactoryReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var store = new Mock<IVectorStore>().Object;
        IVectorStore Factory(IServiceProvider _) => store;

        // Act
        var builder = services.AddVectorStore(Factory, ServiceLifetime.Scoped);
        var provider = services.BuildServiceProvider();
        var resolvedStore = provider.GetService<IVectorStore>();

        // Assert
        Assert.IsType<VectorStoreBuilder>(builder);
        Assert.Same(store, resolvedStore);
        Assert.Single(services, d => d.ServiceType == typeof(IVectorStore) && d.Lifetime == ServiceLifetime.Scoped);
    }

    [Fact]
    public void AddKeyedVectorStoreWithInstanceReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var store = new Mock<IVectorStore>().Object;
        var key = "testKey";

        // Act
        var builder = services.AddKeyedVectorStore(key, store);
        var provider = services.BuildServiceProvider();
        var resolvedStore = provider.GetKeyedService<IVectorStore>(key);

        // Assert
        Assert.IsType<VectorStoreBuilder>(builder);
        Assert.Same(store, resolvedStore);
        Assert.Single(services,
            d => d.ServiceType == typeof(IVectorStore) &&
            d.ServiceKey is not null &&
            d.ServiceKey.Equals(key) &&
            d.Lifetime == ServiceLifetime.Singleton);
    }

    [Fact]
    public void AddKeyedVectorStoreWithFactoryReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var store = new Mock<IVectorStore>().Object;
        IVectorStore Factory(IServiceProvider _) => store;
        var key = "testKey";

        // Act
        var builder = services.AddKeyedVectorStore(key, Factory, ServiceLifetime.Scoped);
        var provider = services.BuildServiceProvider();
        var resolvedStore = provider.GetKeyedService<IVectorStore>(key);

        // Assert
        Assert.IsType<VectorStoreBuilder>(builder);
        Assert.Same(store, resolvedStore);
        Assert.Single(services,
            d => d.ServiceType == typeof(IVectorStore) &&
            d.ServiceKey is not null &&
            d.ServiceKey.Equals(key) &&
            d.Lifetime == ServiceLifetime.Scoped);
    }
}
