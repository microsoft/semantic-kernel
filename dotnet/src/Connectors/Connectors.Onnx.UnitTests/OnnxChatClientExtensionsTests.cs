// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
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
        collection.AddOnnxRuntimeGenAIChatClient("modelId", "modelPath");

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
        kernelBuilder.AddOnnxRuntimeGenAIChatClient("modelId", "modelPath");

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
        collection.AddOnnxRuntimeGenAIChatClient("modelId", "modelPath", "test-service");

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
        kernelBuilder.AddOnnxRuntimeGenAIChatClient("modelId", "modelPath", "test-service");

        // Assert
        var serviceDescriptor = collection.FirstOrDefault(x => x.ServiceType == typeof(IChatClient) && x.ServiceKey?.ToString() == "test-service");
        Assert.NotNull(serviceDescriptor);
        Assert.Equal(ServiceLifetime.Singleton, serviceDescriptor.Lifetime);
    }
}
