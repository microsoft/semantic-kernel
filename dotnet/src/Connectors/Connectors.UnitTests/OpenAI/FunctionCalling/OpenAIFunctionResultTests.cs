// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.FunctionCalling;
public sealed class OpenAIFunctionResultTests
{
    [Fact]
    public void ItCanConvertFromFunctionCallWithPluginName()
    {
        // Arrange
        var sut = new FunctionCall("foo-bar", "{}");

        // Act
        var result = OpenAIFunctionResult.FromFunctionCall(sut);

        // Assert
        Assert.Equal("foo", result.PluginName);
        Assert.Equal("bar", result.FunctionName);
    }

    [Fact]
    public void ItCanConvertFromFunctionCallWithNoPluginName()
    {
        // Arrange
        var sut = new FunctionCall("foo", "{}");

        // Act
        var result = OpenAIFunctionResult.FromFunctionCall(sut);

        // Assert
        Assert.Equal(string.Empty, result.PluginName);
        Assert.Equal("foo", result.FunctionName);
    }

    [Fact]
    public void ItCanConvertFromFunctionCallWithNoParameters()
    {
        // Arrange
        var sut = new FunctionCall("foo", "{}");

        // Act
        var result = OpenAIFunctionResult.FromFunctionCall(sut);

        // Assert
        Assert.Equal(new Dictionary<string, object>(), result.Parameters);
    }

    [Fact]
    public void ItCanConvertFromFunctionCallWithParameters()
    {
        // Arrange
        var sut = new FunctionCall("foo", "{ \"param1\": \"bar\", \"param2\": 5 }");

        // Act
        var result = OpenAIFunctionResult.FromFunctionCall(sut);

        // Assert
        Assert.True(result.Parameters.TryGetValue("param1", out object? value1));
        Assert.Equal("bar", value1.ToString());
        Assert.True(result.Parameters.TryGetValue("param2", out object? value2));
        Assert.Equal("5", value2.ToString());
    }
}
