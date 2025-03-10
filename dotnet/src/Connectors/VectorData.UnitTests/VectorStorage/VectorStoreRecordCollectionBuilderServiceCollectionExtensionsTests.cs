// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class VectorStoreRecordCollectionBuilderServiceCollectionExtensionsTests
{
    [Fact]
    public void AddVectorStoreRecordCollectionWithInstanceReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var collection = new Mock<IVectorStoreRecordCollection<string, object>>().Object;

        // Act
        var builder = services.AddVectorStoreRecordCollection(collection);
        var provider = services.BuildServiceProvider();
        var resolvedCollection = provider.GetService<IVectorStoreRecordCollection<string, object>>();

        // Assert
        Assert.IsType<VectorStoreRecordCollectionBuilder<string, object>>(builder);
        Assert.Same(collection, resolvedCollection);
        Assert.Single(services, d => d.ServiceType == typeof(IVectorStoreRecordCollection<string, object>) && d.Lifetime == ServiceLifetime.Singleton);
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithFactoryReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var collection = new Mock<IVectorStoreRecordCollection<string, object>>().Object;
        IVectorStoreRecordCollection<string, object> Factory(IServiceProvider _) => collection;

        // Act
        var builder = services.AddVectorStoreRecordCollection(Factory, ServiceLifetime.Scoped);
        var provider = services.BuildServiceProvider();
        var resolvedCollection = provider.GetService<IVectorStoreRecordCollection<string, object>>();

        // Assert
        Assert.IsType<VectorStoreRecordCollectionBuilder<string, object>>(builder);
        Assert.Same(collection, resolvedCollection);
        Assert.Single(services, d => d.ServiceType == typeof(IVectorStoreRecordCollection<string, object>) && d.Lifetime == ServiceLifetime.Scoped);
    }

    [Fact]
    public void AddKeyedVectorStoreRecordCollectionWithInstanceReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var collection = new Mock<IVectorStoreRecordCollection<string, object>>().Object;
        var key = "testKey";

        // Act
        var builder = services.AddKeyedVectorStoreRecordCollection(key, collection);
        var provider = services.BuildServiceProvider();
        var resolvedCollection = provider.GetKeyedService<IVectorStoreRecordCollection<string, object>>(key);

        // Assert
        Assert.IsType<VectorStoreRecordCollectionBuilder<string, object>>(builder);
        Assert.Same(collection, resolvedCollection);
        Assert.Single(services,
            d => d.ServiceType == typeof(IVectorStoreRecordCollection<string, object>) &&
            d.ServiceKey is not null &&
            d.ServiceKey.Equals(key) &&
            d.Lifetime == ServiceLifetime.Singleton);
    }

    [Fact]
    public void AddKeyedVectorStoreRecordCollectionWithFactoryReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var collection = new Mock<IVectorStoreRecordCollection<string, object>>().Object;
        IVectorStoreRecordCollection<string, object> Factory(IServiceProvider _) => collection;
        var key = "testKey";

        // Act
        var builder = services.AddKeyedVectorStoreRecordCollection(key, Factory, ServiceLifetime.Scoped);
        var provider = services.BuildServiceProvider();
        var resolvedCollection = provider.GetKeyedService<IVectorStoreRecordCollection<string, object>>(key);

        // Assert
        Assert.IsType<VectorStoreRecordCollectionBuilder<string, object>>(builder);
        Assert.Same(collection, resolvedCollection);
        Assert.Single(services,
            d => d.ServiceType == typeof(IVectorStoreRecordCollection<string, object>) &&
            d.ServiceKey is not null &&
            d.ServiceKey.Equals(key) &&
            d.Lifetime == ServiceLifetime.Scoped);
    }
}
