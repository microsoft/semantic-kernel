// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;
public class KernelFunctionArgumentsTests
{
    [Fact]
    public void ItCanBeCreatedWithNoArguments()
    {
        KernelFunctionArguments kernelFunction = new() { };

        Assert.Null(kernelFunction.RequestSettings);
        Assert.Empty(kernelFunction);
    }

    [Fact]
    public void ItCanBeCreatedWithRequestSettingsOnly()
    {
        // Arrange
        var requestSettings = new AIRequestSettings();

        // Act
        KernelFunctionArguments kernelFunction = new(requestSettings) { };

        // Assert
        Assert.Equal(requestSettings, kernelFunction.RequestSettings);
        Assert.Empty(kernelFunction);
    }

    [Fact]
    public void ItCanBeCreatedWithArgumentsOnly()
    {
        // Arrange & Act
        KernelFunctionArguments kernelFunction = new() { { "fake-key", "fake-value" } };

        // Assert
        Assert.Null(kernelFunction.RequestSettings);

        var argument = Assert.Single(kernelFunction);
        Assert.Equal("fake-key", argument.Key);
        Assert.Equal("fake-value", argument.Value);
    }

    [Fact]
    public void ItCanBeCreatedWithBothRequestSettingsAndArguments()
    {
        // Arrange
        var requestSettings = new AIRequestSettings();

        // Act
        KernelFunctionArguments kernelFunction = new(requestSettings) { { "fake-key", "fake-value" } };

        // Assert
        Assert.Equal(requestSettings, kernelFunction.RequestSettings);

        var argument = Assert.Single(kernelFunction);
        Assert.Equal("fake-key", argument.Key);
        Assert.Equal("fake-value", argument.Value);
    }
}
