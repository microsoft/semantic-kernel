// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Core;

/// <summary>
/// Unit tests for <see cref="OpenAIPluginCollectionExtensions"/> class.
/// </summary>
public sealed class OpenAIPluginCollectionExtensionsTests
{
    [Fact]
    public void TryGetFunctionAndArgumentsWithNonExistingFunctionReturnsFalse()
    {
        // Arrange
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin");
        var plugins = new KernelPluginCollection([plugin]);

        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin_MyFunction", string.Empty);

        // Act
        var result = plugins.TryGetOpenAIFunctionAndArguments(toolCall, out var actualFunction, out var actualArguments);

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
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin-MyFunction", string.Empty);

        // Act
        var result = plugins.TryGetOpenAIFunctionAndArguments(toolCall, out var actualFunction, out var actualArguments);

        // Assert
        Assert.True(result);
        Assert.Equal(function.Name, actualFunction?.Name);
        Assert.Null(actualArguments);
    }

    [Fact]
    public void TryGetFunctionAndArgumentsWithArgumentsReturnsTrue()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "MyFunction");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);

        var plugins = new KernelPluginCollection([plugin]);
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin-MyFunction", "{\n \"location\": \"San Diego\",\n \"max_price\": 300\n,\n \"null_argument\": null\n}");

        // Act
        var result = plugins.TryGetOpenAIFunctionAndArguments(toolCall, out var actualFunction, out var actualArguments);

        // Assert
        Assert.True(result);
        Assert.Equal(function.Name, actualFunction?.Name);

        Assert.NotNull(actualArguments);

        Assert.Equal("San Diego", actualArguments["location"]);
        Assert.Equal("300", actualArguments["max_price"]);

        Assert.Null(actualArguments["null_argument"]);
    }
}
