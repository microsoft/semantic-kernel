// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;
using Xunit;
using static Microsoft.SemanticKernel.Connectors.OpenAI.ToolCallBehavior;

namespace SemanticKernel.Connectors.OpenAI.UnitTests;

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
        Assert.Equal($"{nameof(KernelFunctions)}(autoInvoke:{behavior.MaximumAutoInvokeAttempts != 0})", behavior.ToString());
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
        Assert.Contains($"{nameof(EnabledFunctions)}(autoInvoke:{behavior.MaximumAutoInvokeAttempts != 0})", behavior.ToString());
    }

    [Fact]
    public void RequireFunctionReturnsRequiredFunctionInstance()
    {
        // Arrange & Act
        var behavior = ToolCallBehavior.RequireFunction(new("Plugin", "Function", "description", [], null));

        // Assert
        Assert.IsType<RequiredFunction>(behavior);
        Assert.Contains($"{nameof(RequiredFunction)}(autoInvoke:{behavior.MaximumAutoInvokeAttempts != 0})", behavior.ToString());
    }

    [Fact]
    public void KernelFunctionsConfigureOptionsWithNullKernelDoesNotAddTools()
    {
        // Arrange
        var kernelFunctions = new KernelFunctions(autoInvoke: false);

        // Act
        var options = kernelFunctions.ConfigureOptions(null);

        // Assert
        Assert.Null(options.Choice);
        Assert.Null(options.Tools);
    }

    [Fact]
    public void KernelFunctionsConfigureOptionsWithoutFunctionsDoesNotAddTools()
    {
        // Arrange
        var kernelFunctions = new KernelFunctions(autoInvoke: false);
        var kernel = Kernel.CreateBuilder().Build();

        // Act
        var options = kernelFunctions.ConfigureOptions(kernel);

        // Assert
        Assert.Null(options.Choice);
        Assert.Null(options.Tools);
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
        var options = kernelFunctions.ConfigureOptions(kernel);

        // Assert
        Assert.Equal(ChatToolChoice.Auto, options.Choice);

        Assert.Equal(ChatToolChoice.Auto, options.Choice);

        Assert.NotNull(options.Choice);
        Assert.NotNull(options.Choice);
        Assert.NotNull(options.Choice);
        Assert.NotNull(options.Choice);
        this.AssertTools(options.Tools);
    }

    [Fact]
    public void EnabledFunctionsConfigureOptionsWithoutFunctionsDoesNotAddTools()
    {
        // Arrange
        var enabledFunctions = new EnabledFunctions([], autoInvoke: false);

        // Act
        var options = enabledFunctions.ConfigureOptions(null);

        // Assert
        Assert.Null(options.Choice);
        Assert.Null(options.Tools);
    }

    [Fact]
    public void EnabledFunctionsConfigureOptionsWithAutoInvokeAndNullKernelThrowsException()
    {
        // Arrange
        var functions = this.GetTestPlugin().GetFunctionsMetadata().Select(function => function.ToOpenAIFunction());
        var enabledFunctions = new EnabledFunctions(functions, autoInvoke: true);

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => enabledFunctions.ConfigureOptions(null));
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
        var exception = Assert.Throws<KernelException>(() => enabledFunctions.ConfigureOptions(kernel));
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
        var options = enabledFunctions.ConfigureOptions(kernel);

        // Assert
        Assert.Equal(ChatToolChoice.Auto, options.Choice);

        Assert.Equal(ChatToolChoice.Auto, options.Choice);

        Assert.NotNull(options.Choice);
        Assert.NotNull(options.Choice);
        Assert.NotNull(options.Choice);
        Assert.NotNull(options.Choice);
        this.AssertTools(options.Tools);
    }

    [Fact]
    public void RequiredFunctionsConfigureOptionsWithAutoInvokeAndNullKernelThrowsException()
    {
        // Arrange
        var function = this.GetTestPlugin().GetFunctionsMetadata().Select(function => function.ToOpenAIFunction()).First();
        var requiredFunction = new RequiredFunction(function, autoInvoke: true);

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => requiredFunction.ConfigureOptions(null));
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
        var exception = Assert.Throws<KernelException>(() => requiredFunction.ConfigureOptions(kernel));
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
        var options = requiredFunction.ConfigureOptions(kernel);

        // Assert
        Assert.NotNull(options.Choice);

        this.AssertTools(options.Tools);
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

    private void AssertTools(IList<ChatTool>? tools)
    {
        Assert.NotNull(tools);
        var tool = Assert.Single(tools);

        Assert.NotNull(tool);

        Assert.Equal("MyPlugin-MyFunction", tool.FunctionName);
        Assert.Equal("Test Function", tool.FunctionDescription);
        Assert.Equal("{\"type\":\"object\",\"required\":[],\"properties\":{\"parameter1\":{\"type\":\"string\"},\"parameter2\":{\"type\":\"string\"}}}", tool.FunctionParameters.ToString());
    }
}
