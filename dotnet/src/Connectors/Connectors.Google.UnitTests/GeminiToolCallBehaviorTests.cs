﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests;

/// <summary>
/// Unit tests for <see cref="GeminiToolCallBehavior"/>
/// </summary>
public sealed class GeminiToolCallBehaviorTests
{
    [Fact]
    public void EnableKernelFunctionsReturnsCorrectKernelFunctionsInstance()
    {
        // Arrange & Act
        var behavior = GeminiToolCallBehavior.EnableKernelFunctions;

        // Assert
        Assert.IsType<GeminiToolCallBehavior.KernelFunctions>(behavior);
        Assert.Equal(0, behavior.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void AutoInvokeKernelFunctionsReturnsCorrectKernelFunctionsInstance()
    {
        // Arrange & Act
        const int DefaultMaximumAutoInvokeAttempts = 128;
        var behavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions;

        // Assert
        Assert.IsType<GeminiToolCallBehavior.KernelFunctions>(behavior);
        Assert.Equal(DefaultMaximumAutoInvokeAttempts, behavior.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void EnableFunctionsReturnsEnabledFunctionsInstance()
    {
        // Arrange & Act
        List<GeminiFunction> functions =
            [new GeminiFunction("Plugin", "Function", "description", [], null)];
        var behavior = GeminiToolCallBehavior.EnableFunctions(functions);

        // Assert
        Assert.IsType<GeminiToolCallBehavior.EnabledFunctions>(behavior);
    }

    [Fact]
    public void KernelFunctionsConfigureGeminiRequestWithNullKernelDoesNotAddTools()
    {
        // Arrange
        var kernelFunctions = new GeminiToolCallBehavior.KernelFunctions(autoInvoke: false);
        var geminiRequest = new GeminiRequest();

        // Act
        kernelFunctions.ConfigureGeminiRequest(null, geminiRequest);

        // Assert
        Assert.Null(geminiRequest.Tools);
    }

    [Fact]
    public void KernelFunctionsConfigureGeminiRequestWithoutFunctionsDoesNotAddTools()
    {
        // Arrange
        var kernelFunctions = new GeminiToolCallBehavior.KernelFunctions(autoInvoke: false);
        var geminiRequest = new GeminiRequest();
        var kernel = Kernel.CreateBuilder().Build();

        // Act
        kernelFunctions.ConfigureGeminiRequest(kernel, geminiRequest);

        // Assert
        Assert.Null(geminiRequest.Tools);
    }

    [Fact]
    public void KernelFunctionsConfigureGeminiRequestWithFunctionsAddsTools()
    {
        // Arrange
        var kernelFunctions = new GeminiToolCallBehavior.KernelFunctions(autoInvoke: false);
        var geminiRequest = new GeminiRequest();
        var kernel = Kernel.CreateBuilder().Build();
        var plugin = GetTestPlugin();
        kernel.Plugins.Add(plugin);

        // Act
        kernelFunctions.ConfigureGeminiRequest(kernel, geminiRequest);

        // Assert
        AssertFunctions(geminiRequest);
    }

    [Fact]
    public void EnabledFunctionsConfigureGeminiRequestWithoutFunctionsDoesNotAddTools()
    {
        // Arrange
        var enabledFunctions = new GeminiToolCallBehavior.EnabledFunctions([], autoInvoke: false);
        var geminiRequest = new GeminiRequest();

        // Act
        enabledFunctions.ConfigureGeminiRequest(null, geminiRequest);

        // Assert
        Assert.Null(geminiRequest.Tools);
    }

    [Fact]
    public void EnabledFunctionsConfigureGeminiRequestWithAutoInvokeAndNullKernelThrowsException()
    {
        // Arrange
        var functions = GetTestPlugin().GetFunctionsMetadata().Select(function => function.ToGeminiFunction());
        var enabledFunctions = new GeminiToolCallBehavior.EnabledFunctions(functions, autoInvoke: true);
        var geminiRequest = new GeminiRequest();

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => enabledFunctions.ConfigureGeminiRequest(null, geminiRequest));
        Assert.Equal(
            $"Auto-invocation with {nameof(GeminiToolCallBehavior.EnabledFunctions)} is not supported when no kernel is provided.",
            exception.Message);
    }

    [Fact]
    public void EnabledFunctionsConfigureGeminiRequestWithAutoInvokeAndEmptyKernelThrowsException()
    {
        // Arrange
        var functions = GetTestPlugin().GetFunctionsMetadata().Select(function => function.ToGeminiFunction());
        var enabledFunctions = new GeminiToolCallBehavior.EnabledFunctions(functions, autoInvoke: true);
        var geminiRequest = new GeminiRequest();
        var kernel = Kernel.CreateBuilder().Build();

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => enabledFunctions.ConfigureGeminiRequest(kernel, geminiRequest));
        Assert.Equal(
            $"The specified {nameof(GeminiToolCallBehavior.EnabledFunctions)} function MyPlugin{GeminiFunction.NameSeparator}MyFunction is not available in the kernel.",
            exception.Message);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void EnabledFunctionsConfigureGeminiRequestWithKernelAndPluginsAddsTools(bool autoInvoke)
    {
        // Arrange
        var plugin = GetTestPlugin();
        var functions = plugin.GetFunctionsMetadata().Select(function => function.ToGeminiFunction());
        var enabledFunctions = new GeminiToolCallBehavior.EnabledFunctions(functions, autoInvoke);
        var geminiRequest = new GeminiRequest();
        var kernel = Kernel.CreateBuilder().Build();

        kernel.Plugins.Add(plugin);

        // Act
        enabledFunctions.ConfigureGeminiRequest(kernel, geminiRequest);

        // Assert
        AssertFunctions(geminiRequest);
    }

    [Fact]
    public void EnabledFunctionsCloneReturnsCorrectClone()
    {
        // Arrange
        var functions = GetTestPlugin().GetFunctionsMetadata().Select(function => function.ToGeminiFunction());
        var toolcallbehavior = new GeminiToolCallBehavior.EnabledFunctions(functions, autoInvoke: true);

        // Act
        var clone = toolcallbehavior.Clone();

        // Assert
        Assert.IsType<GeminiToolCallBehavior.EnabledFunctions>(clone);
        Assert.NotSame(toolcallbehavior, clone);
        Assert.Equivalent(toolcallbehavior, clone, strict: true);
    }

    [Fact]
    public void KernelFunctionsCloneReturnsCorrectClone()
    {
        // Arrange
        var functions = GetTestPlugin().GetFunctionsMetadata().Select(function => function.ToGeminiFunction());
        var toolcallbehavior = new GeminiToolCallBehavior.KernelFunctions(autoInvoke: true);

        // Act
        var clone = toolcallbehavior.Clone();

        // Assert
        Assert.IsType<GeminiToolCallBehavior.KernelFunctions>(clone);
        Assert.NotSame(toolcallbehavior, clone);
        Assert.Equivalent(toolcallbehavior, clone, strict: true);
    }

    [Fact]
    public void FunctionChoiceBehaviorAutoConvertsToAutoInvokeKernelFunctions()
    {
        // Arrange
        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Act
        var converted = GeminiPromptExecutionSettings.FromExecutionSettings(settings);

        // Assert
        Assert.NotNull(converted.ToolCallBehavior);
        Assert.IsType<GeminiToolCallBehavior.KernelFunctions>(converted.ToolCallBehavior);
        Assert.True(converted.ToolCallBehavior.MaximumAutoInvokeAttempts > 0);
    }

    [Fact]
    public void FunctionChoiceBehaviorAutoWithNoAutoInvokeConvertsToEnableKernelFunctions()
    {
        // Arrange
        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false)
        };

        // Act
        var converted = GeminiPromptExecutionSettings.FromExecutionSettings(settings);

        // Assert
        Assert.NotNull(converted.ToolCallBehavior);
        Assert.IsType<GeminiToolCallBehavior.KernelFunctions>(converted.ToolCallBehavior);
        Assert.Equal(0, converted.ToolCallBehavior.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void FunctionChoiceBehaviorRequiredConvertsToAutoInvokeKernelFunctions()
    {
        // Arrange
        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Required()
        };

        // Act
        var converted = GeminiPromptExecutionSettings.FromExecutionSettings(settings);

        // Assert
        Assert.NotNull(converted.ToolCallBehavior);
        Assert.IsType<GeminiToolCallBehavior.KernelFunctions>(converted.ToolCallBehavior);
        Assert.True(converted.ToolCallBehavior.MaximumAutoInvokeAttempts > 0);
    }

    [Fact]
    public void FunctionChoiceBehaviorNoneConvertsToEnableKernelFunctions()
    {
        // Arrange
        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.None()
        };

        // Act
        var converted = GeminiPromptExecutionSettings.FromExecutionSettings(settings);

        // Assert
        Assert.NotNull(converted.ToolCallBehavior);
        Assert.IsType<GeminiToolCallBehavior.KernelFunctions>(converted.ToolCallBehavior);
        // None behavior doesn't auto-invoke
        Assert.Equal(0, converted.ToolCallBehavior.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void GeminiPromptExecutionSettingsWithNoFunctionChoiceBehaviorDoesNotSetToolCallBehavior()
    {
        // Arrange
        var settings = new GeminiPromptExecutionSettings();

        // Act
        var converted = GeminiPromptExecutionSettings.FromExecutionSettings(settings);

        // Assert
        Assert.Null(converted.ToolCallBehavior);
    }

    [Fact]
    public void GeminiPromptExecutionSettingsPreservesExistingToolCallBehavior()
    {
        // Arrange
        var settings = new GeminiPromptExecutionSettings
        {
            ToolCallBehavior = GeminiToolCallBehavior.EnableKernelFunctions,
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Act
        var converted = GeminiPromptExecutionSettings.FromExecutionSettings(settings);

        // Assert - ToolCallBehavior should be preserved when already set
        Assert.NotNull(converted.ToolCallBehavior);
        Assert.IsType<GeminiToolCallBehavior.KernelFunctions>(converted.ToolCallBehavior);
        Assert.Equal(0, converted.ToolCallBehavior.MaximumAutoInvokeAttempts);
    }

    private static KernelPlugin GetTestPlugin()
    {
        var function = KernelFunctionFactory.CreateFromMethod(
            (string parameter1, string parameter2) => "Result1",
            "MyFunction",
            "Test Function",
            [new KernelParameterMetadata("parameter1"), new KernelParameterMetadata("parameter2")],
            new KernelReturnParameterMetadata { ParameterType = typeof(string), Description = "Function Result" });

        return KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);
    }

    private static void AssertFunctions(GeminiRequest request)
    {
        Assert.NotNull(request.Tools);
        Assert.Single(request.Tools);
        Assert.Single(request.Tools[0].Functions);

        var function = request.Tools[0].Functions[0];

        Assert.NotNull(function);

        Assert.Equal($"MyPlugin{GeminiFunction.NameSeparator}MyFunction", function.Name);
        Assert.Equal("Test Function", function.Description);
        Assert.Equal("""{"type":"object","required":[],"properties":{"parameter1":{"type":"string"},"parameter2":{"type":"string"}}}""",
            JsonSerializer.Serialize(function.Parameters));
    }
}
