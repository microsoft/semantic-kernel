// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

/// <summary>
/// Unit tests for <see cref="RequiredFunctionChoiceBehavior"/>
/// </summary>
public sealed class RequiredFunctionChoiceBehaviorTests
{
    private readonly Kernel _kernel;

    public RequiredFunctionChoiceBehaviorTests()
    {
        this._kernel = new Kernel();
    }

    [Fact]
    public void ItShouldAdvertiseAllKernelFunctionsAsRequiredOnes()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new RequiredFunctionChoiceBehavior();

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Null(config.AvailableFunctions);

        Assert.NotNull(config.RequiredFunctions);
        Assert.Equal(3, config.RequiredFunctions.Count());
        Assert.Contains(config.RequiredFunctions, f => f.Name == "Function1");
        Assert.Contains(config.RequiredFunctions, f => f.Name == "Function2");
        Assert.Contains(config.RequiredFunctions, f => f.Name == "Function3");
    }

    [Fact]
    public void ItShouldAdvertiseOnlyFunctionsSuppliedViaConstructorAsRequiredOnes()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new RequiredFunctionChoiceBehavior(functions: [plugin.ElementAt(0), plugin.ElementAt(1)]);

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Null(config.AvailableFunctions);

        Assert.NotNull(config.RequiredFunctions);
        Assert.Equal(2, config.RequiredFunctions.Count());
        Assert.Contains(config.RequiredFunctions, f => f.Name == "Function1");
        Assert.Contains(config.RequiredFunctions, f => f.Name == "Function2");
    }

    [Fact]
    public void ItShouldAdvertiseOnlyFunctionsSuppliedInFunctionsPropertyAsRequiredOnes()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new RequiredFunctionChoiceBehavior()
        {
            Functions = ["MyPlugin-Function1", "MyPlugin-Function2"]
        };

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Null(config.AvailableFunctions);

        Assert.NotNull(config.RequiredFunctions);
        Assert.Equal(2, config.RequiredFunctions.Count());
        Assert.Contains(config.RequiredFunctions, f => f.Name == "Function1");
        Assert.Contains(config.RequiredFunctions, f => f.Name == "Function2");
    }

    [Fact]
    public void ItShouldAdvertiseOnlyFunctionsSuppliedViaConstructorAsRequiredOnesForManualInvocation()
    {
        // Arrange
        var plugin = GetTestPlugin();

        // Act
        var choiceBehavior = new RequiredFunctionChoiceBehavior(functions: [plugin.ElementAt(0), plugin.ElementAt(1)])
        {
            MaximumAutoInvokeAttempts = 0
        };

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Null(config.AvailableFunctions);

        Assert.NotNull(config.RequiredFunctions);
        Assert.Equal(2, config.RequiredFunctions.Count());
        Assert.Contains(config.RequiredFunctions, f => f.Name == "Function1");
        Assert.Contains(config.RequiredFunctions, f => f.Name == "Function2");
    }

    [Fact]
    public void ItShouldAdvertiseAllKernelFunctionsAsRequiredOnesForManualInvocation()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new RequiredFunctionChoiceBehavior()
        {
            MaximumAutoInvokeAttempts = 0
        };

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Null(config.AvailableFunctions);

        Assert.NotNull(config.RequiredFunctions);
        Assert.Equal(3, config.RequiredFunctions.Count());
        Assert.Contains(config.RequiredFunctions, f => f.Name == "Function1");
        Assert.Contains(config.RequiredFunctions, f => f.Name == "Function2");
        Assert.Contains(config.RequiredFunctions, f => f.Name == "Function3");
    }

    [Fact]
    public void ItShouldHaveFiveMaxAutoInvokeAttemptsByDefault()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new RequiredFunctionChoiceBehavior();

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
        var choiceBehavior = new RequiredFunctionChoiceBehavior()
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
        var choiceBehavior = new RequiredFunctionChoiceBehavior()
        {
            MaximumAutoInvokeAttempts = 0
        };

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.Equal(0, config.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void ItShouldInitializeFunctionPropertyByFunctionsPassedViaConstructor()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new RequiredFunctionChoiceBehavior(functions: [plugin.ElementAt(0), plugin.ElementAt(1)]);

        // Assert
        Assert.NotNull(choiceBehavior.Functions);
        Assert.Equal(2, choiceBehavior.Functions.Count);

        Assert.Equal("MyPlugin-Function1", choiceBehavior.Functions.ElementAt(0));
        Assert.Equal("MyPlugin-Function2", choiceBehavior.Functions.ElementAt(1));
    }

    [Fact]
    public void ItShouldThrowExceptionIfAutoInvocationRequestedButNoKernelIsProvided()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        var choiceBehavior = new RequiredFunctionChoiceBehavior()
        {
            MaximumAutoInvokeAttempts = 8
        };

        // Act
        var exception = Assert.Throws<KernelException>(() =>
        {
            choiceBehavior.GetConfiguration(new() { Kernel = null });
        });

        Assert.Equal("Auto-invocation for Required choice behavior is not supported when no kernel is provided.", exception.Message);
    }

    [Fact]
    public void ItShouldThrowExceptionIfAutoInvocationRequestedAndFunctionIsNotRegisteredInKernel()
    {
        // Arrange
        var plugin = GetTestPlugin();

        var choiceBehavior = new RequiredFunctionChoiceBehavior([plugin.ElementAt(0)])
        {
            MaximumAutoInvokeAttempts = 5
        };

        // Act
        var exception = Assert.Throws<KernelException>(() =>
        {
            choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });
        });

        Assert.Equal("The specified function MyPlugin-Function1 is not available in the kernel.", exception.Message);
    }

    [Fact]
    public void ItShouldThrowExceptionIfNoFunctionFoundAndManualInvocationIsRequested()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        var choiceBehavior = new RequiredFunctionChoiceBehavior()
        {
            MaximumAutoInvokeAttempts = 0,
            Functions = ["MyPlugin-NonKernelFunction"]
        };

        // Act
        var exception = Assert.Throws<KernelException>(() =>
        {
            choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });
        });

        Assert.Equal("No instance of the specified function MyPlugin-NonKernelFunction is found.", exception.Message);
    }

    [Fact]
    public void ItShouldAllowInvocationOfAnyRequestedKernelFunction()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new RequiredFunctionChoiceBehavior();

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.True(config.AllowAnyRequestedKernelFunction);
    }

    [Fact]
    public void ItShouldNotAllowInvocationOfAnyRequestedKernelFunctionIfSubsetOfFunctionsSpecified()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new RequiredFunctionChoiceBehavior(functions: [plugin.ElementAt(1)]);

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.False(config.AllowAnyRequestedKernelFunction);
    }

    [Fact]
    public void ItShouldHaveOneMaxUseAttemptsByDefault()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new RequiredFunctionChoiceBehavior();

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.Equal(1, config.MaximumUseAttempts);
    }

    [Fact]
    public void ItShouldAllowChangingMaxUseAttempts()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new RequiredFunctionChoiceBehavior()
        {
            MaximumUseAttempts = 2
        };

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.Equal(2, config.MaximumUseAttempts);
    }

    private static KernelPlugin GetTestPlugin()
    {
        var function1 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function2");
        var function3 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function3");

        return KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2, function3]);
    }
}
