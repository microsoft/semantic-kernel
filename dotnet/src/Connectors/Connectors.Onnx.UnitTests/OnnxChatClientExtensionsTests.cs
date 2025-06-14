// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Xunit;

#pragma warning disable SKEXP0010

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
        collection.AddOnnxRuntimeGenAIChatClient("modelId", "modelPath");

        // Act
        var kernelBuilder = collection.AddKernel();
        var serviceProvider = collection.BuildServiceProvider();
        var kernel = serviceProvider.GetRequiredService<Kernel>();
        var service = kernel.GetRequiredService<IChatClient>();

        // Assert
        Assert.NotNull(service);
    }

    [Fact]
    public void AddOnnxRuntimeGenAIChatClientToKernelBuilder()
    {
        // Arrange
        var collection = new ServiceCollection();
        var kernelBuilder = collection.AddKernel();
        kernelBuilder.AddOnnxRuntimeGenAIChatClient("modelId", "modelPath");

        // Act
        var serviceProvider = collection.BuildServiceProvider();
        var kernel = serviceProvider.GetRequiredService<Kernel>();
        var service = kernel.GetRequiredService<IChatClient>();

        // Assert
        Assert.NotNull(service);
    }

    [Fact]
    public void AddOnnxRuntimeGenAIChatClientWithServiceId()
    {
        // Arrange
        var collection = new ServiceCollection();
        collection.AddOnnxRuntimeGenAIChatClient("modelId", "modelPath", "test-service");

        // Act
        var kernelBuilder = collection.AddKernel();
        var serviceProvider = collection.BuildServiceProvider();
        var kernel = serviceProvider.GetRequiredService<Kernel>();
        var service = serviceProvider.GetRequiredKeyedService<IChatClient>("test-service");

        // Assert
        Assert.NotNull(service);
    }

    [Fact]
    public void AddOnnxRuntimeGenAIChatClientToKernelBuilderWithServiceId()
    {
        // Arrange
        var collection = new ServiceCollection();
        var kernelBuilder = collection.AddKernel();
        kernelBuilder.AddOnnxRuntimeGenAIChatClient("modelId", "modelPath", "test-service");

        // Act
        var serviceProvider = collection.BuildServiceProvider();
        var kernel = serviceProvider.GetRequiredService<Kernel>();
        var service = serviceProvider.GetRequiredKeyedService<IChatClient>("test-service");

        // Assert
        Assert.NotNull(service);
    }
}
