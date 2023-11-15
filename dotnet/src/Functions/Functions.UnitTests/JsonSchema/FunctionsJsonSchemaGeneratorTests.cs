// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.JsonSchema;
using Microsoft.SemanticKernel.Prompt;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.JsonSchema;

public sealed class FunctionsJsonSchemaGeneratorTests
{
    [Fact]
    public void ItShouldGenerateSchemaForType()
    {
        // Arrange
        var jsonSchemaGenerator = new FunctionsJsonSchemaGenerator();

        // Act
        var schema = jsonSchemaGenerator.GenerateSchema(typeof(PromptNode), "description");

        // Assert
        Assert.NotNull(schema);
        Assert.Equal("object", schema.RootElement.GetProperty("type").GetString());
    }

    [Fact]
    public void ItShouldGenerateSchemaForFunction()
    {
        // Arrange
        var schemaGenerator = new FunctionsJsonSchemaGenerator();
        static string Test(string parameter)
        {
            return parameter;
        }

        // Act
        var function = SKFunction.Create(Method(Test), functionName: "Test", schemaGenerator: schemaGenerator);

        // Assert
        Assert.NotNull(function);
        var functionView = function.Describe();
        Assert.Single(functionView.Parameters);
        Assert.Equal(typeof(string), functionView.Parameters[0].ParameterType);
        Assert.Equal("{\"type\":\"string\",\"description\":\"\"}", functionView.Parameters[0].Schema?.RootElement.ToString());
    }

    private static MethodInfo Method(Delegate method)
    {
        return method.Method;
    }
}
