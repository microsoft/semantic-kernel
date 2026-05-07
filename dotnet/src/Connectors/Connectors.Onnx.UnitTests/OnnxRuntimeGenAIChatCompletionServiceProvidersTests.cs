// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.ML.OnnxRuntimeGenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Onnx;
using Xunit;

namespace SemanticKernel.Connectors.Onnx.UnitTests;

/// <summary>
/// Unit tests for <see cref="OnnxRuntimeGenAIChatCompletionService"/> constructor overloads and Provider functionality.
/// </summary>
public class OnnxRuntimeGenAIChatCompletionServiceProvidersTests
{
    private const string TestModelId = "test-model";
    private const string TestModelPath = "test-model-path";

    [Fact]
    public void ConstructorWithProvidersShouldValidateParameters()
    {
        // Arrange
        var providers = new List<Provider> { new("cuda"), new("cpu") };

        // Act & Assert - Should not throw during parameter validation
        // Note: We expect this to fail during ONNX model loading, but parameter validation should pass
        var exception = Assert.ThrowsAny<Exception>(() =>
            new OnnxRuntimeGenAIChatCompletionService(TestModelId, TestModelPath, providers));

        // The exception should not be from parameter validation (ArgumentException/ArgumentNullException)
        Assert.False(exception is ArgumentException or ArgumentNullException,
            "Constructor should not fail due to parameter validation when valid parameters are provided");
    }

    [Fact]
    public void ConstructorWithNullModelIdShouldThrowArgumentNullException()
    {
        // Arrange
        var providers = new List<Provider> { new("cuda") };

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() =>
            new OnnxRuntimeGenAIChatCompletionService(
                null!,
                TestModelPath,
                providers));
    }

    [Fact]
    public void ConstructorWithEmptyModelIdShouldThrowArgumentException()
    {
        // Arrange
        var providers = new List<Provider> { new("cuda") };

        // Act & Assert
        Assert.Throws<ArgumentException>(() =>
            new OnnxRuntimeGenAIChatCompletionService(
                string.Empty,
                TestModelPath,
                providers));
    }

    [Fact]
    public void ConstructorWithNullModelPathShouldThrowArgumentNullException()
    {
        // Arrange
        var providers = new List<Provider> { new("cuda") };

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() =>
            new OnnxRuntimeGenAIChatCompletionService(
                TestModelId,
                null!,
                providers));
    }

    [Fact]
    public void ConstructorWithEmptyModelPathShouldThrowArgumentException()
    {
        // Arrange
        var providers = new List<Provider> { new("cuda") };

        // Act & Assert
        Assert.Throws<ArgumentException>(() =>
            new OnnxRuntimeGenAIChatCompletionService(
                TestModelId,
                string.Empty,
                providers));
    }

    [Fact]
    public void ConstructorWithNullProvidersShouldThrowArgumentNullException()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() =>
            new OnnxRuntimeGenAIChatCompletionService(
                TestModelId,
                TestModelPath,
                (IEnumerable<Provider>)null!));
    }

    [Fact]
    public void ConstructorWithEmptyProvidersShouldValidateParameters()
    {
        // Arrange
        var providers = new List<Provider>();

        // Act & Assert - Should not throw during parameter validation
        var exception = Assert.ThrowsAny<Exception>(() =>
            new OnnxRuntimeGenAIChatCompletionService(TestModelId, TestModelPath, providers));

        // The exception should not be from parameter validation
        Assert.False(exception is ArgumentException or ArgumentNullException,
            "Constructor should not fail due to parameter validation when valid parameters are provided");
    }

    [Fact]
    public void ConstructorWithMultipleProvidersShouldValidateParameters()
    {
        // Arrange
        var providers = new List<Provider>
        {
            new("cuda"),
            new("cpu"),
            new("dml")
        };

        // Act & Assert - Should not throw during parameter validation
        var exception = Assert.ThrowsAny<Exception>(() =>
            new OnnxRuntimeGenAIChatCompletionService(TestModelId, TestModelPath, providers));

        // The exception should not be from parameter validation
        Assert.False(exception is ArgumentException or ArgumentNullException,
            "Constructor should not fail due to parameter validation when valid parameters are provided");
    }

    [Fact]
    public void ConstructorWithProviderOptionsShouldValidateParameters()
    {
        // Arrange
        var provider = new Provider("cuda");
        provider.Options["device_id"] = "0";
        provider.Options["gpu_mem_limit"] = "2147483648";
        var providers = new List<Provider> { provider };

        // Act & Assert - Should not throw during parameter validation
        var exception = Assert.ThrowsAny<Exception>(() =>
            new OnnxRuntimeGenAIChatCompletionService(TestModelId, TestModelPath, providers));

        // The exception should not be from parameter validation
        Assert.False(exception is ArgumentException or ArgumentNullException,
            "Constructor should not fail due to parameter validation when valid parameters are provided");
    }

    [Theory]
    [InlineData("cuda")]
    [InlineData("cpu")]
    [InlineData("dml")]
    [InlineData("coreml")]
    public void ConstructorWithDifferentProviderTypesShouldValidateParameters(string providerId)
    {
        // Arrange
        var providers = new List<Provider> { new(providerId) };

        // Act & Assert - Should not throw during parameter validation
        var exception = Assert.ThrowsAny<Exception>(() =>
            new OnnxRuntimeGenAIChatCompletionService(TestModelId, TestModelPath, providers));

        // The exception should not be from parameter validation
        Assert.False(exception is ArgumentException or ArgumentNullException,
            "Constructor should not fail due to parameter validation when valid parameters are provided");
    }

    [Fact]
    public void ServiceRegistrationWithProvidersShouldRegisterCorrectly()
    {
        // Arrange
        var services = new ServiceCollection();
        var providers = new List<Provider> { new("cuda") };

        // Act
        services.AddOnnxRuntimeGenAIChatCompletion(TestModelId, TestModelPath, providers);

        // Assert
        var serviceDescriptor = services.FirstOrDefault(x => x.ServiceType == typeof(IChatCompletionService));
        Assert.NotNull(serviceDescriptor);
        Assert.Equal(ServiceLifetime.Singleton, serviceDescriptor.Lifetime);
        Assert.NotNull(serviceDescriptor.ImplementationFactory);
    }

    [Fact]
    public void ServiceRegistrationWithProvidersAndServiceIdShouldRegisterWithKey()
    {
        // Arrange
        var services = new ServiceCollection();
        var providers = new List<Provider> { new("cuda") };
        const string serviceId = "test-service";

        // Act
        services.AddOnnxRuntimeGenAIChatCompletion(TestModelId, TestModelPath, providers, serviceId);
        services.AddKernel();
        var serviceProvider = services.BuildServiceProvider();
        var kernel = serviceProvider.GetRequiredService<Kernel>();

        // Assert - Should be able to retrieve the service by its key
        var exception = Assert.Throws<OnnxRuntimeGenAIException>(() => kernel.GetRequiredService<IChatCompletionService>("test-service"));

        Assert.Contains("genai_config.json", exception.Message);
    }

    [Fact]
    public void KernelBuilderExtensionWithProvidersShouldRegisterCorrectly()
    {
        // Arrange
        var services = new ServiceCollection();
        var kernelBuilder = services.AddKernel();
        var providers = new List<Provider> { new("cuda") };

        // Act
        kernelBuilder.AddOnnxRuntimeGenAIChatCompletion(TestModelId, TestModelPath, providers);

        // Assert
        var serviceDescriptor = services.FirstOrDefault(x => x.ServiceType == typeof(IChatCompletionService));
        Assert.NotNull(serviceDescriptor);
        Assert.Equal(ServiceLifetime.Singleton, serviceDescriptor.Lifetime);
        Assert.NotNull(serviceDescriptor.ImplementationFactory);
    }

    [Fact]
    public void KernelBuilderExtensionWithProvidersAndServiceIdShouldRegisterWithKey()
    {
        // Arrange
        var services = new ServiceCollection();
        var kernelBuilder = services.AddKernel();
        var providers = new List<Provider> { new("cuda") };
        const string serviceId = "test-service";

        // Act
        kernelBuilder.AddOnnxRuntimeGenAIChatCompletion(TestModelId, TestModelPath, providers, serviceId);
        var serviceProvider = services.BuildServiceProvider();
        var kernel = serviceProvider.GetRequiredService<Kernel>();

        // Assert - Should be able to retrieve the service by its key
        var exception = Assert.Throws<OnnxRuntimeGenAIException>(() => kernel.GetRequiredService<IChatCompletionService>("test-service"));

        Assert.Contains("genai_config.json", exception.Message);
    }

    [Fact]
    public void ProviderConstructorShouldInitializeCorrectly()
    {
        // Arrange & Act
        var provider = new Provider("cuda");

        // Assert
        Assert.Equal("cuda", provider.Id);
        Assert.NotNull(provider.Options);
        Assert.Empty(provider.Options);
    }

    [Fact]
    public void ProviderWithOptionsShouldStoreOptionsCorrectly()
    {
        // Arrange
        var provider = new Provider("cuda");

        // Act
        provider.Options["device_id"] = "0";
        provider.Options["gpu_mem_limit"] = "2147483648";

        // Assert
        Assert.Equal("0", provider.Options["device_id"]);
        Assert.Equal("2147483648", provider.Options["gpu_mem_limit"]);
        Assert.Equal(2, provider.Options.Count);
    }

    [Fact]
    public void ProviderConstructorWithNullIdShouldThrowArgumentNullException()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new Provider(null!));
    }

    [Fact]
    public void ProviderConstructorWithEmptyIdShouldThrowArgumentException()
    {
        // Act & Assert
        Assert.Throws<ArgumentException>(() => new Provider(string.Empty));
    }

    [Fact]
    public void ProviderConstructorWithWhitespaceIdShouldThrowArgumentException()
    {
        // Act & Assert
        Assert.Throws<ArgumentException>(() => new Provider("   "));
    }
}
