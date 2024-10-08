// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.AI.FunctionChoiceBehaviors;

/// <summary>
/// Unit tests for <see cref="NoneFunctionChoiceBehavior"/>
/// </summary>
public sealed class NoneFunctionChoiceBehaviorTests
{
    private readonly Kernel _kernel;

    public NoneFunctionChoiceBehaviorTests()
    {
        this._kernel = new Kernel();
    }

    [Fact]
    public void ItShouldAdvertiseKernelFunctions()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new NoneFunctionChoiceBehavior();

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
    public void ItShouldAdvertiseFunctionsIfSpecified()
    {
        // Arrange
        var plugin = GetTestPlugin();

        // Act
        var choiceBehavior = new NoneFunctionChoiceBehavior([plugin.ElementAt(0), plugin.ElementAt(2)]);

        var config = choiceBehavior.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.NotNull(config.Functions);
        Assert.Equal(2, config.Functions.Count);
        Assert.Contains(config.Functions, f => f.Name == "Function1");
        Assert.Contains(config.Functions, f => f.Name == "Function3");
    }

    [Fact]
    public void ItShouldNotAllowAutoInvocation()
    {
        // Arrange
        var choiceBehavior = new NoneFunctionChoiceBehavior();

        // Act
        var config = choiceBehavior.GetConfiguration(new(chatHistory: []) { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);
        Assert.False(config.AutoInvoke);
    }

    [Fact]
    public void ItShouldPropagateOptionsToConfiguration()
    {
        // Arrange
        var options = new FunctionChoiceBehaviorOptions();

        // Act
        var choiceBehavior = new NoneFunctionChoiceBehavior(options: options);

        // Assert
        var configuration = choiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext(chatHistory: []));

        Assert.Same(options, configuration.Options);
    }

    [Fact]
    public void ItShouldPropagateDefaultOptionsIfNoneAreProvided()
    {
        // Arrange & Act
        var choiceBehavior = new NoneFunctionChoiceBehavior(options: null);

        // Assert
        var configuration = choiceBehavior.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext(chatHistory: []));

        Assert.NotNull(configuration.Options);
    }

    private static KernelPlugin GetTestPlugin()
    {
        var function1 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function2");
        var function3 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function3");

        return KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2, function3]);
    }
}
