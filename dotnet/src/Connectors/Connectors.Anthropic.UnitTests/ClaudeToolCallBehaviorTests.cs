// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Microsoft.SemanticKernel.Connectors.Anthropic.Core;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests;

/// <summary>
/// Unit tests for <see cref="ClaudeToolCallBehavior"/>
/// </summary>
public sealed class ClaudeToolCallBehaviorTests
{
    [Fact]
    public void EnableKernelFunctionsReturnsCorrectKernelFunctionsInstance()
    {
        // Arrange & Act
        var behavior = ClaudeToolCallBehavior.EnableKernelFunctions;

        // Assert
        Assert.IsType<ClaudeToolCallBehavior.KernelFunctions>(behavior);
        Assert.Equal(0, behavior.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void AutoInvokeKernelFunctionsReturnsCorrectKernelFunctionsInstance()
    {
        // Arrange & Act
        var behavior = ClaudeToolCallBehavior.AutoInvokeKernelFunctions;

        // Assert
        Assert.IsType<ClaudeToolCallBehavior.KernelFunctions>(behavior);
        Assert.Equal(5, behavior.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void EnableFunctionsReturnsEnabledFunctionsInstance()
    {
        // Arrange & Act
        List<ClaudeFunction> functions =
            [new ClaudeFunction("Plugin", "Function", "description", [], null)];
        var behavior = ClaudeToolCallBehavior.EnableFunctions(functions);

        // Assert
        Assert.IsType<ClaudeToolCallBehavior.EnabledFunctions>(behavior);
    }

    [Fact]
    public void KernelFunctionsConfigureClaudeRequestWithNullKernelDoesNotAddTools()
    {
        // Arrange
        var kernelFunctions = new ClaudeToolCallBehavior.KernelFunctions(autoInvoke: false);
        var ClaudeRequest = new ClaudeRequest();

        // Act
        kernelFunctions.ConfigureClaudeRequest(null, ClaudeRequest);

        // Assert
        Assert.Null(ClaudeRequest.Tools);
    }

    [Fact]
    public void KernelFunctionsConfigureClaudeRequestWithoutFunctionsDoesNotAddTools()
    {
        // Arrange
        var kernelFunctions = new ClaudeToolCallBehavior.KernelFunctions(autoInvoke: false);
        var ClaudeRequest = new ClaudeRequest();
        var kernel = Kernel.CreateBuilder().Build();

        // Act
        kernelFunctions.ConfigureClaudeRequest(kernel, ClaudeRequest);

        // Assert
        Assert.Null(ClaudeRequest.Tools);
    }

    [Fact]
    public void KernelFunctionsConfigureClaudeRequestWithFunctionsAddsTools()
    {
        // Arrange
        var kernelFunctions = new ClaudeToolCallBehavior.KernelFunctions(autoInvoke: false);
        var ClaudeRequest = new ClaudeRequest();
        var kernel = Kernel.CreateBuilder().Build();
        var plugin = GetTestPlugin();
        kernel.Plugins.Add(plugin);

        // Act
        kernelFunctions.ConfigureClaudeRequest(kernel, ClaudeRequest);

        // Assert
        AssertFunctions(ClaudeRequest);
    }

    [Fact]
    public void EnabledFunctionsConfigureClaudeRequestWithoutFunctionsDoesNotAddTools()
    {
        // Arrange
        var enabledFunctions = new ClaudeToolCallBehavior.EnabledFunctions([], autoInvoke: false);
        var ClaudeRequest = new ClaudeRequest();

        // Act
        enabledFunctions.ConfigureClaudeRequest(null, ClaudeRequest);

        // Assert
        Assert.Null(ClaudeRequest.Tools);
    }

    [Fact]
    public void EnabledFunctionsConfigureClaudeRequestWithAutoInvokeAndNullKernelThrowsException()
    {
        // Arrange
        var functions = GetTestPlugin().GetFunctionsMetadata().Select(function => ClaudeKernelFunctionMetadataExtensions.ToClaudeFunction(function));
        var enabledFunctions = new ClaudeToolCallBehavior.EnabledFunctions(functions, autoInvoke: true);
        var ClaudeRequest = new ClaudeRequest();

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => enabledFunctions.ConfigureClaudeRequest(null, ClaudeRequest));
        Assert.Equal(
            $"Auto-invocation with {nameof(ClaudeToolCallBehavior.EnabledFunctions)} is not supported when no kernel is provided.",
            exception.Message);
    }

    [Fact]
    public void EnabledFunctionsConfigureClaudeRequestWithAutoInvokeAndEmptyKernelThrowsException()
    {
        // Arrange
        var functions = GetTestPlugin().GetFunctionsMetadata().Select(function => function.ToClaudeFunction());
        var enabledFunctions = new ClaudeToolCallBehavior.EnabledFunctions(functions, autoInvoke: true);
        var ClaudeRequest = new ClaudeRequest();
        var kernel = Kernel.CreateBuilder().Build();

        // Act & Assert
        var exception = Assert.Throws<KernelException>(() => enabledFunctions.ConfigureClaudeRequest(kernel, ClaudeRequest));
        Assert.Equal(
            $"The specified {nameof(ClaudeToolCallBehavior.EnabledFunctions)} function MyPlugin{ClaudeFunction.NameSeparator}MyFunction is not available in the kernel.",
            exception.Message);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void EnabledFunctionsConfigureClaudeRequestWithKernelAndPluginsAddsTools(bool autoInvoke)
    {
        // Arrange
        var plugin = GetTestPlugin();
        var functions = plugin.GetFunctionsMetadata().Select(function => function.ToClaudeFunction());
        var enabledFunctions = new ClaudeToolCallBehavior.EnabledFunctions(functions, autoInvoke);
        var ClaudeRequest = new ClaudeRequest();
        var kernel = Kernel.CreateBuilder().Build();

        kernel.Plugins.Add(plugin);

        // Act
        enabledFunctions.ConfigureClaudeRequest(kernel, ClaudeRequest);

        // Assert
        AssertFunctions(ClaudeRequest);
    }

    [Fact]
    public void EnabledFunctionsCloneReturnsCorrectClone()
    {
        // Arrange
        var functions = GetTestPlugin().GetFunctionsMetadata().Select(function => function.ToClaudeFunction());
        var toolcallbehavior = new ClaudeToolCallBehavior.EnabledFunctions(functions, autoInvoke: true);

        // Act
        var clone = toolcallbehavior.Clone();

        // Assert
        Assert.IsType<ClaudeToolCallBehavior.EnabledFunctions>(clone);
        Assert.NotSame(toolcallbehavior, clone);
        Assert.Equivalent(toolcallbehavior, clone, strict: true);
    }

    [Fact]
    public void KernelFunctionsCloneReturnsCorrectClone()
    {
        // Arrange
        var functions = GetTestPlugin().GetFunctionsMetadata().Select(function => function.ToClaudeFunction());
        var toolcallbehavior = new ClaudeToolCallBehavior.KernelFunctions(autoInvoke: true);

        // Act
        var clone = toolcallbehavior.Clone();

        // Assert
        Assert.IsType<ClaudeToolCallBehavior.KernelFunctions>(clone);
        Assert.NotSame(toolcallbehavior, clone);
        Assert.Equivalent(toolcallbehavior, clone, strict: true);
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

    private static void AssertFunctions(ClaudeRequest request)
    {
        Assert.NotNull(request.Tools);
        Assert.Single(request.Tools);
        Assert.Single(request.Tools[0].Functions);

        var function = request.Tools[0].Functions[0];

        Assert.NotNull(function);

        Assert.Equal($"MyPlugin{ClaudeFunction.NameSeparator}MyFunction", function.Name);
        Assert.Equal("Test Function", function.Description);
        Assert.Equal("""{"type":"object","required":[],"properties":{"parameter1":{"type":"string"},"parameter2":{"type":"string"}}}""",
            JsonSerializer.Serialize(function.Parameters));
    }
}
