// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Nodes;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Extensions;

/// <summary>
/// Unit tests for <see cref="GeminiPluginCollectionExtensions"/> class.
/// </summary>
public sealed class GeminiPluginCollectionExtensionsTests
{
    [Fact]
    public void TryGetFunctionAndArgumentsWithNonExistingFunctionReturnsFalse()
    {
        // Arrange
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin");
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
        var toolCall = new GeminiFunctionToolCall(new GeminiPart.FunctionCallPart { FunctionName = $"MyPlugin{GeminiFunction.NameSeparator}MyFunction" });

        // Act
        var result = plugins.TryGetFunctionAndArguments(toolCall, out var actualFunction, out var actualArguments);

        // Assert
        Assert.True(result);
        Assert.NotNull(actualFunction);
        Assert.Equal(function.Name, actualFunction.Name);
        Assert.Null(actualArguments);
    }

    [Fact]
    public void TryGetFunctionAndArgumentsWithArgumentsReturnsTrue()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "MyFunction");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);
        var expectedArgs = new JsonObject
        {
            ["location"] = "San Diego",
            ["max_price"] = 300,
            ["null_argument"] = null
        };
        var plugins = new KernelPluginCollection([plugin]);
        var toolCall = new GeminiFunctionToolCall(new GeminiPart.FunctionCallPart
        {
            FunctionName = $"MyPlugin{GeminiFunction.NameSeparator}MyFunction",
            Arguments = expectedArgs
        });

        // Act
        var result = plugins.TryGetFunctionAndArguments(toolCall, out var actualFunction, out var actualArguments);

        // Assert
        Assert.True(result);
        Assert.NotNull(actualFunction);
        Assert.Equal(function.Name, actualFunction.Name);

        Assert.NotNull(actualArguments);
        Assert.Equal(expectedArgs["location"]!.ToString(), actualArguments["location"]!.ToString());
        Assert.Equal(expectedArgs["max_price"]!.ToString(), actualArguments["max_price"]!.ToString());
        Assert.Equal(expectedArgs["null_argument"], actualArguments["null_argument"]);
    }
}
