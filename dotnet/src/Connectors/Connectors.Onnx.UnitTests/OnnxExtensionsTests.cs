// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.ML.OnnxRuntimeGenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Onnx;
using Xunit;

namespace SemanticKernel.Connectors.Onnx.UnitTests;

/// <summary>
/// Unit tests for <see cref="OnnxKernelBuilderExtensions"/>.
/// </summary>
public class OnnxExtensionsTests
{
    [Fact]
    public void AddOnnxRuntimeGenAIChatCompletionToServiceCollection()
    {
        // Arrange
        var collection = new ServiceCollection();
        collection.AddOnnxRuntimeGenAIChatCompletion("modelId", "modelPath");

        // Act
        var kernelBuilder = collection.AddKernel();
        var kernel = collection.BuildServiceProvider().GetRequiredService<Kernel>();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Assert
        Assert.NotNull(service);
        Assert.IsType<OnnxRuntimeGenAIChatCompletionService>(service);
    }

    [Fact]
    public void AddOnnxRuntimeGenAIChatCompletionToKernelBuilder()
    {
        // Arrange
        var collection = new ServiceCollection();
        var kernelBuilder = collection.AddKernel();
        kernelBuilder.AddOnnxRuntimeGenAIChatCompletion("modelId", "modelPath");

        // Act
        var kernel = collection.BuildServiceProvider().GetRequiredService<Kernel>();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Assert
        Assert.NotNull(service);
        Assert.IsType<OnnxRuntimeGenAIChatCompletionService>(service);
    }

    [Fact]
    public void AddOnnxRuntimeGenAIChatCompletionWithProvidersToServiceCollection()
    {
        // Arrange
        var collection = new ServiceCollection();
        var providers = new List<Provider> { new("cuda"), new("cpu") };
        collection.AddOnnxRuntimeGenAIChatCompletion("modelId", "modelPath", providers);

        // Act
        var serviceDescriptor = collection.FirstOrDefault(x => x.ServiceType == typeof(IChatCompletionService));

        // Assert
        Assert.NotNull(serviceDescriptor);
        Assert.Equal(ServiceLifetime.Singleton, serviceDescriptor.Lifetime);
        Assert.NotNull(serviceDescriptor.ImplementationFactory);
    }

    [Fact]
    public void AddOnnxRuntimeGenAIChatCompletionWithProvidersToKernelBuilder()
    {
        // Arrange
        var collection = new ServiceCollection();
        var kernelBuilder = collection.AddKernel();
        var providers = new List<Provider> { new("cuda"), new("cpu") };
        kernelBuilder.AddOnnxRuntimeGenAIChatCompletion("modelId", "modelPath", providers);

        // Act
        var serviceDescriptor = collection.FirstOrDefault(x => x.ServiceType == typeof(IChatCompletionService));

        // Assert
        Assert.NotNull(serviceDescriptor);
        Assert.Equal(ServiceLifetime.Singleton, serviceDescriptor.Lifetime);
        Assert.NotNull(serviceDescriptor.ImplementationFactory);
    }

    [Fact]
    public void AddOnnxRuntimeGenAIChatCompletionWithProvidersAndServiceIdToServiceCollection()
    {
        // Arrange
        var collection = new ServiceCollection();
        var providers = new List<Provider> { new("cuda") };
        collection.AddOnnxRuntimeGenAIChatCompletion("modelId", "modelPath", providers, serviceId: "test-service");

        // Act
        var serviceProvider = collection.BuildServiceProvider();

        // Assert
        var exception = Assert.Throws<OnnxRuntimeGenAIException>(() => serviceProvider.GetRequiredKeyedService<IChatCompletionService>("test-service"));

        Assert.Contains("Error opening modelPath\\genai_config.json", exception.Message);
    }

    [Fact]
    public void AddOnnxRuntimeGenAIChatCompletionWithProvidersAndServiceIdToKernelBuilder()
    {
        // Arrange
        var collection = new ServiceCollection();
        var kernelBuilder = collection.AddKernel();
        var providers = new List<Provider> { new("cuda") };
        kernelBuilder.AddOnnxRuntimeGenAIChatCompletion("modelId", "modelPath", providers, serviceId: "test-service");

        // Act
        var serviceDescriptor = collection.FirstOrDefault(x => x.ServiceType == typeof(IChatCompletionService) && x.ServiceKey?.ToString() == "test-service");
        var serviceProvider = collection.BuildServiceProvider();

        // Assert
        var kernel = serviceProvider.GetRequiredService<Kernel>();
        var exception = Assert.Throws<OnnxRuntimeGenAIException>(() => kernel.GetRequiredService<IChatCompletionService>("test-service"));

        Assert.Contains("Error opening modelPath\\genai_config.json", exception.Message);
    }
}
