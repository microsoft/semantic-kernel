// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.FunctionCalling;
public sealed class OpenAIFunctionTests
{
    [Fact]
    public void ItCanConvertToFunctionDefinitionWithNoPluginName()
    {
        // Arrange
        var sut = new OpenAIFunction
        {
            FunctionName = "myfunc",
            PluginName = string.Empty,
            Description = "This is a description of the function.",
        };

        // Act
        FunctionDefinition result = sut.ToFunctionDefinition();

        // Assert
        Assert.Equal(sut.FunctionName, result.Name);
        Assert.Equal(sut.Description, result.Description);
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionWithPluginName()
    {
        // Arrange
        var sut = new OpenAIFunction
        {
            FunctionName = "myfunc",
            PluginName = "myplugin",
            Description = "This is a description of the function.",
        };

        // Act
        FunctionDefinition result = sut.ToFunctionDefinition();

        // Assert
        Assert.Equal("myplugin-myfunc", result.Name);
        Assert.Equal(sut.Description, result.Description);
    }
}
