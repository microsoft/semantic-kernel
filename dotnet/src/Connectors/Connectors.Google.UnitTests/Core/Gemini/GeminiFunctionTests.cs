// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.Gemini;

public sealed class GeminiFunctionTests
{
    [Theory]
    [InlineData(null, null, "", "")]
    [InlineData("name", "description", "name", "description")]
    public void ItInitializesGeminiFunctionParameterCorrectly(string? name, string? description, string expectedName, string expectedDescription)
    {
        // Arrange & Act
        var schema = KernelJsonSchema.Parse("""{"type": "object" }""");
        var functionParameter = new GeminiFunctionParameter(name, description, true, typeof(string), schema);

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
    public void ItInitializesGeminiFunctionReturnParameterCorrectly(string? description, string expectedDescription)
    {
        // Arrange & Act
        var schema = KernelJsonSchema.Parse("""{"type": "object" }""");
        var functionParameter = new GeminiFunctionReturnParameter(description, typeof(string), schema);

        // Assert
        Assert.Equal(expectedDescription, functionParameter.Description);
        Assert.Equal(typeof(string), functionParameter.ParameterType);
        Assert.Same(schema, functionParameter.Schema);
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionWithNoPluginName()
    {
        // Arrange
        GeminiFunction sut = KernelFunctionFactory.CreateFromMethod(
            () => { }, "myfunc", "This is a description of the function.").Metadata.ToGeminiFunction();

        // Act
        GeminiTool.FunctionDeclaration result = sut.ToFunctionDeclaration();

        // Assert
        Assert.Equal(sut.FunctionName, result.Name);
        Assert.Equal(sut.Description, result.Description);
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionWithNullParameters()
    {
        // Arrange
        GeminiFunction sut = new("plugin", "function", "description", null, null);

        // Act
        var result = sut.ToFunctionDeclaration();

        // Assert
        Assert.NotNull(result.Parameters);
        Assert.Equal(JsonValueKind.Null, result.Parameters.Value.ValueKind);
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionWithPluginName()
    {
        // Arrange
        GeminiFunction sut = KernelPluginFactory.CreateFromFunctions("myplugin", new[]
        {
            KernelFunctionFactory.CreateFromMethod(() => { }, "myfunc", "This is a description of the function.")
        }).GetFunctionsMetadata()[0].ToGeminiFunction();

        // Act
        GeminiTool.FunctionDeclaration result = sut.ToFunctionDeclaration();

        // Assert
        Assert.Equal($"myplugin{GeminiFunction.NameSeparator}myfunc", result.Name);
        Assert.Equal(sut.Description, result.Description);
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionsWithParameterTypesAndReturnParameterType()
    {
        string expectedParameterSchema = """
                                         {   "type": "object",
                                         "required": ["param1", "param2"],
                                         "properties": {
                                         "param1": { "description": "String param 1", "type": "string" },
                                         "param2": { "description": "Int param 2" , "type": "integer"}   } }
                                         """;

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("Tests", new[]
        {
            KernelFunctionFactory.CreateFromMethod(
                [return: Description("My test Result")]
                ([Description("String param 1")] string param1, [Description("Int param 2")] int param2) => "",
                "TestFunction",
                "My test function")
        });

        GeminiFunction sut = plugin.GetFunctionsMetadata()[0].ToGeminiFunction();

        GeminiTool.FunctionDeclaration functionDefinition = sut.ToFunctionDeclaration();

        Assert.NotNull(functionDefinition);
        Assert.Equal($"Tests{GeminiFunction.NameSeparator}TestFunction", functionDefinition.Name);
        Assert.Equal("My test function", functionDefinition.Description);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse(expectedParameterSchema)),
            JsonSerializer.Serialize(functionDefinition.Parameters));
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionsWithParameterTypesAndNoReturnParameterType()
    {
        string expectedParameterSchema = """
                                         {   "type": "object",
                                         "required": ["param1", "param2"],
                                         "properties": {
                                         "param1": { "description": "String param 1", "type": "string" },
                                         "param2": { "description": "Int param 2", "type": "integer"}   } }
                                         """;

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("Tests", new[]
        {
            KernelFunctionFactory.CreateFromMethod(
                [return: Description("My test Result")]
                ([Description("String param 1")] string param1, [Description("Int param 2")] int param2) => { },
                "TestFunction",
                "My test function")
        });

        GeminiFunction sut = plugin.GetFunctionsMetadata()[0].ToGeminiFunction();

        GeminiTool.FunctionDeclaration functionDefinition = sut.ToFunctionDeclaration();

        Assert.NotNull(functionDefinition);
        Assert.Equal($"Tests{GeminiFunction.NameSeparator}TestFunction", functionDefinition.Name);
        Assert.Equal("My test function", functionDefinition.Description);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse(expectedParameterSchema)),
            JsonSerializer.Serialize(functionDefinition.Parameters));
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionsWithNoParameterTypes()
    {
        // Arrange
        GeminiFunction f = KernelFunctionFactory.CreateFromMethod(
            () => { },
            parameters: new[] { new KernelParameterMetadata("param1") }).Metadata.ToGeminiFunction();

        // Act
        GeminiTool.FunctionDeclaration result = f.ToFunctionDeclaration();

        // Assert
        Assert.Equal(
            """{"type":"object","required":[],"properties":{"param1":{"type":"string"}}}""",
            JsonSerializer.Serialize(result.Parameters));
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionsWithNoParameterTypesButWithDescriptions()
    {
        // Arrange
        GeminiFunction f = KernelFunctionFactory.CreateFromMethod(
            () => { },
            parameters: new[] { new KernelParameterMetadata("param1") { Description = "something neat" } }).Metadata.ToGeminiFunction();

        // Act
        GeminiTool.FunctionDeclaration result = f.ToFunctionDeclaration();

        // Assert
        Assert.Equal(
            """{"type":"object","required":[],"properties":{"param1":{"description":"something neat","type":"string"}}}""",
            JsonSerializer.Serialize(result.Parameters));
    }
}
