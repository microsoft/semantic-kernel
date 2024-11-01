// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
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
}
