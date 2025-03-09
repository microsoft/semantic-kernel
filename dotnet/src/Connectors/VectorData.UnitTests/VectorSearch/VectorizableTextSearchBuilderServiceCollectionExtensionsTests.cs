// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class VectorizableTextSearchBuilderServiceCollectionExtensionsTests
{
    [Fact]
    public void AddVectorizableTextSearchWithInstanceReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var search = new Mock<IVectorizableTextSearch<string>>().Object;

        // Act
        var builder = services.AddVectorizableTextSearch(search);
        var provider = services.BuildServiceProvider();
        var resolvedSearch = provider.GetService<IVectorizableTextSearch<string>>();

        // Assert
        Assert.IsType<VectorizableTextSearchBuilder<string>>(builder);
        Assert.Same(search, resolvedSearch);
        Assert.Single(services, d => d.ServiceType == typeof(IVectorizableTextSearch<string>) && d.Lifetime == ServiceLifetime.Singleton);
    }

    [Fact]
    public void AddVectorizableTextSearchWithFactoryReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var search = new Mock<IVectorizableTextSearch<string>>().Object;
        IVectorizableTextSearch<string> Factory(IServiceProvider _) => search;

        // Act
        var builder = services.AddVectorizableTextSearch(Factory, ServiceLifetime.Scoped);
        var provider = services.BuildServiceProvider();
        var resolvedSearch = provider.GetService<IVectorizableTextSearch<string>>();

        // Assert
        Assert.IsType<VectorizableTextSearchBuilder<string>>(builder);
        Assert.Same(search, resolvedSearch);
        Assert.Single(services, d => d.ServiceType == typeof(IVectorizableTextSearch<string>) && d.Lifetime == ServiceLifetime.Scoped);
    }

    [Fact]
    public void AddKeyedVectorizableTextSearchWithInstanceReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var search = new Mock<IVectorizableTextSearch<string>>().Object;
        var key = "testKey";

        // Act
        var builder = services.AddKeyedVectorizableTextSearch(key, search);
        var provider = services.BuildServiceProvider();
        var resolvedSearch = provider.GetKeyedService<IVectorizableTextSearch<string>>(key);

        // Assert
        Assert.IsType<VectorizableTextSearchBuilder<string>>(builder);
        Assert.Same(search, resolvedSearch);
        Assert.Single(services,
            d => d.ServiceType == typeof(IVectorizableTextSearch<string>) &&
            d.ServiceKey is not null &&
            d.ServiceKey.Equals(key) &&
            d.Lifetime == ServiceLifetime.Singleton);
    }

    [Fact]
    public void AddKeyedVectorizableTextSearchWithFactoryReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var search = new Mock<IVectorizableTextSearch<string>>().Object;
        IVectorizableTextSearch<string> Factory(IServiceProvider _) => search;
        var key = "testKey";

        // Act
        var builder = services.AddKeyedVectorizableTextSearch(key, Factory, ServiceLifetime.Scoped);
        var provider = services.BuildServiceProvider();
        var resolvedSearch = provider.GetKeyedService<IVectorizableTextSearch<string>>(key);

        // Assert
        Assert.IsType<VectorizableTextSearchBuilder<string>>(builder);
        Assert.Same(search, resolvedSearch);
        Assert.Single(services,
            d => d.ServiceType == typeof(IVectorizableTextSearch<string>) &&
            d.ServiceKey is not null &&
            d.ServiceKey.Equals(key) &&
            d.Lifetime == ServiceLifetime.Scoped);
    }
}
