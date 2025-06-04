// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Core;

public sealed class OpenAIFunctionTests
{
    [Theory]
    [InlineData(null, null, "", "")]
    [InlineData("name", "description", "name", "description")]
    public void ItInitializesOpenAIFunctionParameterCorrectly(string? name, string? description, string expectedName, string expectedDescription)
    {
        // Arrange & Act
        var schema = KernelJsonSchema.Parse("{\"type\": \"object\" }");
        var functionParameter = new OpenAIFunctionParameter(name, description, true, typeof(string), schema);

        // Assert
        Assert.Equal(expectedName, functionParameter.Name);
        Assert.Equal(expectedDescription, functionParameter.Description);
        Assert.True(functionParameter.IsRequired);
        Assert.Equal(typeof(string), functionParameter.ParameterType);
        Assert.Same(schema, functionParameter.Schema);
    }

    [Theory]
    [InlineData(null, "")]
    [InlineData("description", "description")]
    public void ItInitializesOpenAIFunctionReturnParameterCorrectly(string? description, string expectedDescription)
    {
        // Arrange & Act
        var schema = KernelJsonSchema.Parse("{\"type\": \"object\" }");
        var functionParameter = new OpenAIFunctionReturnParameter(description, typeof(string), schema);

        // Assert
        Assert.Equal(expectedDescription, functionParameter.Description);
        Assert.Equal(typeof(string), functionParameter.ParameterType);
        Assert.Same(schema, functionParameter.Schema);
    }

    [InlineData(true)]
    [InlineData(false)]
    [Theory]
    public void ItCanConvertToFunctionDefinitionWithNoPluginName(bool strict)
    {
        // Arrange
        OpenAIFunction sut = KernelFunctionFactory.CreateFromMethod(() => { }, "myfunc", "This is a description of the function.").Metadata.ToOpenAIFunction();

        // Act
        ChatTool result = sut.ToFunctionDefinition(strict);

        // Assert
        Assert.Equal(sut.FunctionName, result.FunctionName);
        Assert.Equal(sut.Description, result.FunctionDescription);
    }

    [InlineData(true)]
    [InlineData(false)]
    [Theory]
    public void ItCanConvertToFunctionDefinitionWithNullParameters(bool strict)
    {
        // Arrange
        OpenAIFunction sut = new("plugin", "function", "description", null, null);

        // Act
        var result = sut.ToFunctionDefinition(strict);

        // Assert
        if (strict)
        {
            Assert.Equal("{\"type\":\"object\",\"required\":[],\"properties\":{},\"additionalProperties\":false}", result.FunctionParameters.ToString());
        }
        else
        {
            Assert.Equal("{\"type\":\"object\",\"required\":[],\"properties\":{}}", result.FunctionParameters.ToString());
        }
    }

    [InlineData(false)]
    [InlineData(true)]
    [Theory]
    public void SetsParametersToRequiredWhenStrict(bool strict)
    {
        var parameters = new List<OpenAIFunctionParameter>
        {
            new ("foo", "bar", false, typeof(string), null),
        };
        OpenAIFunction sut = new("plugin", "function", "description", parameters, null);

        var result = sut.ToFunctionDefinition(strict);

        Assert.Equal(strict, result.FunctionSchemaIsStrict);
        if (strict)
        {
            Assert.Equal("""{"type":"object","required":["foo"],"properties":{"foo":{"description":"bar","type":["string","null"]}},"additionalProperties":false}""", result.FunctionParameters.ToString());
        }
        else
        {
            Assert.Equal("""{"type":"object","required":[],"properties":{"foo":{"description":"bar","type":"string"}}}""", result.FunctionParameters.ToString());
        }
    }

    [InlineData(false)]
    [InlineData(true)]
    [Theory]
    public void ItCanConvertToFunctionDefinitionWithPluginName(bool strict)
    {
        // Arrange
        OpenAIFunction sut = KernelPluginFactory.CreateFromFunctions("myplugin", new[]
        {
            KernelFunctionFactory.CreateFromMethod(() => { }, "myfunc", "This is a description of the function.")
        }).GetFunctionsMetadata()[0].ToOpenAIFunction();

        // Act
        ChatTool result = sut.ToFunctionDefinition(strict);

        // Assert
        Assert.Equal("myplugin-myfunc", result.FunctionName);
        Assert.Equal(sut.Description, result.FunctionDescription);
    }

    [InlineData(false)]
    [InlineData(true)]
    [Theory]
    public void ItCanConvertToFunctionDefinitionsWithParameterTypesAndReturnParameterType(bool strict)
    {
        string expectedParameterSchema = strict ?
        """{   "type": "object",   "required": ["param1", "param2"],   "properties": {     "param1": { "description": "String param 1", "type": "string" },     "param2": { "description": "Int param 2", "type": "integer" }   },"additionalProperties":false } """ :
        """{   "type": "object",   "required": ["param1", "param2"],   "properties": {     "param1": { "description": "String param 1", "type": "string" },     "param2": { "description": "Int param 2", "type": "integer" }   } } """;

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("Tests", new[]
        {
            KernelFunctionFactory.CreateFromMethod(
                [return: Description("My test Result")] ([Description("String param 1")] string param1, [Description("Int param 2")] int param2) => "",
                "TestFunction",
                "My test function")
        });

        OpenAIFunction sut = plugin.GetFunctionsMetadata()[0].ToOpenAIFunction();

        ChatTool functionDefinition = sut.ToFunctionDefinition(strict);

        var exp = JsonSerializer.Serialize(KernelJsonSchema.Parse(expectedParameterSchema));
        var act = JsonSerializer.Serialize(KernelJsonSchema.Parse(functionDefinition.FunctionParameters));

        Assert.NotNull(functionDefinition);
        Assert.Equal("Tests-TestFunction", functionDefinition.FunctionName);
        Assert.Equal("My test function", functionDefinition.FunctionDescription);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse(expectedParameterSchema)), JsonSerializer.Serialize(KernelJsonSchema.Parse(functionDefinition.FunctionParameters)));
    }

    [InlineData(false)]
    [InlineData(true)]
    [Theory]
    public void ItCanConvertToFunctionDefinitionsWithParameterTypesAndNoReturnParameterType(bool strict)
    {
        string expectedParameterSchema = strict ?
        """{   "type": "object",   "required": ["param1", "param2"],   "properties": {     "param1": { "description": "String param 1", "type": "string" },     "param2": { "description": "Int param 2", "type": "integer" }   }, "additionalProperties":false} """ :
        """{   "type": "object",   "required": ["param1", "param2"],   "properties": {     "param1": { "description": "String param 1", "type": "string" },     "param2": { "description": "Int param 2", "type": "integer" }   } } """;

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("Tests", new[]
        {
            KernelFunctionFactory.CreateFromMethod(
                [return: Description("My test Result")] ([Description("String param 1")] string param1, [Description("Int param 2")] int param2) => { },
                "TestFunction",
                "My test function")
        });

        OpenAIFunction sut = plugin.GetFunctionsMetadata()[0].ToOpenAIFunction();

        ChatTool functionDefinition = sut.ToFunctionDefinition(strict);

        Assert.NotNull(functionDefinition);
        Assert.Equal("Tests-TestFunction", functionDefinition.FunctionName);
        Assert.Equal("My test function", functionDefinition.FunctionDescription);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse(expectedParameterSchema)), JsonSerializer.Serialize(KernelJsonSchema.Parse(functionDefinition.FunctionParameters)));
    }

    [InlineData(false)]
    [InlineData(true)]
    [Theory]
    public void ItCanConvertToFunctionDefinitionsWithNoParameterTypes(bool strict)
    {
        // Arrange
        OpenAIFunction f = KernelFunctionFactory.CreateFromMethod(
            () => { },
            parameters: [new KernelParameterMetadata("param1")]).Metadata.ToOpenAIFunction();

        // Act
        ChatTool result = f.ToFunctionDefinition(strict);
        ParametersData pd = JsonSerializer.Deserialize<ParametersData>(result.FunctionParameters.ToString())!;

        // Assert
        Assert.NotNull(pd.properties);
        Assert.Single(pd.properties);
        var expectedSchema = strict ?
        """{ "type":["string","null"] }""" :
        """{ "type":"string" }""";
        Assert.Equal(
            JsonSerializer.Serialize(KernelJsonSchema.Parse(expectedSchema)),
            JsonSerializer.Serialize(pd.properties.First().Value.RootElement));
    }

    [InlineData(false)]
    [InlineData(true)]
    [Theory]
    public void ItCanConvertToFunctionDefinitionsWithNoParameterTypesButWithDescriptions(bool strict)
    {
        // Arrange
        OpenAIFunction f = KernelFunctionFactory.CreateFromMethod(
            () => { },
            parameters: [new KernelParameterMetadata("param1") { Description = "something neat" }]).Metadata.ToOpenAIFunction();

        // Act
        ChatTool result = f.ToFunctionDefinition(strict);
        ParametersData pd = JsonSerializer.Deserialize<ParametersData>(result.FunctionParameters.ToString())!;

        // Assert
        Assert.NotNull(pd.properties);
        Assert.Single(pd.properties);
        var expectedSchema = strict ?
        """{ "description":"something neat", "type":["string","null"] }""" :
        """{ "description":"something neat", "type":"string" }""";
        Assert.Equal(
            JsonSerializer.Serialize(KernelJsonSchema.Parse(expectedSchema)),
            JsonSerializer.Serialize(pd.properties.First().Value.RootElement));
    }

    [InlineData("number", "maximum", "10", false)]
    [InlineData("number", "maximum", "10", true)]
    [InlineData("number", "minimum", "10", false)]
    [InlineData("number", "minimum", "10", true)]
    [InlineData("number", "maxContains", "10", false)]
    [InlineData("number", "maxContains", "10", true)]
    [InlineData("number", "minContains", "10", false)]
    [InlineData("number", "minContains", "10", true)]
    [InlineData("number", "multipleOf", "10", false)]
    [InlineData("number", "multipleOf", "10", true)]
    [InlineData("number", "format", "\"int64\"", false)]
    [InlineData("number", "format", "\"int64\"", true)]
    [InlineData("array", "maxItems", "5", false)]
    [InlineData("array", "maxItems", "5", true)]
    [InlineData("array", "minItems", "5", false)]
    [InlineData("array", "minItems", "5", true)]
    [InlineData("array", "contains", "5", false)]
    [InlineData("array", "contains", "5", true)]
    [InlineData("array", "uniqueItems", "true", false)]
    [InlineData("array", "uniqueItems", "true", true)]
    [InlineData("string", "minLength", "5", false)]
    [InlineData("string", "minLength", "5", true)]
    [InlineData("string", "maxLength", "5", false)]
    [InlineData("string", "maxLength", "5", true)]
    [InlineData("object", "maxProperties", "5", false)]
    [InlineData("object", "maxProperties", "5", true)]
    [InlineData("object", "minProperties", "5", false)]
    [InlineData("object", "minProperties", "5", true)]
    [InlineData("object", "pattern", "\"foo*\"", false)]
    [InlineData("object", "pattern", "\"foo*\"", true)]
    [InlineData("object", "patternProperties", "\"foo*\"", false)]
    [InlineData("object", "patternProperties", "\"foo*\"", true)]
    [InlineData("object", "propertyNames", """{ "maxLength": 3, "minLength": 3 }""", false)]
    [InlineData("object", "propertyNames", """{ "maxLength": 3, "minLength": 3 }""", true)]
    [InlineData("object", "unevaluatedItems", "true", false)]
    [InlineData("object", "unevaluatedItems", "true", true)]
    [InlineData("object", "unevaluatedProperties", "true", false)]
    [InlineData("object", "unevaluatedProperties", "true", true)]
    [Theory]
    public void ItCleansUpRestrictedSchemaKeywords(string typeName, string keyword, string keywordValue, bool strict)
    {
        // Arrange
        var parameterSchema = KernelJsonSchema.Parse($$"""{ "description":"something neat", "type":"{{typeName}}", "{{keyword}}":{{keywordValue}} }""");
        OpenAIFunction f = KernelFunctionFactory.CreateFromMethod(
            () => { },
            parameters: [new KernelParameterMetadata("param1") { Description = "something neat", Schema = parameterSchema }]).Metadata.ToOpenAIFunction();

        // Act
        ChatTool result = f.ToFunctionDefinition(strict);
        ParametersData pd = JsonSerializer.Deserialize<ParametersData>(result.FunctionParameters.ToString())!;

        // Assert
        Assert.NotNull(pd.properties);
        Assert.Single(pd.properties);
        var resultSchema = JsonSerializer.Serialize(pd.properties.First().Value.RootElement);
        if (strict)
        {
            Assert.DoesNotContain(keyword, resultSchema, StringComparison.OrdinalIgnoreCase);
        }
        else
        {
            Assert.Contains(keyword, resultSchema, StringComparison.OrdinalIgnoreCase);
        }
    }

#pragma warning disable CA1812 // uninstantiated internal class
    private sealed class ParametersData
    {
        public string? type { get; set; }
        public string[]? required { get; set; }
        public Dictionary<string, KernelJsonSchema>? properties { get; set; }
    }
#pragma warning restore CA1812
}
