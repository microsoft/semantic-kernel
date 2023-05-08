// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.UnitTests.Services;

/// <summary>
/// Unit tests of <see cref="AIServiceCollection"/>.
/// </summary>
public class ServiceRegistryTests
{
    [Fact]
    public void ItCanSetAndRetrieveServiceInstance()
    {
        // Arrange
        var services = new AIServiceCollection();
        var service = new TestService();

        // Act
        services.SetService<IAIService>(service);
        var provider = services.Build();
        var result = provider.GetService<IAIService>();

        // Assert
        Assert.Same(service, result);
    }

    [Fact]
    public void ItCanSetAndRetrieveServiceInstanceWithName()
    {
        // Arrange
        var services = new AIServiceCollection();
        var service1 = new TestService();
        var service2 = new TestService();

        // Act
        services.SetService<IAIService>("foo", service1);
        services.SetService<IAIService>("bar", service2);
        var provider = services.Build();

        // Assert
        Assert.Same(service1, provider.GetService<IAIService>("foo"));
        Assert.Same(service2, provider.GetService<IAIService>("bar"));
    }

    [Fact]
    public void ItCanSetAndRetrieveServiceFactory()
    {
        // Arrange
        var services = new AIServiceCollection();
        var service = new TestService();

        // Act
        services.SetService<IAIService>(() => service);
        var provider = services.Build();

        // Assert
        Assert.Same(service, provider.GetService<IAIService>());
    }

    [Fact]
    public void ItCanSetAndRetrieveServiceFactoryWithName()
    {
        // Arrange
        var services = new AIServiceCollection();
        var service1 = new TestService();
        var service2 = new TestService();

        // Act
        services.SetService<IAIService>("foo", () => service1);
        services.SetService<IAIService>("bar", () => service2);
        var provider = services.Build();

        // Assert
        Assert.Same(service1, provider.GetService<IAIService>("foo"));
        Assert.Same(service2, provider.GetService<IAIService>("bar"));
    }

    [Fact]
    public void ItCanSetAndRetrieveServiceFactoryWithServiceProvider()
    {
        // Arrange
        var services = new AIServiceCollection();
        var service = new TestService();

        // Act
        services.SetService<IAIService>(() => service);
        var provider = services.Build();

        // Assert
        Assert.Same(service, provider.GetService<IAIService>());
    }

    [Fact]
    public void ItCanSetAndRetrieveServiceFactoryWithServiceProviderAndName()
    {
        // Arrange
        var services = new AIServiceCollection();
        var service1 = new TestService();
        var service2 = new TestService();

        // Act
        services.SetService<IAIService>("foo", () => service1);
        services.SetService<IAIService>("bar", () => service2);
        var provider = services.Build();

        // Assert
        Assert.Same(service1, provider.GetService<IAIService>("foo"));
        Assert.Same(service2, provider.GetService<IAIService>("bar"));
    }

    [Fact]
    public void ItCanSetDefaultService()
    {
        // Arrange
        var services = new AIServiceCollection();
        var service1 = new TestService();
        var service2 = new TestService();

        // Act
        services.SetService<IAIService>("foo", service1);
        services.SetService<IAIService>("bar", service2, setAsDefault: true);
        var provider = services.Build();

        // Assert
        Assert.Same(service2, provider.GetService<IAIService>());
    }

    [Fact]
    public void ItCanSetDefaultServiceFactory()
    {
        // Arrange
        var services = new AIServiceCollection();
        var service1 = new TestService();
        var service2 = new TestService();

        // Act
        services.SetService<IAIService>("foo", () => service1);
        services.SetService<IAIService>("bar", () => service2, setAsDefault: true);
        var provider = services.Build();

        // Assert
        Assert.Same(service2, provider.GetService<IAIService>());
    }

    [Fact]
    public void ItCanSetDefaultServiceFactoryWithServiceProvider()
    {
        // Arrange
        var services = new AIServiceCollection();
        var service1 = new TestService();
        var service2 = new TestService();

        // Act
        services.SetService<IAIService>("foo", () => service1);
        services.SetService<IAIService>("bar", () => service2, setAsDefault: true);
        var provider = services.Build();

        // Assert
        Assert.Same(service2, provider.GetService<IAIService>());
    }

    [Fact]
    public void ItCanTryGetService()
    {
        // Arrange
        var services = new AIServiceCollection();
        var service = new TestService();
        services.SetService<IAIService>(service);
        var provider = services.Build();

        // Act
        var result = provider.TryGetService(out IAIService? retrieved);

        // Assert
        Assert.True(result);
        Assert.Same(service, retrieved);
    }

    [Fact]
    public void ItCanTryGetServiceWithName()
    {
        // Arrange
        var services = new AIServiceCollection();
        var service = new TestService();
        services.SetService<IAIService>("foo", service);
        var provider = services.Build();

        // Act
        var result = provider.TryGetService("foo", out IAIService? retrieved);

        // Assert
        Assert.True(result);
        Assert.Same(service, retrieved);
    }

    [Fact]
    public void ItReturnsFalseIfTryGetServiceWithInvalidName()
    {
        // Arrange
        var services = new AIServiceCollection();
        var service = new TestService();
        services.SetService<IAIService>("foo", service);
        var provider = services.Build();

        // Act
        var result = provider.TryGetService("bar", out IAIService? retrieved);

        // Assert
        Assert.False(result);
        Assert.Null(retrieved);
    }

    // A test service implementation
    private sealed class TestService : IAIService
    {
    }
}
