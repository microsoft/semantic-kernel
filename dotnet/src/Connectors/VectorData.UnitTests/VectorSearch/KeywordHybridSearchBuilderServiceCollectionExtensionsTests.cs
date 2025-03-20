// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class KeywordHybridSearchBuilderServiceCollectionExtensionsTests
{
    [Fact]
    public void AddKeywordHybridSearchWithInstanceReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var search = new Mock<IKeywordHybridSearch<string>>().Object;

        // Act
        var builder = services.AddKeywordHybridSearch(search);
        var provider = services.BuildServiceProvider();
        var resolvedSearch = provider.GetService<IKeywordHybridSearch<string>>();

        // Assert
        Assert.IsType<KeywordHybridSearchBuilder<string>>(builder);
        Assert.Same(search, resolvedSearch);
        Assert.Single(services, d => d.ServiceType == typeof(IKeywordHybridSearch<string>) && d.Lifetime == ServiceLifetime.Singleton);
    }

    [Fact]
    public void AddKeywordHybridSearchWithFactoryReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var search = new Mock<IKeywordHybridSearch<string>>().Object;
        IKeywordHybridSearch<string> Factory(IServiceProvider _) => search;

        // Act
        var builder = services.AddKeywordHybridSearch(Factory, ServiceLifetime.Scoped);
        var provider = services.BuildServiceProvider();
        var resolvedSearch = provider.GetService<IKeywordHybridSearch<string>>();

        // Assert
        Assert.IsType<KeywordHybridSearchBuilder<string>>(builder);
        Assert.Same(search, resolvedSearch);
        Assert.Single(services, d => d.ServiceType == typeof(IKeywordHybridSearch<string>) && d.Lifetime == ServiceLifetime.Scoped);
    }

    [Fact]
    public void AddKeyedKeywordHybridSearchWithInstanceReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var search = new Mock<IKeywordHybridSearch<string>>().Object;
        var key = "testKey";

        // Act
        var builder = services.AddKeyedKeywordHybridSearch(key, search);
        var provider = services.BuildServiceProvider();
        var resolvedSearch = provider.GetKeyedService<IKeywordHybridSearch<string>>(key);

        // Assert
        Assert.IsType<KeywordHybridSearchBuilder<string>>(builder);
        Assert.Same(search, resolvedSearch);
        Assert.Single(services,
            d => d.ServiceType == typeof(IKeywordHybridSearch<string>) &&
            d.ServiceKey is not null &&
            d.ServiceKey.Equals(key) &&
            d.Lifetime == ServiceLifetime.Singleton);
    }

    [Fact]
    public void AddKeyedKeywordHybridSearchWithFactoryReturnsBuilder()
    {
        // Arrange
        var services = new ServiceCollection();
        var search = new Mock<IKeywordHybridSearch<string>>().Object;
        IKeywordHybridSearch<string> Factory(IServiceProvider _) => search;
        var key = "testKey";

        // Act
        var builder = services.AddKeyedKeywordHybridSearch(key, Factory, ServiceLifetime.Scoped);
        var provider = services.BuildServiceProvider();
        var resolvedSearch = provider.GetKeyedService<IKeywordHybridSearch<string>>(key);

        // Assert
        Assert.IsType<KeywordHybridSearchBuilder<string>>(builder);
        Assert.Same(search, resolvedSearch);
        Assert.Single(services,
            d => d.ServiceType == typeof(IKeywordHybridSearch<string>) &&
            d.ServiceKey is not null &&
            d.ServiceKey.Equals(key) &&
            d.Lifetime == ServiceLifetime.Scoped);
    }
}
