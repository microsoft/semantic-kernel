// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using static Microsoft.SemanticKernel.Connectors.OpenAI.ToolCallBehavior;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// Unit tests for <see cref="ToolCallBehavior"/>
/// </summary>
public sealed class ToolCallBehaviorTests
{
    [Fact]
    public void EnableKernelFunctionsReturnsCorrectKernelFunctionsInstance()
    {
        // Arrange & Act
        var behavior = ToolCallBehavior.EnableKernelFunctions;

        // Assert
        Assert.IsType<KernelFunctions>(behavior);
        Assert.Equal(0, behavior.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void AutoInvokeKernelFunctionsReturnsCorrectKernelFunctionsInstance()
    {
        // Arrange & Act
        const int DefaultMaximumAutoInvokeAttempts = 128;
        var behavior = ToolCallBehavior.AutoInvokeKernelFunctions;

        // Assert
        Assert.IsType<KernelFunctions>(behavior);
        Assert.Equal(DefaultMaximumAutoInvokeAttempts, behavior.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void EnableFunctionsReturnsEnabledFunctionsInstance()
    {
        // Arrange & Act
        List<OpenAIFunction> functions = [new("Plugin", "Function", "description", [], null)];
        var behavior = ToolCallBehavior.EnableFunctions(functions);

        // Assert
        Assert.IsType<EnabledFunctions>(behavior);
    }

    [Fact]
    public void RequireFunctionReturnsRequiredFunctionInstance()
    {
        // Arrange & Act
        var behavior = ToolCallBehavior.RequireFunction(new("Plugin", "Function", "description", [], null));

        // Assert
        Assert.IsType<RequiredFunction>(behavior);
    }

    [Fact]
    public void KernelFunctionsConfigureOptionsWithNullKernelDoesNotAddTools()
    {
        // Arrange
        var kernelFunctions = new KernelFunctions(autoInvoke: false);

        // Act
        var config = kernelFunctions.GetConfiguration(new());

        // Assert
        Assert.Null(config.FunctionsMetadata);
    }

    [Fact]
    public void KernelFunctionsConfigureOptionsWithoutFunctionsDoesNotAddTools()
    {
        // Arrange
        var kernelFunctions = new KernelFunctions(autoInvoke: false);
        var kernel = Kernel.CreateBuilder().Build();

        // Act
        var config = kernelFunctions.GetConfiguration(new() { Kernel = kernel });

        // Assert
        Assert.Equal(FunctionChoice.Auto, config.Choice);
        Assert.Null(config.FunctionsMetadata);
    }

    [Fact]
    public void KernelFunctionsConfigureOptionsWithFunctionsAddsTools()
    {
        // Arrange
        var kernelFunctions = new KernelFunctions(autoInvoke: false);
        var kernel = Kernel.CreateBuilder().Build();

        var plugin = this.GetTestPlugin();

        kernel.Plugins.Add(plugin);

        // Act
        var config = kernelFunctions.GetConfiguration(new() { Kernel = kernel });

        // Assert
        Assert.Equal(FunctionChoice.Auto, config.Choice);

        this.AssertFunctions(config.FunctionsMetadata);
    }

    [Fact]
    public void EnabledFunctionsConfigureOptionsWithoutFunctionsDoesNotAddTools()
    {
        // Arrange
        var enabledFunctions = new EnabledFunctions([], autoInvoke: false);

        // Act
        var config = enabledFunctions.GetConfiguration(new());

        // Assert
        Assert.Equal(FunctionChoice.Auto, config.Choice);
        Assert.Null(config.FunctionsMetadata);
    }

    [Fact]
    public void EnabledFunctionsConfigureOptionsWithAutoInvokeAndNullKernelThrowsException()
    {
        // Arrange
        var functions = this.GetTestPlugin().GetFunctionsMetadata().Select(function => function.ToOpenAIFunction());
        var enabledFunctions = new EnabledFunctions(functions, autoInvoke: true);

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => enabledFunctions.GetConfiguration(new()));
        Assert.Equal($"Auto-invocation with {nameof(EnabledFunctions)} is not supported when no kernel is provided.", exception.Message);
    }

    [Fact]
    public void EnabledFunctionsConfigureOptionsWithAutoInvokeAndEmptyKernelThrowsException()
    {
        // Arrange
        var functions = this.GetTestPlugin().GetFunctionsMetadata().Select(function => function.ToOpenAIFunction());
        var enabledFunctions = new EnabledFunctions(functions, autoInvoke: true);
        var kernel = Kernel.CreateBuilder().Build();

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => enabledFunctions.GetConfiguration(new() { Kernel = kernel }));
        Assert.Equal($"The specified {nameof(EnabledFunctions)} function MyPlugin-MyFunction is not available in the kernel.", exception.Message);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void EnabledFunctionsConfigureOptionsWithKernelAndPluginsAddsTools(bool autoInvoke)
    {
        // Arrange
        var plugin = this.GetTestPlugin();
        var functions = plugin.GetFunctionsMetadata().Select(function => function.ToOpenAIFunction());
        var enabledFunctions = new EnabledFunctions(functions, autoInvoke);
        var kernel = Kernel.CreateBuilder().Build();

        kernel.Plugins.Add(plugin);

        // Act
        var config = enabledFunctions.GetConfiguration(new() { Kernel = kernel });

        // Assert
        Assert.Equal(FunctionChoice.Auto, config.Choice);
        this.AssertFunctions(config.FunctionsMetadata);
    }

    [Fact]
    public void RequiredFunctionsConfigureOptionsWithAutoInvokeAndNullKernelThrowsException()
    {
        // Arrange
        var function = this.GetTestPlugin().GetFunctionsMetadata().Select(function => function.ToOpenAIFunction()).First();
        var requiredFunction = new RequiredFunction(function, autoInvoke: true);

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => requiredFunction.GetConfiguration(new()));
        Assert.Equal($"Auto-invocation with {nameof(RequiredFunction)} is not supported when no kernel is provided.", exception.Message);
    }

    [Fact]
    public void RequiredFunctionsConfigureOptionsWithAutoInvokeAndEmptyKernelThrowsException()
    {
        // Arrange
        var function = this.GetTestPlugin().GetFunctionsMetadata().Select(function => function.ToOpenAIFunction()).First();
        var requiredFunction = new RequiredFunction(function, autoInvoke: true);
        var kernel = Kernel.CreateBuilder().Build();

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => requiredFunction.GetConfiguration(new() { Kernel = kernel }));
        Assert.Equal($"The specified {nameof(RequiredFunction)} function MyPlugin-MyFunction is not available in the kernel.", exception.Message);
    }

    [Fact]
    public void RequiredFunctionConfigureOptionsAddsTools()
    {
        // Arrange
        var plugin = this.GetTestPlugin();
        var function = plugin.GetFunctionsMetadata()[0].ToOpenAIFunction();
        var requiredFunction = new RequiredFunction(function, autoInvoke: true);
        var kernel = new Kernel();
        kernel.Plugins.Add(plugin);

        // Act
        var config = requiredFunction.GetConfiguration(new() { Kernel = kernel });

        // Assert
        Assert.NotNull(config.FunctionsMetadata);

        this.AssertFunctions(config.FunctionsMetadata);
    }

    private KernelPlugin GetTestPlugin()
    {
        var function = KernelFunctionFactory.CreateFromMethod(
            (string parameter1, string parameter2) => "Result1",
            "MyFunction",
            "Test Function",
            [new KernelParameterMetadata("parameter1"), new KernelParameterMetadata("parameter2")],
            new KernelReturnParameterMetadata { ParameterType = typeof(string), Description = "Function Result" });

        return KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);
    }

    private void AssertFunctions(IEnumerable<KernelFunctionMetadata>? functions)
    {
        Assert.NotNull(functions);

        var function = Assert.Single(functions);

        Assert.NotNull(function);

        Assert.Equal("MyPlugin", function.PluginName);
        Assert.Equal("MyFunction", function.Name);
        Assert.Equal("Test Function", function.Description);

        Assert.NotNull(function.Parameters);
        Assert.Equal(2, function.Parameters.Count);

        Assert.Equal("parameter1", function.Parameters[0].Name);
        Assert.Equal("parameter2", function.Parameters[1].Name);

        Assert.NotNull(function.ReturnParameter);
        Assert.Equal("Function Result", function.ReturnParameter.Description);
    }
}
