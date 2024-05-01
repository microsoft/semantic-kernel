// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ToolBehaviors;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

/// <summary>
/// Unit tests for <see cref="FunctionCallBehavior"/>
/// </summary>
public sealed class FunctionCallBehaviorTests
{
    private readonly static JsonSerializerOptions s_serializerOptions = new() { TypeInfoResolver = new ToolBehaviorsResolver() };

    [Fact]
    public void EnableKernelFunctionsAreNotAutoInvoked()
    {
        // Arrange
        var kernel = new Kernel();
        var behavior = FunctionCallBehavior.AutoFunctionChoice(autoInvoke: false);

        // Act
        var config = behavior.Choice.Configure(new() { Kernel = kernel });

        // Assert
        Assert.NotNull(config);
        Assert.Equal(0, config.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void AutoInvokeKernelFunctionsShouldSpecifyNumberOfAutoInvokeAttempts()
    {
        // Arrange
        var kernel = new Kernel();
        var behavior = FunctionCallBehavior.AutoFunctionChoice();

        // Act
        var config = behavior.Choice.Configure(new() { Kernel = kernel });

        // Assert
        Assert.NotNull(config);
        Assert.Equal(5, config.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void KernelFunctionsConfigureWithNullKernelDoesNotAddTools()
    {
        // Arrange
        var kernelFunctions = FunctionCallBehavior.AutoFunctionChoice(autoInvoke: false);

        // Act
        var config = kernelFunctions.Choice.Configure(new() { });

        // Assert
        Assert.Null(config.AvailableFunctions);
        Assert.Null(config.RequiredFunctions);
    }

    [Fact]
    public void KernelFunctionsConfigureWithoutFunctionsDoesNotAddTools()
    {
        // Arrange
        var kernelFunctions = FunctionCallBehavior.AutoFunctionChoice(autoInvoke: false);

        var kernel = Kernel.CreateBuilder().Build();

        // Act
        var config = kernelFunctions.Choice.Configure(new() { Kernel = kernel });

        // Assert
        Assert.Null(config.AvailableFunctions);
        Assert.Null(config.RequiredFunctions);
    }

    [Fact]
    public void KernelFunctionsConfigureWithFunctionsAddsTools()
    {
        // Arrange
        var kernelFunctions = FunctionCallBehavior.AutoFunctionChoice(autoInvoke: false);
        var kernel = Kernel.CreateBuilder().Build();

        var plugin = this.GetTestPlugin();

        kernel.Plugins.Add(plugin);

        // Act
        var config = kernelFunctions.Choice.Configure(new() { Kernel = kernel });

        // Assert
        Assert.Null(config.RequiredFunctions);

        this.AssertFunctions(config.AvailableFunctions);
    }

    [Fact]
    public void EnabledFunctionsConfigureWithoutFunctionsDoesNotAddTools()
    {
        // Arrange
        var enabledFunctions = FunctionCallBehavior.AutoFunctionChoice(autoInvoke: false);
        var chatCompletionsOptions = new ChatCompletionsOptions();

        // Act
        var config = enabledFunctions.Choice.Configure(new() { });

        // Assert
        Assert.Null(chatCompletionsOptions.ToolChoice);
        Assert.Empty(chatCompletionsOptions.Tools);
    }

    [Fact]
    public void EnabledFunctionsConfigureWithAutoInvokeAndNullKernelThrowsException()
    {
        // Arrange
        var kernel = new Kernel();

        var function = this.GetTestPlugin().Single();
        var enabledFunctions = FunctionCallBehavior.AutoFunctionChoice([function], autoInvoke: true);

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => enabledFunctions.Choice.Configure(new() { })); ;
        Assert.Equal("Auto-invocation in Auto mode is not supported when no kernel is provided.", exception.Message);
    }

    [Fact]
    public void EnabledFunctionsConfigureWithAutoInvokeAndEmptyKernelThrowsException()
    {
        // Arrange
        var function = this.GetTestPlugin().Single();
        var enabledFunctions = FunctionCallBehavior.AutoFunctionChoice([function], autoInvoke: true);
        var kernel = Kernel.CreateBuilder().Build();

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => enabledFunctions.Choice.Configure(new() { Kernel = kernel }));
        Assert.Equal("The specified function MyPlugin.MyFunction is not available in the kernel.", exception.Message);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void EnabledFunctionsConfigureWithKernelAndPluginsAddsTools(bool autoInvoke)
    {
        // Arrange
        var plugin = this.GetTestPlugin();
        var function = plugin.Single();
        var enabledFunctions = FunctionCallBehavior.AutoFunctionChoice([function], autoInvoke: autoInvoke);
        var kernel = Kernel.CreateBuilder().Build();

        kernel.Plugins.Add(plugin);

        // Act
        var config = enabledFunctions.Choice.Configure(new() { Kernel = kernel });

        // Assert
        this.AssertFunctions(config.AvailableFunctions);
    }

    [Fact]
    public void RequiredFunctionsConfigureWithAutoInvokeAndNullKernelThrowsException()
    {
        // Arrange
        var kernel = new Kernel();

        var function = this.GetTestPlugin().Single();
        var requiredFunction = FunctionCallBehavior.AutoFunctionChoice([function], autoInvoke: true);

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => requiredFunction.Choice.Configure(new() { }));
        Assert.Equal("Auto-invocation in Auto mode is not supported when no kernel is provided.", exception.Message);
    }

    [Fact]
    public void RequiredFunctionsConfigureWithAutoInvokeAndEmptyKernelThrowsException()
    {
        // Arrange
        var function = this.GetTestPlugin().Single();
        var requiredFunction = FunctionCallBehavior.AutoFunctionChoice([function], autoInvoke: true);
        var kernel = Kernel.CreateBuilder().Build();

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => requiredFunction.Choice.Configure(new() { Kernel = kernel }));
        Assert.Equal("The specified function MyPlugin.MyFunction is not available in the kernel.", exception.Message);
    }

    [Fact]
    public void RequiredFunctionConfigureAddsTools()
    {
        // Arrange
        var plugin = this.GetTestPlugin();
        var function = plugin.Single();
        var requiredFunction = FunctionCallBehavior.RequiredFunctionChoice([function], autoInvoke: true);
        var kernel = new Kernel();
        kernel.Plugins.Add(plugin);

        // Act
        var config = requiredFunction.Choice.Configure(new() { Kernel = kernel });

        // Assert
        this.AssertFunctions(config.RequiredFunctions);
    }

    [Fact]
    public void ItShouldBePossibleToDeserializeAutoFunctionCallChoice()
    {
        // Arrange
        var json =
            """
            {
                "type":"auto",
                "allowAnyRequestedKernelFunction":true,
                "maximumAutoInvokeAttempts":12,
                "functions":[
                    "MyPlugin.MyFunction"
                 ]
            }
            """;

        // Act
        var deserializedFunction = JsonSerializer.Deserialize<FunctionCallChoice>(json, s_serializerOptions) as AutoFunctionCallChoice;

        // Assert
        Assert.NotNull(deserializedFunction);
        Assert.True(deserializedFunction.AllowAnyRequestedKernelFunction);
        Assert.Equal(12, deserializedFunction.MaximumAutoInvokeAttempts);
        Assert.NotNull(deserializedFunction.Functions);
        Assert.Single(deserializedFunction.Functions);
        Assert.Equal("MyPlugin.MyFunction", deserializedFunction.Functions.ElementAt(0));
    }

    [Fact]
    public void ItShouldBePossibleToDeserializeForcedFunctionCallChoice()
    {
        // Arrange
        var json =
            """
            {
                "type": "required",
                "maximumAutoInvokeAttempts": 12,
                "maximumUseAttempts": 10,
                "functions":[
                    "MyPlugin.MyFunction"
                 ]
            }
            """;

        // Act
        var deserializedFunction = JsonSerializer.Deserialize<FunctionCallChoice>(json, s_serializerOptions) as RequiredFunctionCallChoice;

        // Assert
        Assert.NotNull(deserializedFunction);
        Assert.Equal(10, deserializedFunction.MaximumUseAttempts);
        Assert.Equal(12, deserializedFunction.MaximumAutoInvokeAttempts);
        Assert.NotNull(deserializedFunction.Functions);
        Assert.Single(deserializedFunction.Functions);
        Assert.Equal("MyPlugin.MyFunction", deserializedFunction.Functions.ElementAt(0));
    }

    [Fact]
    public void ItShouldBePossibleToDeserializeNoneFunctionCallBehavior()
    {
        // Arrange
        var json =
            """
            {
                "type": "none"
            }
            """;

        // Act
        var deserializedFunction = JsonSerializer.Deserialize<FunctionCallChoice>(json, s_serializerOptions) as NoneFunctionCallChoice;

        // Assert
        Assert.NotNull(deserializedFunction);
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

    private void AssertFunctions(IEnumerable<KernelFunctionMetadata>? kernelFunctionsMetadata)
    {
        Assert.NotNull(kernelFunctionsMetadata);
        Assert.Single(kernelFunctionsMetadata);

        var functionMetadata = kernelFunctionsMetadata.ElementAt(0);

        Assert.NotNull(functionMetadata);

        Assert.Equal("MyPlugin", functionMetadata.PluginName);
        Assert.Equal("MyFunction", functionMetadata.Name);
        Assert.Equal("Test Function", functionMetadata.Description);
        Assert.Equal(2, functionMetadata.Parameters.Count);
    }
}
