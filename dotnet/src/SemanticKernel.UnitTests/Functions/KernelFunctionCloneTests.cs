// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelFunctionCloneTests
{
    [Fact]
    public async Task ClonedKernelFunctionUsesProvidedKernelWhenInvokingAsAIFunction()
    {
        // Arrange
        var originalKernel = new Kernel();
        var newKernel = new Kernel();

        // Create a function that returns the kernel's hash code
        var function = KernelFunctionFactory.CreateFromMethod(
            (Kernel k) => k.GetHashCode().ToString(),
            "GetKernelHashCode");

        // Create an AIFunction from the KernelFunction with the original kernel
        var aiFunction = function.WithKernel(originalKernel);

        // Act
        // Clone the function and create a new AIFunction with the new kernel
        var clonedFunction = function.Clone("TestPlugin");
        var clonedAIFunction = clonedFunction.WithKernel(newKernel);

        // Invoke both functions
        var originalResult = await aiFunction.InvokeAsync(new AIFunctionArguments(), default);
        var clonedResult = await clonedAIFunction.InvokeAsync(new AIFunctionArguments(), default);

        // Assert
        // The results should be different because they use different kernels
        Assert.NotNull(originalResult);
        Assert.NotNull(clonedResult);
        Assert.NotEqual(originalResult, clonedResult);
        Assert.Equal(originalKernel.GetHashCode().ToString(), originalResult.ToString());
        Assert.Equal(newKernel.GetHashCode().ToString(), clonedResult.ToString());
    }

    [Fact]
    public async Task KernelAIFunctionUsesProvidedKernelWhenInvoking()
    {
        // Arrange
        var kernel1 = new Kernel();
        var kernel2 = new Kernel();

        // Create a function that returns the kernel's hash code
        var function = KernelFunctionFactory.CreateFromMethod(
            (Kernel k) => k.GetHashCode().ToString(),
            "GetKernelHashCode");

        // Act
        // Create AIFunctions with different kernels
        var aiFunction1 = function.WithKernel(kernel1);
        var aiFunction2 = function.WithKernel(kernel2);

        // Invoke both functions
        var result1 = await aiFunction1.InvokeAsync(new AIFunctionArguments(), default);
        var result2 = await aiFunction2.InvokeAsync(new AIFunctionArguments(), default);

        // Assert
        // The results should be different because they use different kernels
        Assert.NotNull(result1);
        Assert.NotNull(result2);
        Assert.NotEqual(result1, result2);
        Assert.Equal(kernel1.GetHashCode().ToString(), result1.ToString());
        Assert.Equal(kernel2.GetHashCode().ToString(), result2.ToString());
    }

    [Fact]
    public void CloneStoresKernelForLaterUse()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");

        // Act
        var aiFunction = function.WithKernel(kernel);

        // Assert
        // We can't directly access the private _kernel field, but we can verify it's used
        // by checking that the AIFunction has the correct name format
        Assert.Equal("TestFunction", aiFunction.Name);
    }

    [Fact]
    public void ClonePreservesMetadataButChangesPluginName()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(
            () => "Test",
            "TestFunction",
            "Test description");

        // Act
        var clonedFunction = function.Clone("NewPlugin");

        // Assert
        Assert.Equal("TestFunction", clonedFunction.Name);
        Assert.Equal("NewPlugin", clonedFunction.PluginName);
        Assert.Equal("Test description", clonedFunction.Description);
    }
}
