// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Extensions;

/// <summary>
/// Unit tests for <see cref="GeminiPluginCollectionExtensions"/> class.
/// </summary>
public sealed class GeminiPluginCollectionExtensionsTests
{
    [Fact]
    public void TryGetFunctionAndArgumentsWithNonExistingFunctionReturnsFalse()
    {
        // Arrange
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", []);
        var plugins = new KernelPluginCollection([plugin]);

        var toolCall = new GeminiFunctionToolCall(new GeminiPart.FunctionCallPart { FunctionName = "MyPlugin-MyFunction" });

        // Act
        var result = plugins.TryGetFunctionAndArguments(toolCall, out var actualFunction, out var actualArguments);

        // Assert
        Assert.False(result);
        Assert.Null(actualFunction);
        Assert.Null(actualArguments);
    }

    [Fact]
    public void TryGetFunctionAndArgumentsWithoutArgumentsReturnsTrue()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "MyFunction");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);

        var plugins = new KernelPluginCollection([plugin]);
        var toolCall = new GeminiFunctionToolCall(new GeminiPart.FunctionCallPart { FunctionName = "MyPlugin-MyFunction" });

        // Act
        var result = plugins.TryGetFunctionAndArguments(toolCall, out var actualFunction, out var actualArguments);

        // Assert
        Assert.True(result);
        Assert.Same(function, actualFunction);
        Assert.Null(actualArguments);
    }

    [Fact]
    public void TryGetFunctionAndArgumentsWithArgumentsReturnsTrue()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "MyFunction");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);
        Dictionary<string, object?> expectedArgs = new()
        {
            { "location", "San Diego" },
            { "max_price", 300 },
            { "null_argument", null }
        };
        var plugins = new KernelPluginCollection([plugin]);
        var toolCall = new GeminiFunctionToolCall(new GeminiPart.FunctionCallPart
        {
            FunctionName = "MyPlugin-MyFunction",
            Arguments = expectedArgs
        });

        // Act
        var result = plugins.TryGetFunctionAndArguments(toolCall, out var actualFunction, out var actualArguments);

        // Assert
        Assert.True(result);
        Assert.Same(function, actualFunction);

        Assert.NotNull(actualArguments);

        Assert.Equivalent(expectedArgs, actualArguments, strict: true);
    }
}
