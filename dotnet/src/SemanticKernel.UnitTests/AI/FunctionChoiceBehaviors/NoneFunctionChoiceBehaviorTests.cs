// Copyright (c) Microsoft. All rights reserved.

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
    public void ItShouldAdvertiseNeitherAvailableNorRequiredFunctions()
    {
        // Arrange
        var plugin = GetTestPlugin();
        this._kernel.Plugins.Add(plugin);

        // Act
        var choiceBehavior = new NoneFunctionChoiceBehavior();

        var config = choiceBehavior.GetConfiguration(new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(config);

        Assert.Null(config.AvailableFunctions);
        Assert.Null(config.RequiredFunctions);
    }

    private static KernelPlugin GetTestPlugin()
    {
        var function1 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function2");
        var function3 = KernelFunctionFactory.CreateFromMethod(() => { }, "Function3");

        return KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2, function3]);
    }
}
