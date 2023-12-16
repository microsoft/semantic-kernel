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
        Assert.Equal("myplugin_myfunc", result.Name);
        Assert.Equal(sut.Description, result.Description);
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionsWithParameterTypesAndReturnParameterType()
    {
        string expectedParameterSchema = "{   \"type\": \"object\",   \"required\": [\"param1\", \"param2\"],   \"properties\": {     \"param1\": { \"type\": \"string\", \"description\": \"String param 1\" },     \"param2\": { \"type\": \"integer\", \"description\": \"Int param 2\" }   } } ";

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("Tests", new[]
        {
            KernelFunctionFactory.CreateFromMethod(
                [return: Description("My test Result")] ([Description("String param 1")] string param1, [Description("Int param 2")] int param2) => "",
                "TestFunction",
                "My test function")
        });

        OpenAIFunction sut = plugin.GetFunctionsMetadata()[0].ToOpenAIFunction();

        FunctionDefinition functionDefinition = sut.ToFunctionDefinition();

        var exp = JsonSerializer.Serialize(KernelJsonSchema.Parse(expectedParameterSchema));
        var act = JsonSerializer.Serialize(KernelJsonSchema.Parse(functionDefinition.Parameters));

        Assert.NotNull(functionDefinition);
        Assert.Equal("Tests_TestFunction", functionDefinition.Name);
        Assert.Equal("My test function", functionDefinition.Description);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse(expectedParameterSchema)), JsonSerializer.Serialize(KernelJsonSchema.Parse(functionDefinition.Parameters)));
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionsWithParameterTypesAndNoReturnParameterType()
    {
        string expectedParameterSchema = "{   \"type\": \"object\",   \"required\": [\"param1\", \"param2\"],   \"properties\": {     \"param1\": { \"type\": \"string\", \"description\": \"String param 1\" },     \"param2\": { \"type\": \"integer\", \"description\": \"Int param 2\" }   } } ";

        KernelPlugin plugin = KernelPluginFactory.CreateFromFunctions("Tests", new[]
        {
            KernelFunctionFactory.CreateFromMethod(
                [return: Description("My test Result")] ([Description("String param 1")] string param1, [Description("Int param 2")] int param2) => { },
                "TestFunction",
                "My test function")
        });

        OpenAIFunction sut = plugin.GetFunctionsMetadata()[0].ToOpenAIFunction();

        FunctionDefinition functionDefinition = sut.ToFunctionDefinition();

        Assert.NotNull(functionDefinition);
        Assert.Equal("Tests_TestFunction", functionDefinition.Name);
        Assert.Equal("My test function", functionDefinition.Description);
        Assert.Equal(JsonSerializer.Serialize(KernelJsonSchema.Parse(expectedParameterSchema)), JsonSerializer.Serialize(KernelJsonSchema.Parse(functionDefinition.Parameters)));
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionsWithNoParameterTypes()
    {
        // Arrange
        OpenAIFunction f = KernelFunctionFactory.CreateFromMethod(
            () => { },
            parameters: new[] { new KernelParameterMetadata("param1") }).Metadata.ToOpenAIFunction();

        // Act
        FunctionDefinition result = f.ToFunctionDefinition();
        ParametersData pd = JsonSerializer.Deserialize<ParametersData>(result.Parameters.ToString())!;

        // Assert
        Assert.NotNull(pd.properties);
        Assert.Single(pd.properties);
        Assert.Equal(
            JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"string\" }")),
            JsonSerializer.Serialize(pd.properties.First().Value.RootElement));
    }

    [Fact]
    public void ItCanConvertToFunctionDefinitionsWithNoParameterTypesButWithDescriptions()
    {
        // Arrange
        OpenAIFunction f = KernelFunctionFactory.CreateFromMethod(
            () => { },
            parameters: new[] { new KernelParameterMetadata("param1") { Description = "something neat" } }).Metadata.ToOpenAIFunction();

        // Act
        FunctionDefinition result = f.ToFunctionDefinition();
        ParametersData pd = JsonSerializer.Deserialize<ParametersData>(result.Parameters.ToString())!;

        // Assert
        Assert.NotNull(pd.properties);
        Assert.Single(pd.properties);
        Assert.Equal(
            JsonSerializer.Serialize(KernelJsonSchema.Parse("{ \"type\":\"string\", \"description\":\"something neat\" }")),
            JsonSerializer.Serialize(pd.properties.First().Value.RootElement));
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
