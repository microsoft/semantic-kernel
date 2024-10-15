// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;
public class KernelPluginFactoryTests
{
    [Fact]
    public async Task ItCanCreateFromObjectAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var args = new KernelArguments { { "param1", "value1" } };
        var target = new MyKernelFunctions();

        // Act
        var plugin = KernelPluginFactory.CreateFromObject(target);
        FunctionResult result = await plugin["Function1"].InvokeAsync(kernel, args);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(3, plugin.FunctionCount);
        Assert.Equal("Function1: value1", result.Value);
    }

    [Fact]
    public async Task ItCanCreateFromTypeUsingGenericsAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var args = new KernelArguments { { "param1", "value1" } };

        // Act
        var plugin = KernelPluginFactory.CreateFromType<MyKernelFunctions>();
        FunctionResult result = await plugin["Function1"].InvokeAsync(kernel, args);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(3, plugin.FunctionCount);
        Assert.Equal("Function1: value1", result.Value);
    }

    [Fact]
    public async Task ItCanCreateFromTypeAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var args = new KernelArguments { { "param1", "value1" } };
        var instanceType = typeof(MyKernelFunctions);

        // Act
        var plugin = KernelPluginFactory.CreateFromType(instanceType);
        FunctionResult result = await plugin["Function1"].InvokeAsync(kernel, args);

        // Assert
        Assert.NotNull(plugin);
        Assert.Equal(3, plugin.FunctionCount);
        Assert.Equal("Function1: value1", result.Value);
    }

    #region private
    private sealed class MyKernelFunctions
    {
        [KernelFunction("Function1")]
        [Description("Description for function 1.")]
        public string Function1([Description("Description for parameter 1")] string param1) => $"Function1: {param1}";

        [KernelFunction("Function2")]
        [Description("Description for function 2.")]
        public string Function2([Description("Description for parameter 1")] string param1) => $"Function2: {param1}";

        [KernelFunction("Function3")]
        [Description("Description for function 3.")]
        public string Function3([Description("Description for parameter 1")] string param1) => $"Function3: {param1}";
    }
    #endregion
}
