// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

/// <summary>
/// Tests for <see cref="KernelFunction"/> cloning with a <see cref="Kernel"/> instance.
/// </summary>
public class KernelFunctionTests
{
    private readonly Mock<ILoggerFactory> _loggerFactory = new();

    [Fact]
    public async Task ClonedFunctionWithKernelUsesProvidedKernelWhenInvokedWithoutKernel()
    {
        // Arrange
        // Create a function that will return the kernel's ID
        var function = KernelFunctionFactory.CreateFromMethod(
            (Kernel kernel) => kernel.Data.TryGetValue("id", out var id) ? id?.ToString() ?? string.Empty : string.Empty,
            functionName: "GetKernelId",
            description: "Gets the ID of the kernel used for invocation",
            loggerFactory: this._loggerFactory.Object);

        // Create two kernels with different IDs
        var kernel1 = new Kernel();
        kernel1.Data["id"] = "kernel1";

        var kernel2 = new Kernel();
        kernel2.Data["id"] = "kernel2";

        // Clone the function with kernel2
        var clonedFunction = function.WithKernel(kernel2);

        // Act
        // Invoke the cloned function without providing a kernel
        var result = await clonedFunction.InvokeAsync();

        // Assert
        // The function should have used kernel2
        Assert.NotNull(result);
        Assert.Equal("kernel2", result.ToString());
    }

    [Fact]
    public async Task ClonedFunctionWithKernelUsesProvidedKernelWhenInvokedWithNullKernel()
    {
        // Arrange
        // Create a function that will return the kernel's ID
        var function = KernelFunctionFactory.CreateFromMethod(
            (Kernel kernel) => kernel.Data["id"]!.ToString(),
            functionName: "GetKernelId",
            description: "Gets the ID of the kernel used for invocation",
            loggerFactory: this._loggerFactory.Object);

        // Create two kernels with different IDs
        var kernel1 = new Kernel();
        kernel1.Data["id"] = "kernel1";

        var kernel2 = new Kernel();
        kernel2.Data["id"] = "kernel2";

        // Clone the function with kernel2
        var clonedFunction = function.WithKernel(kernel2);

        // Act
        // Invoke the cloned function with null kernel
        var result = await clonedFunction.InvokeAsync(kernel: null!);

        // Assert
        // The function should have used kernel2
        Assert.Equal("kernel2", result.GetValue<string>());
    }

    [Fact]
    public async Task ClonedFunctionWithKernelUsesExplicitKernelWhenProvidedInInvoke()
    {
        // Arrange
        // Create a function that will return the kernel's ID
        var function = KernelFunctionFactory.CreateFromMethod(
            (Kernel kernel) => kernel.Data.TryGetValue("id", out var id) ? id?.ToString() ?? string.Empty : string.Empty,
            functionName: "GetKernelId",
            description: "Gets the ID of the kernel used for invocation",
            loggerFactory: this._loggerFactory.Object);

        // Create two kernels with different IDs
        var kernel1 = new Kernel();
        kernel1.Data["id"] = "kernel1";

        var kernel2 = new Kernel();
        kernel2.Data["id"] = "kernel2";

        // Clone the function with kernel2
        var clonedFunction = function.WithKernel(kernel2);

        // Act
        // Invoke the cloned function with kernel1 explicitly
        var result = await clonedFunction.InvokeAsync(kernel: kernel1);

        // Assert
        // The function should have used kernel1, not kernel2
        Assert.Equal("kernel1", result.GetValue<string>());
    }

    [Fact]
    public async Task ClonedFunctionWithKernelUsesProvidedKernelWhenInvokedWithArguments()
    {
        // Arrange
        // Create a function that will return the kernel's ID
        var function = KernelFunctionFactory.CreateFromMethod(
            (Kernel kernel) => kernel.Data.TryGetValue("id", out var id) ? id?.ToString() ?? string.Empty : string.Empty,
            functionName: "GetKernelId",
            description: "Gets the ID of the kernel used for invocation",
            loggerFactory: this._loggerFactory.Object);

        // Create two kernels with different IDs
        var kernel1 = new Kernel();
        kernel1.Data["id"] = "kernel1";

        var kernel2 = new Kernel();
        kernel2.Data["id"] = "kernel2";

        // Clone the function with kernel2
        var clonedFunction = function.WithKernel(kernel2);

        // Act
        // Invoke the cloned function with just arguments
        var result = await clonedFunction.InvokeAsync();

        // Assert
        // The function should have used kernel2
        Assert.NotNull(result);
        Assert.Equal("kernel2", result.ToString());
    }

    [Fact]
    public async Task ClonedFunctionWithKernelUsesExplicitKernelWhenProvidedInArguments()
    {
        // Arrange
        // Create a function that will return the kernel's ID
        var function = KernelFunctionFactory.CreateFromMethod(
            (Kernel kernel) => kernel.Data["id"]!.ToString(),
            functionName: "GetKernelId",
            description: "Gets the ID of the kernel used for invocation",
            loggerFactory: this._loggerFactory.Object);

        // Create two kernels with different IDs
        var kernel1 = new Kernel();
        kernel1.Data["id"] = "kernel1";

        var kernel2 = new Kernel();
        kernel2.Data["id"] = "kernel2";

        // Clone the function with kernel2
        var clonedFunction = function.WithKernel(kernel2);

        // Act
        // Invoke the cloned function with kernel1 explicitly
        var result = await clonedFunction.InvokeAsync(kernel1, new KernelArguments());

        // Assert
        // The function should have used kernel1, not kernel2
        Assert.Equal("kernel1", result.GetValue<string>());
    }

    [Fact]
    public async Task NonClonedFunctionThrowsExceptionWhenInvokedWithNullKernel()
    {
        // Arrange
        // Create a function that will return the kernel's ID
        var function = KernelFunctionFactory.CreateFromMethod(
            (Kernel kernel) => kernel.Data.TryGetValue("id", out var id) ? id?.ToString() ?? string.Empty : string.Empty,
            functionName: "GetKernelId",
            description: "Gets the ID of the kernel used for invocation",
            loggerFactory: this._loggerFactory.Object);

        // Act & Assert
        // Invoke the function with null kernel (without cloning it first)
        // This should throw an ArgumentNullException because the function requires a kernel and none is provided
        var exception = await Assert.ThrowsAsync<ArgumentNullException>(
            async () => await function.InvokeAsync(kernel: null!));

        // Verify the exception parameter name is 'kernel'
        Assert.Equal("kernel", exception.ParamName);
    }
}
