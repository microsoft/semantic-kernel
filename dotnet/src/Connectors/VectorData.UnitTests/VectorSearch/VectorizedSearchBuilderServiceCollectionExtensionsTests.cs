// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class VectorizedSearchBuilderServiceCollectionExtensionsTests
{
    [Fact]
    public void AddVectorizedSearchWithInstanceReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var search = new Mock<IVectorizedSearch<string>>().Object;

        // Act
        var builder = services.AddVectorizedSearch(search);
        var provider = services.BuildServiceProvider();
        var resolvedSearch = provider.GetService<IVectorizedSearch<string>>();

        // Assert
        Assert.IsType<VectorizedSearchBuilder<string>>(builder);
        Assert.Same(search, resolvedSearch);
        Assert.Single(services, d => d.ServiceType == typeof(IVectorizedSearch<string>) && d.Lifetime == ServiceLifetime.Singleton);
    }

    [Fact]
    public void AddVectorizedSearchWithFactoryReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var search = new Mock<IVectorizedSearch<string>>().Object;
        IVectorizedSearch<string> Factory(IServiceProvider _) => search;

        // Act
        var builder = services.AddVectorizedSearch(Factory, ServiceLifetime.Scoped);
        var provider = services.BuildServiceProvider();
        var resolvedSearch = provider.GetService<IVectorizedSearch<string>>();

        // Assert
        Assert.IsType<VectorizedSearchBuilder<string>>(builder);
        Assert.Same(search, resolvedSearch);
        Assert.Single(services, d => d.ServiceType == typeof(IVectorizedSearch<string>) && d.Lifetime == ServiceLifetime.Scoped);
    }

    [Fact]
    public void AddKeyedVectorizedSearchWithInstanceReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var search = new Mock<IVectorizedSearch<string>>().Object;
        var key = "testKey";

        // Act
        var builder = services.AddKeyedVectorizedSearch(key, search);
        var provider = services.BuildServiceProvider();
        var resolvedSearch = provider.GetKeyedService<IVectorizedSearch<string>>(key);

        // Assert
        Assert.IsType<VectorizedSearchBuilder<string>>(builder);
        Assert.Same(search, resolvedSearch);
        Assert.Single(services,
            d => d.ServiceType == typeof(IVectorizedSearch<string>) &&
            d.ServiceKey is not null &&
            d.ServiceKey.Equals(key) &&
            d.Lifetime == ServiceLifetime.Singleton);
    }

    [Fact]
    public void AddKeyedVectorizedSearchWithFactoryReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var search = new Mock<IVectorizedSearch<string>>().Object;
        IVectorizedSearch<string> Factory(IServiceProvider _) => search;
        var key = "testKey";

        // Act
        var builder = services.AddKeyedVectorizedSearch(key, Factory, ServiceLifetime.Scoped);
        var provider = services.BuildServiceProvider();
        var resolvedSearch = provider.GetKeyedService<IVectorizedSearch<string>>(key);

        // Assert
        Assert.IsType<VectorizedSearchBuilder<string>>(builder);
        Assert.Same(search, resolvedSearch);
        Assert.Single(services,
            d => d.ServiceType == typeof(IVectorizedSearch<string>) &&
            d.ServiceKey is not null &&
            d.ServiceKey.Equals(key) &&
            d.Lifetime == ServiceLifetime.Scoped);
    }
}
