// Copyright (c) Microsoft. All rights reserved.

<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
using System;
using System.Collections.Generic;
using System.Text.Json;
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin");
        var plugins = new KernelPluginCollection([plugin]);

        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin_MyFunction", string.Empty);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
        var args = JsonSerializer.Serialize(new Dictionary<string, object?>());
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin");
        var plugins = new KernelPluginCollection([plugin]);

        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin_MyFunction", BinaryData.FromString(args));
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
        var args = JsonSerializer.Serialize(new Dictionary<string, object?>());
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "MyFunction");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);

        var plugins = new KernelPluginCollection([plugin]);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin-MyFunction", string.Empty);
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin-MyFunction", string.Empty);
=======
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin-MyFunction", BinaryData.FromString(args));
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

        // Act
        var result = plugins.TryGetFunctionAndArguments(toolCall, out var actualFunction, out var actualArguments);

        // Assert
        Assert.True(result);
        Assert.Equal(function.Name, actualFunction?.Name);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Assert.Null(actualArguments);
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        Assert.Null(actualArguments);
=======
        Assert.Empty(actualArguments!);
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    }

    [Fact]
    public void TryGetFunctionAndArgumentsWithArgumentsReturnsTrue()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "MyFunction");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);

        var plugins = new KernelPluginCollection([plugin]);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin-MyFunction", "{\n \"location\": \"San Diego\",\n \"max_price\": 300\n,\n \"null_argument\": null\n}");
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin-MyFunction", "{\n \"location\": \"San Diego\",\n \"max_price\": 300\n,\n \"null_argument\": null\n}");
=======
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin-MyFunction", BinaryData.FromString("{\n \"location\": \"San Diego\",\n \"max_price\": 300\n,\n \"null_argument\": null\n}"));
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

        // Act
        var result = plugins.TryGetFunctionAndArguments(toolCall, out var actualFunction, out var actualArguments);

        // Assert
        Assert.True(result);
        Assert.Equal(function.Name, actualFunction?.Name);

        Assert.NotNull(actualArguments);

        Assert.Equal("San Diego", actualArguments["location"]);
        Assert.Equal("300", actualArguments["max_price"]);

        Assert.Null(actualArguments["null_argument"]);
    }
}
