// Copyright (c) Microsoft. All rights reserved.

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
    public void FunctionChoiceBehaviorAutoConvertsToEnabledFunctionsWithAllKernelFunctions()
    {
        // Arrange
        var kernel = CreateKernelWithFunctions("FunctionA", "FunctionB");
        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Act
        var converted = GeminiPromptExecutionSettings.FromExecutionSettings(settings, kernel);

        // Assert
        Assert.NotNull(converted.ToolCallBehavior);
        var enabledFunctions = Assert.IsType<GeminiToolCallBehavior.EnabledFunctions>(converted.ToolCallBehavior);
        Assert.True(converted.ToolCallBehavior.MaximumAutoInvokeAttempts > 0);
        // The provided set is validated against the requested functions.
        Assert.False(GetAllowAnyRequestedKernelFunction(converted.ToolCallBehavior));
        Assert.Equal(new[] { $"TestPlugin{GeminiFunction.NameSeparator}FunctionA", $"TestPlugin{GeminiFunction.NameSeparator}FunctionB" }, GetAdvertisedFunctionNames(enabledFunctions, kernel));
    }

    [Fact]
    public void FunctionChoiceBehaviorAutoWithNoAutoInvokeConvertsToEnabledFunctionsWithoutAutoInvoke()
    {
        // Arrange
        var kernel = CreateKernelWithFunctions("FunctionA");
        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false)
        };

        // Act
        var converted = GeminiPromptExecutionSettings.FromExecutionSettings(settings, kernel);

        // Assert
        Assert.NotNull(converted.ToolCallBehavior);
        Assert.IsType<GeminiToolCallBehavior.EnabledFunctions>(converted.ToolCallBehavior);
        Assert.Equal(0, converted.ToolCallBehavior.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void FunctionChoiceBehaviorRequiredConvertsToEnabledFunctions()
    {
        // Arrange
        var kernel = CreateKernelWithFunctions("FunctionA");
        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Required()
        };

        // Act
        var converted = GeminiPromptExecutionSettings.FromExecutionSettings(settings, kernel);

        // Assert
        Assert.NotNull(converted.ToolCallBehavior);
        Assert.IsType<GeminiToolCallBehavior.EnabledFunctions>(converted.ToolCallBehavior);
        Assert.True(converted.ToolCallBehavior.MaximumAutoInvokeAttempts > 0);
        Assert.False(GetAllowAnyRequestedKernelFunction(converted.ToolCallBehavior));
    }

    [Fact]
    public void FunctionChoiceBehaviorNoneConvertsToEnabledFunctionsWithoutAutoInvoke()
    {
        // Arrange
        var kernel = CreateKernelWithFunctions("FunctionA");
        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.None()
        };

        // Act
        var converted = GeminiPromptExecutionSettings.FromExecutionSettings(settings, kernel);

        // Assert
        Assert.NotNull(converted.ToolCallBehavior);
        Assert.IsType<GeminiToolCallBehavior.EnabledFunctions>(converted.ToolCallBehavior);
        // None behavior doesn't auto-invoke
        Assert.Equal(0, converted.ToolCallBehavior.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void FunctionChoiceBehaviorAutoWithEmptyFunctionListDisablesFunctionCalling()
    {
        // Arrange
        // An empty function list is documented as being equivalent to disabling function calling.
        var kernel = CreateKernelWithFunctions("FunctionA", "FunctionB");
        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(functions: [], autoInvoke: true)
        };

        // Act
        var converted = GeminiPromptExecutionSettings.FromExecutionSettings(settings, kernel);

        // Assert
        Assert.Null(converted.ToolCallBehavior);
    }

    [Fact]
    public void FunctionChoiceBehaviorAutoWithSubsetProvidesOnlyThatSubset()
    {
        // Arrange
        var kernel = CreateKernelWithFunctions("First", "Second");
        var first = kernel.Plugins.GetFunction("TestPlugin", "First");
        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(functions: [first], autoInvoke: true)
        };

        // Act
        var converted = GeminiPromptExecutionSettings.FromExecutionSettings(settings, kernel);

        // Assert
        Assert.NotNull(converted.ToolCallBehavior);
        var enabledFunctions = Assert.IsType<GeminiToolCallBehavior.EnabledFunctions>(converted.ToolCallBehavior);
        Assert.False(GetAllowAnyRequestedKernelFunction(converted.ToolCallBehavior));
        // Only the function specified in the behavior is provided to the model.
        Assert.Equal(new[] { $"TestPlugin{GeminiFunction.NameSeparator}First" }, GetAdvertisedFunctionNames(enabledFunctions, kernel));
    }

    [Fact]
    public void FromExecutionSettingsDoesNotMutateCallerSettingsWhenConvertingFunctionChoiceBehavior()
    {
        // Arrange
        var kernel = CreateKernelWithFunctions("FunctionA");
        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Act
        var converted = GeminiPromptExecutionSettings.FromExecutionSettings(settings, kernel);

        // Assert - the caller's original settings object must remain untouched.
        Assert.NotSame(settings, converted);
        Assert.Null(settings.ToolCallBehavior);
        Assert.NotNull(converted.ToolCallBehavior);
    }

    [Fact]
    public void FromExecutionSettingsWithFrozenSettingsDoesNotThrowWhenConvertingFunctionChoiceBehavior()
    {
        // Arrange
        var kernel = CreateKernelWithFunctions("FunctionA");
        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };
        settings.Freeze();

        // Act - converting a frozen settings object must not attempt to mutate it.
        var converted = GeminiPromptExecutionSettings.FromExecutionSettings(settings, kernel);

        // Assert
        Assert.NotNull(converted.ToolCallBehavior);
        Assert.IsType<GeminiToolCallBehavior.EnabledFunctions>(converted.ToolCallBehavior);
    }

    [Fact]
    public void FromExecutionSettingsReResolvesFunctionChoiceBehaviorPerKernel()
    {
        // Arrange - a single reused settings object must reflect each request's own kernel.
        var settings = new GeminiPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };
        var kernelA = CreateKernelWithFunctions("FunctionA");
        var kernelB = CreateKernelWithFunctions("FunctionB");

        // Act
        var convertedA = GeminiPromptExecutionSettings.FromExecutionSettings(settings, kernelA);
        var convertedB = GeminiPromptExecutionSettings.FromExecutionSettings(settings, kernelB);

        // Assert - each request reflects its own kernel.
        var enabledA = Assert.IsType<GeminiToolCallBehavior.EnabledFunctions>(convertedA.ToolCallBehavior);
        var enabledB = Assert.IsType<GeminiToolCallBehavior.EnabledFunctions>(convertedB.ToolCallBehavior);
        Assert.Equal(new[] { $"TestPlugin{GeminiFunction.NameSeparator}FunctionA" }, GetAdvertisedFunctionNames(enabledA, kernelA));
        Assert.Equal(new[] { $"TestPlugin{GeminiFunction.NameSeparator}FunctionB" }, GetAdvertisedFunctionNames(enabledB, kernelB));
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

    private static Kernel CreateKernelWithFunctions(params string[] functionNames)
    {
        var functions = functionNames
            .Select(name => KernelFunctionFactory.CreateFromMethod(() => "result", name))
            .ToArray();

        var kernel = Kernel.CreateBuilder().Build();
        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("TestPlugin", functions));
        return kernel;
    }

    private static bool GetAllowAnyRequestedKernelFunction(GeminiToolCallBehavior behavior)
        => behavior.AllowAnyRequestedKernelFunction;

    private static string[] GetAdvertisedFunctionNames(GeminiToolCallBehavior behavior, Kernel kernel)
    {
        var request = new GeminiRequest();
        behavior.ConfigureGeminiRequest(kernel, request);
        if (request.Tools is null)
        {
            return [];
        }

        return request.Tools[0].Functions.Select(f => f.Name).ToArray();
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
