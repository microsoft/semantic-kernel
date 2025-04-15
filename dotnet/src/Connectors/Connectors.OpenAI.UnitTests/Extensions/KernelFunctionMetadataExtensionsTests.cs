// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

#pragma warning disable CA1812 // Uninstantiated internal types

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Extensions;

public sealed class KernelFunctionMetadataExtensionsTests
{
    [Fact]
    public void ItCanConvertToAzureOpenAIFunctionNoParameters()
    {
        // Arrange
        var sut = new KernelFunctionMetadata("foo")
        {
            PluginName = "bar",
            Description = "baz",
            ReturnParameter = new KernelReturnParameterMetadata
            {
                Description = "retDesc",
                Schema = KernelJsonSchema.Parse("""{"type": "object" }"""),
            }
        };

        // Act
        var result = sut.ToOpenAIFunction();

        // Assert
        Assert.Equal(sut.Name, result.FunctionName);
        Assert.Equal(sut.PluginName, result.PluginName);
        Assert.Equal(sut.Description, result.Description);
        Assert.Equal($"{sut.PluginName}-{sut.Name}", result.FullyQualifiedName);

        Assert.NotNull(result.ReturnParameter);
        Assert.Equal("retDesc", result.ReturnParameter.Description);
        Assert.Equivalent(KernelJsonSchema.Parse("""{"type": "object" }"""), result.ReturnParameter.Schema);
        Assert.Null(result.ReturnParameter.ParameterType);
    }

    [Fact]
    public void ItCanConvertToAzureOpenAIFunctionNoPluginName()
    {
        // Arrange
        var sut = new KernelFunctionMetadata("foo")
        {
            PluginName = string.Empty,
            Description = "baz",
            ReturnParameter = new KernelReturnParameterMetadata
            {
                Description = "retDesc",
                Schema = KernelJsonSchema.Parse("""{"type": "object" }"""),
            }
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
        Assert.Equivalent(KernelJsonSchema.Parse("""{"type": "object" }"""), result.ReturnParameter.Schema);
        Assert.Null(result.ReturnParameter.ParameterType);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void ItCanConvertToAzureOpenAIFunctionWithParameter(bool withSchema)
    {
        // Arrange
        var param1 = new KernelParameterMetadata("param1")
        {
            Description = "This is param1",
            DefaultValue = "1",
            ParameterType = typeof(int),
            IsRequired = false,
            Schema = withSchema ? KernelJsonSchema.Parse("""{"type":"integer"}""") : null,
        };

        var sut = new KernelFunctionMetadata("foo")
        {
            PluginName = "bar",
            Description = "baz",
            Parameters = [param1],
            ReturnParameter = new KernelReturnParameterMetadata
            {
                Description = "retDesc",
                Schema = KernelJsonSchema.Parse("""{"type": "object" }"""),
            }
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
        Assert.Equivalent(KernelJsonSchema.Parse("""{"type": "object" }"""), result.ReturnParameter.Schema);
        Assert.Null(result.ReturnParameter.ParameterType);
    }

    [Fact]
    public void ItCanConvertToAzureOpenAIFunctionWithParameterNoType()
    {
        // Arrange
        var param1 = new KernelParameterMetadata("param1") { Description = "This is param1" };

        var sut = new KernelFunctionMetadata("foo")
        {
            PluginName = "bar",
            Description = "baz",
            Parameters = [param1],
            ReturnParameter = new KernelReturnParameterMetadata
            {
                Description = "retDesc",
                Schema = KernelJsonSchema.Parse("""{"type": "object" }"""),
            }
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
        Assert.Equivalent(KernelJsonSchema.Parse("""{"type": "object" }"""), result.ReturnParameter.Schema);
        Assert.Null(result.ReturnParameter.ParameterType);
    }

    [Fact]
    public void ItCanConvertToAzureOpenAIFunctionWithNoReturnParameterType()
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
            Parameters = [param1],
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

    [InlineData(false)]
    [InlineData(true)]
    [Theory]
    public void ItCanCreateValidAzureOpenAIFunctionManualForPlugin(bool strict)
    {
        // Arrange
        var kernel = new Kernel();
        kernel.Plugins.AddFromType<MyPlugin>("MyPlugin");

        var functionMetadata = kernel.Plugins["MyPlugin"].First().Metadata;

        var sut = functionMetadata.ToOpenAIFunction();

        // Act
        var result = sut.ToFunctionDefinition(strict);

        // Assert
        Assert.NotNull(result);
        var parametersResult = result.FunctionParameters.ToString();
        if (strict)
        {
            Assert.Equal(
                """{"type":"object","required":["parameter1","parameter2","parameter3"],"properties":{"parameter1":{"description":"String parameter","type":"string"},"parameter2":{"description":"Enum parameter","type":"string","enum":["Value1","Value2"]},"parameter3":{"description":"DateTime parameter","type":"string"}},"additionalProperties":false}""",
                parametersResult
            );
        }
        else
        {
            Assert.Equal(
                """{"type":"object","required":["parameter1","parameter2","parameter3"],"properties":{"parameter1":{"description":"String parameter","type":"string"},"parameter2":{"description":"Enum parameter","type":"string","enum":["Value1","Value2"]},"parameter3":{"description":"DateTime parameter","type":"string"}}}""",
                parametersResult
            );
        }
    }

    [InlineData(false)]
    [InlineData(true)]
    [Theory]
    public void ItCanCreateValidAzureOpenAIFunctionManualForPrompt(bool strict)
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
            JsonSchema = """{"type":"string","description":"String parameter"}"""
        });
        promptTemplateConfig.InputVariables.Add(new InputVariable
        {
            Name = "parameter2",
            Description = "Enum parameter",
            JsonSchema = """{"enum":["Value1","Value2"],"description":"Enum parameter"}"""
        });
        var function = KernelFunctionFactory.CreateFromPrompt(promptTemplateConfig);
        var functionMetadata = function.Metadata;
        var sut = functionMetadata.ToOpenAIFunction();

        // Act
        var result = sut.ToFunctionDefinition(strict);

        // Assert
        Assert.NotNull(result);
        var parametersResult = result.FunctionParameters.ToString();
        if (strict)
        {
            Assert.Equal(
                """{"type":"object","required":["parameter1","parameter2"],"properties":{"parameter1":{"type":"string","description":"String parameter"},"parameter2":{"enum":["Value1","Value2"],"description":"Enum parameter"}},"additionalProperties":false}""",
                parametersResult
            );
        }
        else
        {
            Assert.Equal(
                """{"type":"object","required":["parameter1","parameter2"],"properties":{"parameter1":{"type":"string","description":"String parameter"},"parameter2":{"enum":["Value1","Value2"],"description":"Enum parameter"}}}""",
                parametersResult
        );
        }
    }

    [InlineData(false)]
    [InlineData(true)]
    [Theory]
    public void ItCanCreateValidAzureOpenAIFunctionManualForPromptWithNestedSchema(bool strict)
    {
        // Arrange
        var promptTemplateConfig = new PromptTemplateConfig("Hello AI")
        {
            Description = "My sample function."
        };
        promptTemplateConfig.InputVariables.Add(new InputVariable
        {
            Name = "parameter1",
            Description = "Object parameter",
            JsonSchema = """{"type":"object","description":"A user of the application","properties":{"name":{"type":"string","description":"The name of the user"},"age":{"type":"integer","description":"The age of the user","minimum":0,"nullable":true}},"additionalProperties":true,"required":["name"]}"""
        });
        var function = KernelFunctionFactory.CreateFromPrompt(promptTemplateConfig);
        var functionMetadata = function.Metadata;
        var sut = functionMetadata.ToOpenAIFunction();

        // Act
        var result = sut.ToFunctionDefinition(strict);

        // Assert
        Assert.NotNull(result);
        var parametersResult = result.FunctionParameters.ToString();
        if (strict)
        {
            Assert.Equal(
                """{"type":"object","required":["parameter1"],"properties":{"parameter1":{"type":"object","description":"A user of the application","properties":{"name":{"type":"string","description":"The name of the user"},"age":{"type":["integer","null"],"description":"The age of the user"}},"additionalProperties":false,"required":["name","age"]}},"additionalProperties":false}""",
                parametersResult
            );
        }
        else
        {
            Assert.Equal(
                """{"type":"object","required":["parameter1"],"properties":{"parameter1":{"type":"object","description":"A user of the application","properties":{"name":{"type":"string","description":"The name of the user"},"age":{"type":"integer","description":"The age of the user","minimum":0,"nullable":true}},"additionalProperties":true,"required":["name"]}}}""",
                parametersResult
            );
        }
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
