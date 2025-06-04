// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

/// <summary>
/// Unit tests for <see cref="FunctionChoiceBehavior"/>
/// </summary>
public sealed class FunctionChoiceBehaviorTests
{
    private readonly Kernel _kernel;

    public FunctionChoiceBehaviorTests()
    {
        this._kernel = new Kernel();
    }

    [Fact]
    public void AutoFunctionChoiceShouldBeUsed()
    {
        // Act
        var choiceBehavior = FunctionChoiceBehavior.Auto();

        // Assert
        Assert.IsType<AutoFunctionChoiceBehavior>(choiceBehavior);
    }

    [Fact]
    public void RequiredFunctionChoiceShouldBeUsed()
    {
        // Act
        var choiceBehavior = FunctionChoiceBehavior.Required();

        // Assert
        Assert.IsType<RequiredFunctionChoiceBehavior>(choiceBehavior);
    }

    [Fact]
    public void NoneFunctionChoiceShouldBeUsed()
    {
        // Act
        var choiceBehavior = FunctionChoiceBehavior.None();

        // Assert
        Assert.IsType<NoneFunctionChoiceBehavior>(choiceBehavior);
    }

    [Fact]
    public void AutoFunctionChoiceShouldAdvertiseKernelFunctions()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = FunctionChoiceBehavior.Auto(functions: null);

        var config = choiceBehavior.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.NotNull(config.Functions);
        Assert.Equal(3, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.Name == "Function2");
        Assert.Contains(config.Functions, f => f.Name == "Function3");
    }

    [Fact]
    public void AutoFunctionChoiceShouldAdvertiseProvidedFunctions()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = FunctionChoiceBehavior.Auto(functions: [plugin.ElementAt(0), plugin.ElementAt(1)]);

        var config = choiceBehavior.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.NotNull(config.Functions);
        Assert.Equal(2, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.Name == "Function2");
    }

    [Fact]
    public void AutoFunctionChoiceShouldAllowAutoInvocation()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: true);

        var config = choiceBehavior.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.True(config.AutoInvoke);
    }

    [Fact]
    public void AutoFunctionChoiceShouldAllowManualInvocation()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false);

        var config = choiceBehavior.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.False(config.AutoInvoke);
    }

    [Fact]
    public void RequiredFunctionChoiceShouldAdvertiseKernelFunctions()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = FunctionChoiceBehavior.Required(functions: null);

        var config = choiceBehavior.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.NotNull(config.Functions);
        Assert.Equal(3, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.Name == "Function2");
        Assert.Contains(config.Functions, f => f.Name == "Function3");
    }

    [Fact]
    public void RequiredFunctionChoiceShouldAdvertiseProvidedFunctions()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = FunctionChoiceBehavior.Required(functions: [plugin.ElementAt(0), plugin.ElementAt(1)]);

        var config = choiceBehavior.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.NotNull(config.Functions);
        Assert.Equal(2, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.Name == "Function2");
    }

    [Fact]
    public void RequiredFunctionChoiceShouldAllowAutoInvocation()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = FunctionChoiceBehavior.Required(autoInvoke: true);

        var config = choiceBehavior.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.True(config.AutoInvoke);
    }

    //[Fact]
    //This test should be uncommented when the solution to dynamically control list of functions to advertise to the model is implemented.
    //public void RequiredFunctionChoiceShouldReturnNoFunctionAsSpecifiedByFunctionsSelector()
    //{
    //    // Arrange
    //    var plugin = GetTestPlugin();
    //    this._kernel.Plugins.Add(plugin);

    //    static IReadOnlyList<KernelFunction>? FunctionsSelector(FunctionChoiceBehaviorFunctionsSelectorContext context)
    //    {
    //        return [];
    //    }

    //    // Act
    //    var choiceBehavior = FunctionChoiceBehavior.Required(autoInvoke: true, functionsSelector: FunctionsSelector);

    //    var config = choiceBehavior.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

    //    // Assert
    //    Assert.NotNull(config.Functions);
    //    Assert.Empty(config.Functions);
    //}

    //[Fact]
    //This test should be uncommented when the solution to dynamically control the list of functions to advertise to the model is implemented.
    //public void RequiredFunctionChoiceShouldReturnFunctionsAsSpecifiedByFunctionsSelector()
    //{
    //    // Arrange
    //    var plugin = GetTestPlugin();
    //    this._kernel.Plugins.Add(plugin);

    //    static IReadOnlyList<KernelFunction>? FunctionsSelector(FunctionChoiceBehaviorFunctionsSelectorContext context)
    //    {
    //        return context.Functions!.Where(f => f.Name == "Function1").ToList();
    //    }

    //    // Act
    //    var choiceBehavior = FunctionChoiceBehavior.Required(autoInvoke: true, functionsSelector: FunctionsSelector);

    //    var config = choiceBehavior.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

    //    // Assert
    //    Assert.NotNull(config?.Functions);
    //    Assert.Single(config.Functions);
    //    Assert.Equal("Function1", config.Functions[0].Name);
    //}

    [Fact]
    public void RequiredFunctionChoiceShouldAllowManualInvocation()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = FunctionChoiceBehavior.Required(autoInvoke: false);

        var config = choiceBehavior.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.False(config.AutoInvoke);
    }

    [Fact]
    public void NoneFunctionChoiceShouldAdvertiseProvidedFunctions()
    {
        // Arrange
        var plugin = GetTestPlugin();

        // Act
        var choiceBehavior = FunctionChoiceBehavior.None([plugin.ElementAt(0), plugin.ElementAt(2)]);

        var config = choiceBehavior.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.NotNull(config.Functions);
        Assert.Equal(2, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.Name == "Function3");
    }

    [Fact]
    public void NoneFunctionChoiceShouldAdvertiseAllKernelFunctions()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = FunctionChoiceBehavior.None();

        var config = choiceBehavior.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.NotNull(config.Functions);
        Assert.Equal(3, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.Name == "Function2");
        Assert.Contains(config.Functions, f => f.Name == "Function3");
    }

    [Fact]
    public void FunctionChoiceBehaviorShouldPassOptionsToAutoFunctionChoiceBehaviorClass()
    {
        // Arrange
        var options = new FunctionChoiceBehaviorOptions();

        // Act
        var choiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false, options: options);

        // Assert
        var configuration = choiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext(chatHistory: []));

        Assert.Same(options, configuration.Options);
    }

    [Fact]
    public void FunctionChoiceBehaviorShouldPassOptionsToRequiredFunctionChoiceBehaviorClass()
    {
        // Arrange
        var options = new FunctionChoiceBehaviorOptions();

        // Act
        var choiceBehavior = FunctionChoiceBehavior.Required(autoInvoke: false, options: options);

        // Assert
        var configuration = choiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext(chatHistory: []));

        Assert.Same(options, configuration.Options);
    }

    [Fact]
    public void FunctionChoiceBehaviorShouldPassOptionsToNoneFunctionChoiceBehaviorClass()
    {
        // Arrange
        var options = new FunctionChoiceBehaviorOptions();

        // Act
        var choiceBehavior = FunctionChoiceBehavior.None(options: options);

        // Assert
        var configuration = choiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext(chatHistory: []));

        Assert.Same(options, configuration.Options);
    }

    private static KernelPlugin GetTestPlugin()
    {
        var function1 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function2");
        var function3 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function3");

        return KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2, function3]);
    }
}
