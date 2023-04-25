// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.UnitTests.Services;

/// <summary>
/// Unit tests of <see cref="ServiceRegistry"/>.
/// </summary>
public class ServiceRegistryTests
{
    [Fact]
    public void ItCanSetAndRetrieveServiceInstance()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service = new TestService();

        // Act
        services.SetService<ITestService>(service);
        var result = services.GetService<ITestService>();

        // Assert
        Assert.Same(service, result);
    }

    [Fact]
    public void ItCanSetAndRetrieveServiceInstanceWithName()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service1 = new TestService();
        var service2 = new TestService();

        // Act
        services.SetService<ITestService>("foo", service1);
        services.SetService<ITestService>("bar", service2);

        // Assert
        Assert.Same(service1, services.GetService<ITestService>("foo"));
        Assert.Same(service2, services.GetService<ITestService>("bar"));
    }

    [Fact]
    public void ItCanSetAndRetrieveServiceFactory()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service = new TestService();

        // Act
        services.SetServiceFactory<ITestService>(() => service);

        // Assert
        Assert.Same(service, services.GetService<ITestService>());
    }

    [Fact]
    public void ItCanSetAndRetrieveServiceFactoryWithName()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service1 = new TestService();
        var service2 = new TestService();

        // Act
        services.SetServiceFactory<ITestService>("foo", () => service1);
        services.SetServiceFactory<ITestService>("bar", () => service2);

        // Assert
        Assert.Same(service1, services.GetService<ITestService>("foo"));
        Assert.Same(service2, services.GetService<ITestService>("bar"));
    }

    [Fact]
    public void ItCanSetAndRetrieveServiceFactoryWithServiceProvider()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service = new TestService();

        // Act
        services.SetServiceFactory<ITestService>(sp => service);

        // Assert
        Assert.Same(service, services.GetService<ITestService>());
    }

    [Fact]
    public void ItCanSetAndRetrieveServiceFactoryWithServiceProviderAndName()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service1 = new TestService();
        var service2 = new TestService();

        // Act
        services.SetServiceFactory<ITestService>("foo", sp => service1);
        services.SetServiceFactory<ITestService>("bar", sp => service2);

        // Assert
        Assert.Same(service1, services.GetService<ITestService>("foo"));
        Assert.Same(service2, services.GetService<ITestService>("bar"));
    }

    [Fact]
    public void ItCanSetDefaultService()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service1 = new TestService();
        var service2 = new TestService();

        // Act
        services.SetService<ITestService>("foo", service1);
        services.SetService<ITestService>("bar", service2, isDefault: true);

        // Assert
        Assert.Same(service2, services.GetService<ITestService>());
    }

    [Fact]
    public void ItCanSetDefaultServiceFactory()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service1 = new TestService();
        var service2 = new TestService();

        // Act
        services.SetServiceFactory<ITestService>("foo", () => service1);
        services.SetServiceFactory<ITestService>("bar", () => service2, isDefault: true);

        // Assert
        Assert.Same(service2, services.GetService<ITestService>());
    }

    [Fact]
    public void ItCanSetDefaultServiceFactoryWithServiceProvider()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service1 = new TestService();
        var service2 = new TestService();

        // Act
        services.SetServiceFactory<ITestService>("foo", sp => service1);
        services.SetServiceFactory<ITestService>("bar", sp => service2, isDefault: true);

        // Assert
        Assert.Same(service2, services.GetService<ITestService>());
    }

    [Fact]
    public void ItCanTryGetService()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service = new TestService();
        services.SetService<ITestService>(service);

        // Act
        var result = services.TryGetService(out ITestService? retrieved);

        // Assert
        Assert.True(result);
        Assert.Same(service, retrieved);
    }

    [Fact]
    public void ItCanTryGetServiceWithName()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service = new TestService();
        services.SetService<ITestService>("foo", service);

        // Act
        var result = services.TryGetService("foo", out ITestService? retrieved);

        // Assert
        Assert.True(result);
        Assert.Same(service, retrieved);
    }

    [Fact]
    public void ItReturnsFalseIfTryGetServiceWithInvalidName()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service = new TestService();
        services.SetService<ITestService>("foo", service);

        // Act
        var result = services.TryGetService("bar", out ITestService? retrieved);

        // Assert
        Assert.False(result);
        Assert.Null(retrieved);
    }

    [Fact]
    public void ItReturnsFalseIfTryGetServiceWithInvalidType()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service = new TestService();
        services.SetService<ITestService>(service);

        // Act
        var result = services.TryGetService(out string? retrieved);

        // Assert
        Assert.False(result);
        Assert.Null(retrieved);
    }

    [Fact]
    public void ItCanTrySetDefaultService()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service1 = new TestService();
        var service2 = new TestService();
        services.SetService<ITestService>("foo", service1);
        services.SetService<ITestService>("bar", service2);

        // Act
        var result = services.TrySetDefault<ITestService>("foo");

        // Assert
        Assert.True(result);
        Assert.Same(service1, services.GetService<ITestService>());
    }

    [Fact]
    public void ItReturnsFalseIfTrySetDefaultServiceWithInvalidName()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service1 = new TestService();
        var service2 = new TestService();
        services.SetService<ITestService>("foo", service1);
        services.SetService<ITestService>("bar", service2);

        // Act
        var result = services.TrySetDefault<ITestService>("baz");

        // Assert
        Assert.False(result);
        Assert.Same(service1, services.GetService<ITestService>());
    }

    [Fact]
    public void ItReturnsFalseIfTrySetDefaultServiceWithInvalidType()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service = new TestService();
        services.SetService<ITestService>(service);

        // Act
        var result = services.TrySetDefault<string>("foo");

        // Assert
        Assert.False(result);
        Assert.Null(services.GetService<string>());
    }

    [Fact]
    public void ItCanGetServiceNames()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service1 = new TestService();
        var service2 = new TestService();
        services.SetService<ITestService>("foo", service1);
        services.SetService<ITestService>("bar", service2);

        // Act
        var names = services.GetServiceNames<ITestService>();

        // Assert
        Assert.Equal(new[] { "foo", "bar" }, names);
    }

    [Fact]
    public void ItReturnsEmptyEnumerableIfNoServiceNames()
    {
        // Arrange
        var services = new ServiceRegistry();

        // Act
        var names = services.GetServiceNames<ITestService>();

        // Assert
        Assert.Empty(names);
    }

    [Fact]
    public void ItCanGetDefaultServiceName()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service1 = new TestService();
        var service2 = new TestService();
        services.SetService<ITestService>("foo", service1);
        services.SetService<ITestService>("bar", service2, isDefault: true);

        // Act
        var name = services.GetDefaultServiceName<ITestService>();

        // Assert
        Assert.Equal("bar", name);
    }

    [Fact]
    public void ItReturnsNullIfNoDefaultServiceName()
    {
        // Arrange
        var services = new ServiceRegistry();

        // Act
        var name = services.GetDefaultServiceName<ITestService>();

        // Assert
        Assert.Null(name);
    }

    [Fact]
    public void ItReturnsFirstServiceNameIfNoExplicitDefault()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service1 = new TestService();
        var service2 = new TestService();
        services.SetService<ITestService>("foo", service1);
        services.SetService<ITestService>("bar", service2);

        // Act
        var name = services.GetDefaultServiceName<ITestService>();

        // Assert
        Assert.Equal("foo", name);
    }

    [Fact]
    public void ItCanCheckIfHasServiceName()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service = new TestService();
        services.SetService<ITestService>("foo", service);

        // Act
        var result1 = services.HasServiceName<ITestService>("foo");
        var result2 = services.HasServiceName<ITestService>("bar");

        // Assert
        Assert.True(result1);
        Assert.False(result2);
    }

    [Fact]
    public void ItCanCheckIfHasDefaultServiceName()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service = new TestService();
        services.SetService<ITestService>(service);

        // Act
        var result = services.HasServiceName<ITestService>();

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfNoServiceName()
    {
        // Arrange
        var services = new ServiceRegistry();

        // Act
        var result = services.HasServiceName<ITestService>();

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void ItCanTryRemoveService()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service = new TestService();
        services.SetService<ITestService>("foo", service);

        // Act
        var result = services.TryRemove<ITestService>("foo");

        // Assert
        Assert.True(result);
        Assert.Null(services.GetService<ITestService>("foo"));
    }

    [Fact]
    public void ItReturnsFalseIfTryRemoveServiceWithInvalidName()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service = new TestService();
        services.SetService<ITestService>("foo", service);

        // Act
        var result = services.TryRemove<ITestService>("bar");

        // Assert
        Assert.False(result);
        Assert.Same(service, services.GetService<ITestService>("foo"));
    }

    [Fact]
    public void ItReturnsFalseIfTryRemoveServiceWithInvalidType()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service = new TestService();
        services.SetService<ITestService>(service);

        // Act
        var result = services.TryRemove<string>("foo");

        // Assert
        Assert.False(result);
        Assert.Same(service, services.GetService<ITestService>());
    }

    [Fact]
    public void ItCanClearServiceByType()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service1 = new TestService();
        var service2 = new TestService();
        services.SetService<ITestService>("foo", service1);
        services.SetService<ITestService>("bar", service2);

        // Act
        services.Clear<ITestService>();

        // Assert
        Assert.Null(services.GetService<ITestService>("foo"));
        Assert.Null(services.GetService<ITestService>("bar"));
    }

    [Fact]
    public void ItCanClearAllServices()
    {
        // Arrange
        var services = new ServiceRegistry();
        var service1 = new TestService();
        var service2 = new TestService();
        services.SetService<ITestService>("foo", service1);
        services.SetService<ITestService>("bar", service2);

        // Act
        services.Clear();

        // Assert
        Assert.Null(services.GetService<ITestService>("foo"));
        Assert.Null(services.GetService<ITestService>("bar"));
    }

    // A test service interface
    private interface ITestService
    {
    }

    // A test service implementation
    private sealed class TestService : ITestService
    {
    }
}
