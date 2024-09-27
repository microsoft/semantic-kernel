// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Azure.AI.OpenAI;
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
        var behavior = ToolCallBehavior.AutoInvokeKernelFunctions;

        // Assert
        Assert.IsType<KernelFunctions>(behavior);
        Assert.Equal(5, behavior.MaximumAutoInvokeAttempts);
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
        var chatCompletionsOptions = new ChatCompletionsOptions();

        // Act
        kernelFunctions.ConfigureOptions(null, chatCompletionsOptions);

        // Assert
        Assert.Empty(chatCompletionsOptions.Tools);
    }

    [Fact]
    public void KernelFunctionsConfigureOptionsWithoutFunctionsDoesNotAddTools()
    {
        // Arrange
        var kernelFunctions = new KernelFunctions(autoInvoke: false);
        var chatCompletionsOptions = new ChatCompletionsOptions();
        var kernel = Kernel.CreateBuilder().Build();

        // Act
        kernelFunctions.ConfigureOptions(kernel, chatCompletionsOptions);

        // Assert
        Assert.Null(chatCompletionsOptions.ToolChoice);
        Assert.Empty(chatCompletionsOptions.Tools);
    }

    [Fact]
    public void KernelFunctionsConfigureOptionsWithFunctionsAddsTools()
    {
        // Arrange
        var kernelFunctions = new KernelFunctions(autoInvoke: false);
        var chatCompletionsOptions = new ChatCompletionsOptions();
        var kernel = Kernel.CreateBuilder().Build();

        var plugin = this.GetTestPlugin();

        kernel.Plugins.Add(plugin);

        // Act
        kernelFunctions.ConfigureOptions(kernel, chatCompletionsOptions);

        // Assert
        Assert.Equal(ChatCompletionsToolChoice.Auto, chatCompletionsOptions.ToolChoice);

        this.AssertTools(chatCompletionsOptions);
    }

    [Fact]
    public void EnabledFunctionsConfigureOptionsWithoutFunctionsDoesNotAddTools()
    {
        // Arrange
        var enabledFunctions = new EnabledFunctions([], autoInvoke: false);
        var chatCompletionsOptions = new ChatCompletionsOptions();

        // Act
        enabledFunctions.ConfigureOptions(null, chatCompletionsOptions);

        // Assert
        Assert.Null(chatCompletionsOptions.ToolChoice);
        Assert.Empty(chatCompletionsOptions.Tools);
    }

    [Fact]
    public void EnabledFunctionsConfigureOptionsWithAutoInvokeAndNullKernelThrowsException()
    {
        // Arrange
        var functions = this.GetTestPlugin().GetFunctionsMetadata().Select(function => function.ToOpenAIFunction());
        var enabledFunctions = new EnabledFunctions(functions, autoInvoke: true);
        var chatCompletionsOptions = new ChatCompletionsOptions();

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => enabledFunctions.ConfigureOptions(null, chatCompletionsOptions));
        Assert.Equal($"Auto-invocation with {nameof(EnabledFunctions)} is not supported when no kernel is provided.", exception.Message);
    }

    [Fact]
    public void EnabledFunctionsConfigureOptionsWithAutoInvokeAndEmptyKernelThrowsException()
    {
        // Arrange
        var functions = this.GetTestPlugin().GetFunctionsMetadata().Select(function => function.ToOpenAIFunction());
        var enabledFunctions = new EnabledFunctions(functions, autoInvoke: true);
        var chatCompletionsOptions = new ChatCompletionsOptions();
        var kernel = Kernel.CreateBuilder().Build();

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => enabledFunctions.ConfigureOptions(kernel, chatCompletionsOptions));
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
        var chatCompletionsOptions = new ChatCompletionsOptions();
        var kernel = Kernel.CreateBuilder().Build();

        kernel.Plugins.Add(plugin);

        // Act
        enabledFunctions.ConfigureOptions(kernel, chatCompletionsOptions);

        // Assert
        Assert.Equal(ChatCompletionsToolChoice.Auto, chatCompletionsOptions.ToolChoice);

        this.AssertTools(chatCompletionsOptions);
    }

    [Fact]
    public void RequiredFunctionConfigureOptionsAddsTools()
    {
        // Arrange
        var function = this.GetTestPlugin().GetFunctionsMetadata()[0].ToOpenAIFunction();
        var chatCompletionsOptions = new ChatCompletionsOptions();
        var requiredFunction = new RequiredFunction(function, autoInvoke: true);

        // Act
        requiredFunction.ConfigureOptions(null, chatCompletionsOptions);

        // Assert
        Assert.NotNull(chatCompletionsOptions.ToolChoice);

        this.AssertTools(chatCompletionsOptions);
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

    private void AssertTools(ChatCompletionsOptions chatCompletionsOptions)
    {
        Assert.Single(chatCompletionsOptions.Tools);

        var tool = chatCompletionsOptions.Tools[0] as ChatCompletionsFunctionToolDefinition;

        Assert.NotNull(tool);

        Assert.Equal("MyPlugin-MyFunction", tool.Name);
        Assert.Equal("Test Function", tool.Description);
        Assert.Equal("{\"type\":\"object\",\"required\":[],\"properties\":{\"parameter1\":{\"type\":\"string\"},\"parameter2\":{\"type\":\"string\"}}}", tool.Parameters.ToString());
    }
}
