// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

/// <summary>
/// Unit tests for <see cref="AutoFunctionChoiceBehavior"/>
/// </summary>
public sealed class AutoFunctionChoiceBehaviorTests
{
    private readonly Kernel _kernel;

    public AutoFunctionChoiceBehaviorTests()
    {
        this._kernel = new Kernel();
    }

    [Fact]
    public void ItShouldAdvertiseKernelFunctionsAsAvailableOnes()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new AutoFunctionChoiceBehavior();

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Null(config.RequiredFunctions);

        Assert.NotNull(config.AvailableFunctions);
        Assert.Equal(3, config.AvailableFunctions.Count());
        Assert.Contains(config.AvailableFunctions, f => f.Name == "Function1");
        Assert.Contains(config.AvailableFunctions, f => f.Name == "Function2");
        Assert.Contains(config.AvailableFunctions, f => f.Name == "Function3");
    }

    [Fact]
    public void ItShouldAdvertiseFunctionsProvidedAsInstancesAsAvailableOnes()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new AutoFunctionChoiceBehavior(functions: [plugin.ElementAt(0), plugin.ElementAt(1)]);

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Null(config.RequiredFunctions);

        Assert.NotNull(config.AvailableFunctions);
        Assert.Equal(2, config.AvailableFunctions.Count());
        Assert.Contains(config.AvailableFunctions, f => f.Name == "Function1");
        Assert.Contains(config.AvailableFunctions, f => f.Name == "Function2");
    }

    [Fact]
    public void ItShouldAdvertiseFunctionsProvidedAsFunctionFQNsAsAvailableOnes()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new AutoFunctionChoiceBehavior()
        {
            Functions = ["MyPlugin.Function1", "MyPlugin.Function2"]
        };

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Null(config.RequiredFunctions);

        Assert.NotNull(config.AvailableFunctions);
        Assert.Equal(2, config.AvailableFunctions.Count());
        Assert.Contains(config.AvailableFunctions, f => f.Name == "Function1");
        Assert.Contains(config.AvailableFunctions, f => f.Name == "Function2");
    }

    [Fact]
    public void ItShouldHaveFiveMaxAutoInvokeAttemptsByDefault()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new AutoFunctionChoiceBehavior();

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.Equal(5, config.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void ItShouldAllowAutoInvocation()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new AutoFunctionChoiceBehavior()
        {
            MaximumAutoInvokeAttempts = 8
        };

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.Equal(8, config.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void ItShouldAllowManualInvocation()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new AutoFunctionChoiceBehavior()
        {
            MaximumAutoInvokeAttempts = 0
        };

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.Equal(0, config.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void ItShouldThrowExceptionIfFunctionProvidedAsInstancesAndAsFunctionFQNsAtTheSameTime()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var exception = Assert.Throws<KernelException>(() =>
        {
            var choiceBehavior = new AutoFunctionChoiceBehavior(functions: [plugin.ElementAt(0), plugin.ElementAt(1)])
            {
                Functions = ["MyPlugin.Function1"]
            };
        });

        Assert.Equal("Functions are already provided via the constructor.", exception.Message);
    }

    [Fact]
    public void ItShouldThrowExceptionIfAutoInvocationRequestedButNoKernelIsProvided()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        var choiceBehavior = new AutoFunctionChoiceBehavior()
        {
            MaximumAutoInvokeAttempts = 8
        };

        // Act
        var exception = Assert.Throws<KernelException>(() =>
        {
            choiceBehavior.GetConfiguration(new() { Kernel = null });
        });

        Assert.Equal("Auto-invocation for Auto choice behavior is not supported when no kernel is provided.", exception.Message);
    }

    [Fact]
    public void ItShouldThrowExceptionIfAutoInvocationRequestedAndFunctionIsNotRegisteredInKernel()
    {
        // Arrange
        var plugin = GetTestPlugin();

        var choiceBehavior = new AutoFunctionChoiceBehavior([plugin.ElementAt(0)])
        {
            MaximumAutoInvokeAttempts = 5
        };

        // Act
        var exception = Assert.Throws<KernelException>(() =>
        {
            choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });
        });

        Assert.Equal("The specified function MyPlugin.Function1 is not available in the kernel.", exception.Message);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ItShouldThrowExceptionIfFunctionProvidedAsFunctionFQNIsNotRegisteredInKernel(bool autoInvoke)
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        var choiceBehavior = new AutoFunctionChoiceBehavior()
        {
            MaximumAutoInvokeAttempts = autoInvoke ? 5 : 0,
            Functions = ["MyPlugin.NonKernelFunction"]
        };

        // Act
        var exception = Assert.Throws<KernelException>(() =>
        {
            choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });
        });

        Assert.Equal("The specified function MyPlugin.NonKernelFunction is not available in the kernel.", exception.Message);
    }

    [Fact]
    public void ItShouldAllowToInvokeAnyRequestedKernelFunctionForKernelFunctions()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new AutoFunctionChoiceBehavior();

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.True(config.AllowAnyRequestedKernelFunction);
    }

    [Fact]
    public void ItShouldNotAllowInvokingAnyRequestedKernelFunctionForProvidedAsInstancesFunctions()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new AutoFunctionChoiceBehavior(functions: [plugin.ElementAt(1)]);

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.False(config.AllowAnyRequestedKernelFunction);
    }

    [Fact]
    public void ItShouldNotAllowInvokingAnyRequestedKernelFunctionForFunctionsProvidedAsFunctionFQNs()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new AutoFunctionChoiceBehavior()
        {
            Functions = ["MyPlugin.Function2"]
        };

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.False(config.AllowAnyRequestedKernelFunction);
    }

    private static KernelPlugin GetTestPlugin()
    {
        var function1 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function2");
        var function3 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function3");

        return KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2, function3]);
    }
}
