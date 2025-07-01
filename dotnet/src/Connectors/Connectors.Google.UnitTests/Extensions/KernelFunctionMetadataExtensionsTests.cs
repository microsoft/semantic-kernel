// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Google;
using Xunit;

#pragma warning disable CA1812 // Uninstantiated internal types

namespace SemanticKernel.Connectors.Google.UnitTests.Extensions;

/// <summary>
/// Unit tests for <see cref="GeminiKernelFunctionMetadataExtensions"/> class.
/// </summary>
public sealed class KernelFunctionMetadataExtensionsTests
{
    [Fact]
    public void ItCanConvertToGeminiFunctionNoParameters()
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
        var result = sut.ToGeminiFunction();

        // Assert
        Assert.Equal(sut.Name, result.FunctionName);
        Assert.Equal(sut.PluginName, result.PluginName);
        Assert.Equal(sut.Description, result.Description);
        Assert.Equal($"{sut.PluginName}{GeminiFunction.NameSeparator}{sut.Name}", result.FullyQualifiedName);

        Assert.NotNull(result.ReturnParameter);
        Assert.Equal("retDesc", result.ReturnParameter.Description);
        Assert.Equivalent(KernelJsonSchema.Parse("""{"type": "object" }"""), result.ReturnParameter.Schema);
        Assert.Null(result.ReturnParameter.ParameterType);
    }

    [Fact]
    public void ItCanConvertToGeminiFunctionNoPluginName()
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
        var result = sut.ToGeminiFunction();

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
    [InlineData(null)]
    [InlineData("""{"type":"integer"}""")]
    public void ItCanConvertToGeminiFunctionWithParameter(string? schema)
    {
        // Arrange
        var param1 = new KernelParameterMetadata("param1")
        {
            Description = "This is param1",
            DefaultValue = "1",
            ParameterType = typeof(int),
            IsRequired = false,
            Schema = schema is not null ? KernelJsonSchema.Parse(schema) : null,
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
        var result = sut.ToGeminiFunction();
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
    public void ItCanConvertToGeminiFunctionWithParameterNoType()
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
        var result = sut.ToGeminiFunction();
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
    public void ItCanConvertToGeminiFunctionWithNoReturnParameterType()
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
        var result = sut.ToGeminiFunction();
        var outputParam = result.Parameters![0];

        // Assert
        Assert.Equal(param1.Name, outputParam.Name);
        Assert.Equal(param1.Description, outputParam.Description);
        Assert.Equal(param1.IsRequired, outputParam.IsRequired);
        Assert.NotNull(outputParam.Schema);
        Assert.Equal("integer", outputParam.Schema.RootElement.GetProperty("type").GetString());
    }

    [Fact]
    public void ItCanCreateValidGeminiFunctionManualForPlugin()
    {
        // Arrange
        var kernel = new Kernel();
        kernel.Plugins.AddFromType<MyPlugin>("MyPlugin");

        var functionMetadata = kernel.Plugins["MyPlugin"].First().Metadata;

        var sut = functionMetadata.ToGeminiFunction();

        // Act
        var result = sut.ToFunctionDeclaration();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(
            """{"type":"object","required":["parameter1","parameter2","parameter3"],"properties":{"parameter1":{"description":"String parameter","type":"string"},"parameter2":{"description":"Enum parameter","type":"string","enum":["Value1","Value2"]},"parameter3":{"description":"DateTime parameter","type":"string"}}}""",
            JsonSerializer.Serialize(result.Parameters)
        );
    }

    [Fact]
    public void ItCanCreateValidGeminiFunctionManualForPrompt()
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
        var sut = functionMetadata.ToGeminiFunction();

        // Act
        var result = sut.ToFunctionDeclaration();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(
            """{"type":"object","required":["parameter1","parameter2"],"properties":{"parameter1":{"type":"string","description":"String parameter"},"parameter2":{"enum":["Value1","Value2"],"description":"Enum parameter","type":"string"}}}""",
            JsonSerializer.Serialize(result.Parameters)
        );
    }

    private enum MyEnum
    {
        Value1,
        Value2
    }

    private sealed class MyPlugin
    {
        [KernelFunction]
        [Description("My sample function.")]
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
