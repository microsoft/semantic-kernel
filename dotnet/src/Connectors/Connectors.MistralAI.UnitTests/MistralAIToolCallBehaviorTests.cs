// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Xunit;
using static Microsoft.SemanticKernel.Connectors.MistralAI.MistralAIToolCallBehavior;

namespace SemanticKernel.Connectors.MistralAI.UnitTests;

/// <summary>
/// Unit tests for <see cref="MistralAIToolCallBehavior"/>
/// </summary>
public sealed class MistralAIToolCallBehaviorTests
{
    [Fact]
    public void EnableKernelFunctionsReturnsCorrectKernelFunctionsInstance()
    {
        // Arrange & Act
        var behavior = MistralAIToolCallBehavior.EnableKernelFunctions;

        // Assert
        Assert.IsType<KernelFunctions>(behavior);
        Assert.Equal(0, behavior.MaximumAutoInvokeAttempts);
        Assert.Equal($"{nameof(KernelFunctions)}(autoInvoke:{behavior.MaximumAutoInvokeAttempts != 0})", behavior.ToString());
    }

    [Fact]
    public void AutoInvokeKernelFunctionsReturnsCorrectKernelFunctionsInstance()
    {
        // Arrange & Act
        const int DefaultMaximumAutoInvokeAttempts = 5;
        var behavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions;

        // Assert
        Assert.IsType<KernelFunctions>(behavior);
        Assert.Equal(DefaultMaximumAutoInvokeAttempts, behavior.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void CreateAutoInvokeKernelFunctionsWithCustomMaximumReturnsCorrectInstance()
    {
        // Arrange & Act
        const int CustomMaximumAutoInvokeAttempts = 10;
        var behavior = MistralAIToolCallBehavior.CreateAutoInvokeKernelFunctions(CustomMaximumAutoInvokeAttempts);

        // Assert
        Assert.IsType<KernelFunctions>(behavior);
        Assert.Equal(CustomMaximumAutoInvokeAttempts, behavior.MaximumAutoInvokeAttempts);
    }

    [Fact]
    public void RequiredFunctionsReturnsAnyFunctionInstance()
    {
        // Arrange & Act
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "MyFunction");
        List<KernelFunction> functions = [function];
        var behavior = MistralAIToolCallBehavior.RequiredFunctions(functions);

        // Assert
        Assert.IsType<AnyFunction>(behavior);
        Assert.Contains($"{nameof(AnyFunction)}(autoInvoke:{behavior.MaximumAutoInvokeAttempts != 0})", behavior.ToString());
    }

    [Fact]
    public void RequiredFunctionsWithCustomMaximumReturnsCorrectInstance()
    {
        // Arrange & Act
        const int CustomMaximumAutoInvokeAttempts = 3;
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "MyFunction");
        List<KernelFunction> functions = [function];
        var behavior = MistralAIToolCallBehavior.RequiredFunctions(functions, autoInvoke: true, CustomMaximumAutoInvokeAttempts);

        // Assert
        Assert.IsType<AnyFunction>(behavior);
        Assert.Equal(CustomMaximumAutoInvokeAttempts, behavior.MaximumAutoInvokeAttempts);
    }
}
