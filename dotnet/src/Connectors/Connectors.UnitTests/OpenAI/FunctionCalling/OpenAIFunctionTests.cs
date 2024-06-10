// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text.Json;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.FunctionCalling;

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

    [Fact]
    public void ItCanConvertToFunctionDefinitionWithNoPluginName()
    {
        // Arrange
        OpenAIFunction sut = KernelFunctionFactory.CreateFromMethod(() => { }, "myfunc", "This is a description of the function.").Metadata.ToOpenAIFunction();

        // Act
        FunctionDefinition result = sut.ToFunctionDefinition();

        // Assert
        Assert.Equal(sut.FunctionName, result.Name);
        Assert.Equal(sut.Description, result.Description);
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionWithNullParameters()
    {
        // Arrange 
        OpenAIFunction sut = new("plugin", "function", "description", null, null);

        // Act
        var result = sut.ToFunctionDefinition();

        // Assert
        Assert.Equal("{\"type\":\"object\",\"required\":[],\"properties\":{}}", result.Parameters.ToString());
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionWithPluginName()
    {
        // Arrange
        OpenAIFunction sut = KernelPluginFactory.CreateFromFunctions("myplugin", new[]
        {
            KernelFunctionFactory.CreateFromMethod(() => { }, "myfunc", "This is a description of the function.")
        }).GetFunctionsMetadata()[0].ToOpenAIFunction();

        // Act
        FunctionDefinition result = sut.ToFunctionDefinition();

        // Assert
        Assert.Equal("myplugin-myfunc", result.Name);
        Assert.Equal(sut.Description, result.Description);
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionsWithParameterTypesAndReturnParameterType()
    {
        string expectedParameterSchema = """{"type":"object","required":["param1","param2"],"properties":{"param1":{"type":"string","description":"String param 1"},"param2":{"type":"integer","description":"Int param 2"},"param3":{"type":"number","description":"double param 2 (default value: 34.8)"}}}""";

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("Tests", new[]
        {
            KernelFunctionFactory.CreateFromMethod(
                [return: Description("My test Result")] ([Description("String param 1")] string param1, [Description("Int param 2")] int param2, [Description("double param 2")] double param3 = 34.8) => "",
                "TestFunction",
                "My test function")
        });

        OpenAIFunction sut = plugin.GetFunctionsMetadata()[0].ToOpenAIFunction();

        FunctionDefinition functionDefinition = sut.ToFunctionDefinition();

        var exp = JsonSerializer.Serialize(KernelJsonSchema.Parse(expectedParameterSchema));
        var act = JsonSerializer.Serialize(KernelJsonSchema.Parse(functionDefinition.Parameters));

        Assert.NotNull(functionDefinition);
        Assert.Equal("Tests-TestFunction", functionDefinition.Name);
        Assert.Equal("My test function", functionDefinition.Description);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse(expectedParameterSchema)), JsonSerializer.Serialize(KernelJsonSchema.Parse(functionDefinition.Parameters)));
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionsWithParameterTypesAndNoReturnParameterType()
    {
        string expectedParameterSchema = """{"type":"object","required":["param1","param2"],"properties":{"param1":{"type":"string","description":"String param 1"},"param2":{"type":"integer","description":"Int param 2"},"param3":{"type":"number","description":"double param 2 (default value: 34.8)"}}}""";

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("Tests", new[]
        {
            KernelFunctionFactory.CreateFromMethod(
                [return: Description("My test Result")] ([Description("String param 1")] string param1, [Description("Int param 2")] int param2, [Description("double param 2")] double param3 = 34.8) => { },
                "TestFunction",
                "My test function")
        });

        OpenAIFunction sut = plugin.GetFunctionsMetadata()[0].ToOpenAIFunction();

        FunctionDefinition functionDefinition = sut.ToFunctionDefinition();

        Assert.NotNull(functionDefinition);
        Assert.Equal("Tests-TestFunction", functionDefinition.Name);
        Assert.Equal("My test function", functionDefinition.Description);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse(expectedParameterSchema)), JsonSerializer.Serialize(KernelJsonSchema.Parse(functionDefinition.Parameters)));
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionsWithNoParameterTypes()
    {
        // Arrange
        OpenAIFunction f = KernelFunctionFactory.CreateFromMethod(
            () => { },
            parameters: [new KernelParameterMetadata("param1")]).Metadata.ToOpenAIFunction();

        // Act
        FunctionDefinition result = f.ToFunctionDefinition();
        ParametersData pd = JsonSerializer.Deserialize<ParametersData>(result.Parameters.ToString())!;

        // Assert
        Assert.NotNull(pd.properties);
        Assert.Single(pd.properties);
        Assert.Equal(
            JsonSerializer.Serialize(KernelJsonSchema.Parse("""{ "type":"string" }""")),
            JsonSerializer.Serialize(pd.properties.First().Value.RootElement));
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionsWithNoParameterTypesButWithDescriptions()
    {
        // Arrange
        OpenAIFunction f = KernelFunctionFactory.CreateFromMethod(
            () => { },
            parameters: [new KernelParameterMetadata("param1") { Description = "something neat" }]).Metadata.ToOpenAIFunction();

        // Act
        FunctionDefinition result = f.ToFunctionDefinition();
        ParametersData pd = JsonSerializer.Deserialize<ParametersData>(result.Parameters.ToString())!;

        // Assert
        Assert.NotNull(pd.properties);
        Assert.Single(pd.properties);
        Assert.Equal(
            JsonSerializer.Serialize(KernelJsonSchema.Parse("""{ "type":"string", "description":"something neat" }""")),
            JsonSerializer.Serialize(pd.properties.First().Value.RootElement));
    }

    [Fact]
    public void ItCanConvertToFunctionMetadata()
    {
        // Arrange
        OpenAIFunction f = new("p1", "f1", "description", new[]
        {
            new OpenAIFunctionParameter("param1", "param1 description", true, typeof(string), KernelJsonSchema.Parse("""{ "type":"string" }""")),
            new OpenAIFunctionParameter("param2", "param2 description", false, typeof(int), KernelJsonSchema.Parse("""{ "type":"integer" }""")),
        },
        new OpenAIFunctionReturnParameter("return description", typeof(string), KernelJsonSchema.Parse("""{ "type":"string" }""")));

        // Act
        KernelFunctionMetadata result = f.ToKernelFunctionMetadata();

        // Assert
        Assert.Equal("p1", result.PluginName);
        Assert.Equal("f1", result.Name);
        Assert.Equal("description", result.Description);

        Assert.Equal(2, result.Parameters.Count);

        var param1 = result.Parameters[0];
        Assert.Equal("param1", param1.Name);
        Assert.Equal("param1 description", param1.Description);
        Assert.True(param1.IsRequired);
        Assert.Equal(typeof(string), param1.ParameterType);
        Assert.Equal("string", param1.Schema?.RootElement.GetProperty("type").GetString());

        var param2 = result.Parameters[1];
        Assert.Equal("param2", param2.Name);
        Assert.Equal("param2 description", param2.Description);
        Assert.False(param2.IsRequired);
        Assert.Equal(typeof(int), param2.ParameterType);
        Assert.Equal("integer", param2.Schema?.RootElement.GetProperty("type").GetString());

        Assert.NotNull(result.ReturnParameter);
        Assert.Equal("return description", result.ReturnParameter.Description);
        Assert.Equal(typeof(string), result.ReturnParameter.ParameterType);
        Assert.Equal("string", result.ReturnParameter.Schema?.RootElement.GetProperty("type").GetString());
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
