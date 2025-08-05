// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.ML.OnnxRuntimeGenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Onnx;
using Xunit;

namespace SemanticKernel.Connectors.Onnx.UnitTests;

/// <summary>
/// Unit tests for <see cref="OnnxChatClientKernelBuilderExtensions"/> and Onnx IChatClient service collection extensions.
/// </summary>
public class OnnxChatClientExtensionsTests
{
    [Fact]
    public void AddOnnxRuntimeGenAIChatClientToServiceCollection()
    {
        // Arrange
        var collection = new ServiceCollection();

        // Act
        collection.AddOnnxRuntimeGenAIChatClient("modelId");

        // Assert
        var serviceDescriptor = collection.FirstOrDefault(x => x.ServiceType == typeof(IChatClient));
        Assert.NotNull(serviceDescriptor);
        Assert.Equal(ServiceLifetime.Singleton, serviceDescriptor.Lifetime);
    }

    [Fact]
    public void AddOnnxRuntimeGenAIChatClientToKernelBuilder()
    {
        // Arrange
        var collection = new ServiceCollection();
        var kernelBuilder = collection.AddKernel();

        // Act
        kernelBuilder.AddOnnxRuntimeGenAIChatClient("modelPath");

        // Assert
        var serviceDescriptor = collection.FirstOrDefault(x => x.ServiceType == typeof(IChatClient));
        Assert.NotNull(serviceDescriptor);
        Assert.Equal(ServiceLifetime.Singleton, serviceDescriptor.Lifetime);
    }

    [Fact]
    public void AddOnnxRuntimeGenAIChatClientWithServiceId()
    {
        // Arrange
        var collection = new ServiceCollection();

        // Act
        collection.AddOnnxRuntimeGenAIChatClient("modelPath", serviceId: "test-service");

        // Assert
        var serviceDescriptor = collection.FirstOrDefault(x => x.ServiceType == typeof(IChatClient) && x.ServiceKey?.ToString() == "test-service");
        Assert.NotNull(serviceDescriptor);
        Assert.Equal(ServiceLifetime.Singleton, serviceDescriptor.Lifetime);
    }

    [Fact]
    public void AddOnnxRuntimeGenAIChatClientToKernelBuilderWithServiceId()
    {
        // Arrange
        var collection = new ServiceCollection();
        var kernelBuilder = collection.AddKernel();

        // Act
        kernelBuilder.AddOnnxRuntimeGenAIChatClient("modelPath", serviceId: "test-service");

        // Assert
        var serviceDescriptor = collection.FirstOrDefault(x => x.ServiceType == typeof(IChatClient) && x.ServiceKey?.ToString() == "test-service");
        Assert.NotNull(serviceDescriptor);
        Assert.Equal(ServiceLifetime.Singleton, serviceDescriptor.Lifetime);
    }

    [Fact]
    public void AddOnnxRuntimeGenAIChatClientWithProvidersToServiceCollection()
    {
        // Arrange
        var collection = new ServiceCollection();
        var providers = new List<Provider> { new("cuda"), new("cpu") };

        // Act
        collection.AddOnnxRuntimeGenAIChatClient("modelPath", providers);

        // Assert
        var serviceDescriptor = collection.FirstOrDefault(x => x.ServiceType == typeof(IChatClient));
        Assert.NotNull(serviceDescriptor);
        Assert.Equal(ServiceLifetime.Singleton, serviceDescriptor.Lifetime);
        Assert.NotNull(serviceDescriptor.ImplementationFactory);
    }

    [Fact]
    public void AddOnnxRuntimeGenAIChatClientWithProvidersToKernelBuilder()
    {
        // Arrange
        var collection = new ServiceCollection();
        var kernelBuilder = collection.AddKernel();
        var providers = new List<Provider> { new("cuda"), new("cpu") };

        // Act
        kernelBuilder.AddOnnxRuntimeGenAIChatClient("modelPath", providers);

        // Assert
        var serviceDescriptor = collection.FirstOrDefault(x => x.ServiceType == typeof(IChatClient));
        Assert.NotNull(serviceDescriptor);
        Assert.Equal(ServiceLifetime.Singleton, serviceDescriptor.Lifetime);
        Assert.NotNull(serviceDescriptor.ImplementationFactory);
    }

    [Fact]
    public void AddOnnxRuntimeGenAIChatClientWithProvidersAndServiceIdToServiceCollection()
    {
        // Arrange
        var collection = new ServiceCollection();
        var providers = new List<Provider> { new("cuda") };

        // Act
        collection.AddOnnxRuntimeGenAIChatClient("modelPath", providers, serviceId: "test-service");
        var serviceProvider = collection.BuildServiceProvider();

        // Assert
        var exception = Assert.Throws<OnnxRuntimeGenAIException>(() => serviceProvider.GetRequiredKeyedService<IChatClient>("test-service"));

        Assert.Contains("Error opening modelPath\\genai_config.json", exception.Message);
    }

    [Fact]
    public void AddOnnxRuntimeGenAIChatClientWithProvidersAndServiceIdToKernelBuilder()
    {
        // Arrange
        var collection = new ServiceCollection();
        var kernelBuilder = collection.AddKernel();
        var providers = new List<Provider> { new("cuda") };

        // Act
        kernelBuilder.AddOnnxRuntimeGenAIChatClient("modelPath", providers, serviceId: "test-service");
        var serviceProvider = collection.BuildServiceProvider();

        // Assert
        var kernel = serviceProvider.GetRequiredService<Kernel>();
        var exception = Assert.Throws<OnnxRuntimeGenAIException>(() => kernel.GetRequiredService<IChatClient>("test-service"));

        Assert.Contains("Error opening modelPath\\genai_config.json", exception.Message);
    }
}
