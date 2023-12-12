// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

#pragma warning disable CA1812 // Uninstantiated internal types

namespace SemanticKernel.Connectors.UnitTests.OpenAI.FunctionCalling;

public sealed class KernelFunctionMetadataExtensionsTests
{
    [Fact]
    public void ItCanConvertToOpenAIFunctionNoParameters()
    {
        // Arrange
        var sut = new KernelFunctionMetadata("foo")
        {
            PluginName = "bar",
            Description = "baz",
            ReturnParameter = new KernelReturnParameterMetadata { Description = "retDesc", Schema = KernelJsonSchema.Parse("\"schema\"") },
        };

        // Act
        var result = sut.ToOpenAIFunction();

        // Assert
        Assert.Equal(sut.Name, result.FunctionName);
        Assert.Equal(sut.PluginName, result.PluginName);
        Assert.Equal(sut.Description, result.Description);
        Assert.Equal($"{sut.PluginName}_{sut.Name}", result.FullyQualifiedName);

        Assert.NotNull(result.ReturnParameter);
        Assert.Equal("retDesc", result.ReturnParameter.Description);
        Assert.Equivalent(KernelJsonSchema.Parse("\"schema\""), result.ReturnParameter.Schema);
        Assert.Null(result.ReturnParameter.ParameterType);
    }

    [Fact]
    public void ItCanConvertToOpenAIFunctionNoPluginName()
    {
        // Arrange
        var sut = new KernelFunctionMetadata("foo")
        {
            PluginName = string.Empty,
            Description = "baz",
            ReturnParameter = new KernelReturnParameterMetadata { Description = "retDesc", Schema = KernelJsonSchema.Parse("\"schema\"") },
        };

        // Act
        var result = sut.ToOpenAIFunction();

        // Assert
        Assert.Equal(sut.Name, result.FunctionName);
        Assert.Equal(sut.PluginName, result.PluginName);
        Assert.Equal(sut.Description, result.Description);
        Assert.Equal(sut.Name, result.FullyQualifiedName);

        Assert.NotNull(result.ReturnParameter);
        Assert.Equal("retDesc", result.ReturnParameter.Description);
        Assert.Equivalent(KernelJsonSchema.Parse("\"schema\""), result.ReturnParameter.Schema);
        Assert.Null(result.ReturnParameter.ParameterType);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void ItCanConvertToOpenAIFunctionWithParameter(bool withSchema)
    {
        // Arrange
        var param1 = new KernelParameterMetadata("param1")
        {
            Description = "This is param1",
            DefaultValue = "1",
            ParameterType = typeof(int),
            IsRequired = false,
            Schema = withSchema ? KernelJsonSchema.Parse("{\"type\":\"integer\"}") : null,
        };

        var sut = new KernelFunctionMetadata("foo")
        {
            PluginName = "bar",
            Description = "baz",
            Parameters = new[] { param1 },
            ReturnParameter = new KernelReturnParameterMetadata { Description = "retDesc", Schema = KernelJsonSchema.Parse("\"schema\"") },
        };

        // Act
        var result = sut.ToOpenAIFunction();
        var outputParam = result.Parameters![0];

        // Assert
        Assert.Equal(param1.Name, outputParam.Name);
        Assert.Equal("This is param1 (default value: 1)", outputParam.Description);
        Assert.Equal(param1.IsRequired, outputParam.IsRequired);
        Assert.NotNull(outputParam.Schema);
        Assert.Equal("integer", outputParam.Schema.RootElement.GetProperty("type").GetString());

        Assert.NotNull(result.ReturnParameter);
        Assert.Equal("retDesc", result.ReturnParameter.Description);
        Assert.Equivalent(KernelJsonSchema.Parse("\"schema\""), result.ReturnParameter.Schema);
        Assert.Null(result.ReturnParameter.ParameterType);
    }

    [Fact]
    public void ItCanConvertToOpenAIFunctionWithParameterNoType()
    {
        // Arrange
        var param1 = new KernelParameterMetadata("param1")
        {
            Description = "This is param1"
        };

        var sut = new KernelFunctionMetadata("foo")
        {
            PluginName = "bar",
            Description = "baz",
            Parameters = new[] { param1 },
            ReturnParameter = new KernelReturnParameterMetadata { Description = "retDesc", Schema = KernelJsonSchema.Parse("\"schema\"") },
        };

        // Act
        var result = sut.ToOpenAIFunction();
        var outputParam = result.Parameters![0];

        // Assert
        Assert.Equal(param1.Name, outputParam.Name);
        Assert.Equal(param1.Description, outputParam.Description);
        Assert.Equal(param1.IsRequired, outputParam.IsRequired);

        Assert.NotNull(result.ReturnParameter);
        Assert.Equal("retDesc", result.ReturnParameter.Description);
        Assert.Equivalent(KernelJsonSchema.Parse("\"schema\""), result.ReturnParameter.Schema);
        Assert.Null(result.ReturnParameter.ParameterType);
    }

    [Fact]
    public void ItCanConvertToOpenAIFunctionWithNoReturnParameterType()
    {
        // Arrange
        var param1 = new KernelParameterMetadata("param1")
        {
            Description = "This is param1",
            ParameterType = typeof(int),
        };

        var sut = new KernelFunctionMetadata("foo")
        {
            PluginName = "bar",
            Description = "baz",
            Parameters = new[] { param1 },
        };

        // Act
        var result = sut.ToOpenAIFunction();
        var outputParam = result.Parameters![0];

        // Assert
        Assert.Equal(param1.Name, outputParam.Name);
        Assert.Equal(param1.Description, outputParam.Description);
        Assert.Equal(param1.IsRequired, outputParam.IsRequired);
        Assert.NotNull(outputParam.Schema);
        Assert.Equal("integer", outputParam.Schema.RootElement.GetProperty("type").GetString());
    }

    [Fact]
    public void ItCanCreateValidOpenAIFunctionManualForPlugin()
    {
        // Arrange
        var kernel = new Kernel();
        kernel.Plugins.AddFromType<MyPlugin>("MyPlugin");

        var functionMetadata = kernel.Plugins["MyPlugin"].First().Metadata;

        var sut = functionMetadata.ToOpenAIFunction();

        // Act
        var result = sut.ToFunctionDefinition();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(
            "{\"type\":\"object\",\"required\":[\"parameter1\",\"parameter2\",\"parameter3\"],\"properties\":{\"parameter1\":{\"type\":\"string\",\"description\":\"String parameter\"},\"parameter2\":{\"enum\":[\"Value1\",\"Value2\"],\"description\":\"Enum parameter\"},\"parameter3\":{\"type\":\"string\",\"format\":\"date-time\",\"description\":\"DateTime parameter\"}}}",
            result.Parameters.ToString()
        );
    }

    [Fact]
    public void ItCanCreateValidOpenAIFunctionManualForPrompt()
    {
        // Arrange
        var promptTemplateConfig = new PromptTemplateConfig("Hello AI")
        {
            Description = "My sample function."
        };
        promptTemplateConfig.InputVariables.Add(new InputVariable
        {
            Name = "parameter1",
            Description = "String parameter",
            JsonSchema = "{\"type\":\"string\",\"description\":\"String parameter\"}"
        });
        promptTemplateConfig.InputVariables.Add(new InputVariable
        {
            Name = "parameter2",
            Description = "Enum parameter",
            JsonSchema = "{\"enum\":[\"Value1\",\"Value2\"],\"description\":\"Enum parameter\"}"
        });
        var function = KernelFunctionFactory.CreateFromPrompt(promptTemplateConfig);
        var functionMetadata = function.Metadata;
        var sut = functionMetadata.ToOpenAIFunction();

        // Act
        var result = sut.ToFunctionDefinition();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(
            "{\"type\":\"object\",\"required\":[\"parameter1\",\"parameter2\"],\"properties\":{\"parameter1\":{\"type\":\"string\",\"description\":\"String parameter\"},\"parameter2\":{\"enum\":[\"Value1\",\"Value2\"],\"description\":\"Enum parameter\"}}}",
            result.Parameters.ToString()
        );
    }

    private enum MyEnum
    {
        Value1,
        Value2
    }

    private sealed class MyPlugin
    {
        [KernelFunction, Description("My sample function.")]
        public string MyFunction(
            [Description("String parameter")] string parameter1,
            [Description("Enum parameter")] MyEnum parameter2,
            [Description("DateTime parameter")] DateTime parameter3
            )
        {
            return "return";
        }
    }
}
