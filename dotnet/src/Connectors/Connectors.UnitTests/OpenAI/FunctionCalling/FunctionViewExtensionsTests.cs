// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.SkillDefinition;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.FunctionCalling;
public sealed class FunctionViewExtensionsTests
{
    [Fact]
    public void ItCanConvertToOpenAIFunctionNoParameters()
    {
        // Arrange
        var sut = new FunctionView
        {
            Name = "foo",
            SkillName = "bar",
            Description = "baz",
        };

        // Act
        var result = sut.ToOpenAIFunction();

        // Assert
        Assert.Equal(sut.Name, result.FunctionName);
        Assert.Equal(sut.SkillName, result.PluginName);
        Assert.Equal(sut.Description, result.Description);
    }

    [Fact]
    public void ItCanConvertToOpenAIFunctionWithParameter()
    {
        // Arrange
        var param1 = new ParameterView
        {
            Name = "param1",
            Description = "This is param1",
            IsRequired = false,
            Type = new ParameterViewType("int")
        };
        var sut = new FunctionView
        {
            Name = "foo",
            SkillName = "bar",
            Description = "baz",
            Parameters = new List<ParameterView> { param1 }
        };

        // Act
        var result = sut.ToOpenAIFunction();
        var outputParam = result.Parameters.First();

        // Assert
        Assert.Equal("int", outputParam.Type);
        Assert.Equal(param1.Name, outputParam.Name);
        Assert.Equal(param1.Description, outputParam.Description);
        Assert.Equal(param1.IsRequired, outputParam.IsRequired);
    }

    [Fact]
    public void ItCanConvertToOpenAIFunctionWithParameterNoType()
    {
        // Arrange
        var param1 = new ParameterView
        {
            Name = "param1",
            Description = "This is param1",
            IsRequired = false,
            Type = null
        };
        var sut = new FunctionView
        {
            Name = "foo",
            SkillName = "bar",
            Description = "baz",
            Parameters = new List<ParameterView> { param1 }
        };

        // Act
        var result = sut.ToOpenAIFunction();
        var outputParam = result.Parameters.First();

        // Assert
        Assert.Equal("string", outputParam.Type);
        Assert.Equal(param1.Name, outputParam.Name);
        Assert.Equal(param1.Description, outputParam.Description);
        Assert.Equal(param1.IsRequired, outputParam.IsRequired);
    }
}
