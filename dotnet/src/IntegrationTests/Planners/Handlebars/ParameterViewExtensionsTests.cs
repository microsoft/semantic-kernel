// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planners.Handlebars.Extensions;
using Microsoft.SemanticKernel.Planners.Handlebars.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Planners.Handlebars;

public class ParameterViewExtensionsTests
{
    [Fact]
    public void ReturnsTrueForPrimitiveOrStringTypes()
    {
        // Arrange
        var primitiveTypes = new Type[] { typeof(int), typeof(double), typeof(bool), typeof(char) };
        var stringType = typeof(string);

        // Act and Assert
        foreach (var type in primitiveTypes)
        {
            Assert.True(ParameterViewExtensions.isPrimitiveOrStringType(type));
        }

        Assert.True(ParameterViewExtensions.isPrimitiveOrStringType(stringType));
    }

    [Fact]
    public void ReturnsFalseForNonPrimitiveOrStringTypes()
    {
        // Arrange
        var nonPrimitiveTypes = new Type[] { typeof(object), typeof(DateTime), typeof(List<int>), typeof(HandlebarsParameterTypeView) };

        // Act and Assert
        foreach (var type in nonPrimitiveTypes)
        {
            Assert.False(ParameterViewExtensions.isPrimitiveOrStringType(type));
        }
    }

    [Fact]
    public void ReturnsEmptySetForPrimitiveOrStringType()
    {
        // Arrange
        var primitiveType = typeof(int);

        // Act
        var result = primitiveType.ToHandlebarsParameterTypeView();

        // Assert
        Assert.Empty(result);
    }

    [Fact]
    public void ReturnsSetWithOneElementForSimpleClassType()
    {
        // Arrange
        var simpleClassType = typeof(SimpleClass);

        // Act
        var result = simpleClassType.ToHandlebarsParameterTypeView();

        // Assert
        Assert.Single(result);
        Assert.Equal("SimpleClass", result.First().Name);
        Assert.True(result.First().IsComplexType);
        Assert.Equal(2, result.First().Properties.Count);
        Assert.Equal("Id", result.First().Properties[0].Name);
        Assert.Equal(typeof(int), result.First().Properties[0].ParameterType);
        Assert.Equal("Name", result.First().Properties[1].Name);
        Assert.Equal(typeof(string), result.First().Properties[1].ParameterType);
    }

    [Fact]
    public void ReturnsSetWithMultipleElementsForNestedClassType()
    {
        // Arrange
        var nestedClassType = typeof(NestedClass);

        // Act
        var result = nestedClassType.ToHandlebarsParameterTypeView();

        // Assert
        Assert.Equal(3, result.Count);
        Assert.Contains(result, r => r.Name == "NestedClass");
        Assert.Contains(result, r => r.Name == "SimpleClass");
        Assert.Contains(result, r => r.Name == "AnotherClass");

        var nestedClass = result.First(r => r.Name == "NestedClass");
        Assert.True(nestedClass.IsComplexType);
        Assert.Equal(3, nestedClass.Properties.Count);
        Assert.Equal("Id", nestedClass.Properties[0].Name);
        Assert.Equal(typeof(int), nestedClass.Properties[0].ParameterType);
        Assert.Equal("Simple", nestedClass.Properties[1].Name);
        Assert.Equal(typeof(SimpleClass), nestedClass.Properties[1].ParameterType);
        Assert.Equal("Another", nestedClass.Properties[2].Name);
        Assert.Equal(typeof(AnotherClass), nestedClass.Properties[2].ParameterType);

        var simpleClass = result.First(r => r.Name == "SimpleClass");
        Assert.True(simpleClass.IsComplexType);
        Assert.Equal(2, simpleClass.Properties.Count);
        Assert.Equal("Id", simpleClass.Properties[0].Name);
        Assert.Equal(typeof(int), simpleClass.Properties[0].ParameterType);
        Assert.Equal("Name", simpleClass.Properties[1].Name);
        Assert.Equal(typeof(string), simpleClass.Properties[1].ParameterType);

        var anotherClass = result.First(r => r.Name == "AnotherClass");
        Assert.True(anotherClass.IsComplexType);
        Assert.Single(anotherClass.Properties);
        Assert.Equal("Value", anotherClass.Properties[0].Name);
        Assert.Equal(typeof(double), anotherClass.Properties[0].ParameterType);

        // Should not contain primitive types
        Assert.DoesNotContain(result, r => r.Name == "Id");
        Assert.DoesNotContain(result, r => !r.IsComplexType);

        // Should not contain empty complex types
        Assert.DoesNotContain(result, r => r.IsComplexType && r.Properties.Count == 0);
    }

    [Fact]
    public void ReturnsSetWithOneElementForTaskOfSimpleClassType()
    {
        // Arrange
        var taskOfSimpleClassType = typeof(Task<SimpleClass>);

        // Act
        var result = taskOfSimpleClassType.ToHandlebarsParameterTypeView();

        // Assert
        Assert.Single(result);
        Assert.Equal("SimpleClass", result.First().Name);
        Assert.True(result.First().IsComplexType);
        Assert.Equal(2, result.First().Properties.Count);
        Assert.Equal("Id", result.First().Properties[0].Name);
        Assert.Equal(typeof(int), result.First().Properties[0].ParameterType);
        Assert.Equal("Name", result.First().Properties[1].Name);
        Assert.Equal(typeof(string), result.First().Properties[1].ParameterType);
    }

    [Fact]
    public void ReturnsEmptySetForTaskOfPrimitiveOrStringType()
    {
        // Arrange
        var taskOfPrimitiveType = typeof(Task<int>);
        var taskOfStringType = typeof(Task<string>);

        // Act
        var result1 = taskOfPrimitiveType.ToHandlebarsParameterTypeView();
        var result2 = taskOfStringType.ToHandlebarsParameterTypeView();

        // Assert
        Assert.Empty(result1);
        Assert.Empty(result2);
    }

    [Fact]
    public void ReturnsTrueForPrimitiveOrStringSchemaTypes()
    {
        // Arrange
        var primitiveSchemaTypes = new string[] { "string", "number", "integer", "boolean", "null" };

        // Act and Assert
        foreach (var type in primitiveSchemaTypes)
        {
            Assert.True(ParameterViewExtensions.isPrimitiveOrStringType(type));
        }
    }

    [Fact]
    public void ReturnsFalseForNonPrimitiveOrStringSchemaTypes()
    {
        // Arrange
        var nonPrimitiveSchemaTypes = new string[] { "object", "array", "any" };

        // Act and Assert
        foreach (var type in nonPrimitiveSchemaTypes)
        {
            Assert.False(ParameterViewExtensions.isPrimitiveOrStringType(type));
        }
    }

    [Fact]
    public void ReturnsParameterWithParameterTypeForPrimitiveOrStringSchemaType()
    {
        // Arrange
        var schemaTypeMap = new Dictionary<string, Type>
        {
            {"string", typeof(string)},
            {"integer", typeof(long)},
            {"number", typeof(double)},
            {"boolean", typeof(bool)},
            {"null", typeof(object)}
        };

        foreach (var pair in schemaTypeMap)
        {
            var schema = JsonDocument.Parse($"{{\"type\": \"{pair.Key}\"}}");
            var parameter = new ParameterView("test", "test", Schema: schema);

            // Act
            var result = parameter.ParseJsonSchema();

            // Assert
            Assert.Equal(pair.Value, result.ParameterType);
            Assert.Null(result.Schema);
        }
    }

    [Fact]
    public void ReturnsParameterWithSchemaForNonPrimitiveOrStringSchemaType()
    {
        // Arrange
        var schema = JsonDocument.Parse("{\"type\": \"object\", \"properties\": {\"name\": {\"type\": \"string\"}}}");
        var parameter = new ParameterView("test", "test", Schema: schema);

        // Act
        var result = parameter.ParseJsonSchema();

        // Assert
        Assert.Null(result.ParameterType);
        Assert.Equal(schema, result.Schema);
    }

    [Fact]
    public void ReturnsIndentedJsonStringForJsonElement()
    {
        // Arrange
        var jsonProperties = JsonDocument.Parse("{\"name\": \"Alice\", \"age\": 25}").RootElement;

        // Act
        var result = jsonProperties.ToJsonString();

        // Assert
        var expected = @"{
  ""name"": ""Alice"",
  ""age"": 25
}";
        Assert.Equal(expected, result);
    }

    [Fact]
    public void ReturnsParameterNameAndSchemaType()
    {
        // Arrange
        var schema = JsonDocument.Parse("{\"type\": \"object\", \"properties\": {\"name\": {\"type\": \"string\"}}}");
        var parameter = new ParameterView("test", "test", Schema: schema);

        // Act
        var result = parameter.GetSchemaTypeName();

        // Assert
        Assert.Equal("test-object", result);
    }

    [Fact]
    public void ReturnsParameterViewWithFunctionNameAndReturnParameterViewProperties()
    {
        // Arrange
        var schema = JsonDocument.Parse("{\"type\": \"object\", \"properties\": {\"name\": {\"type\": \"string\"}}}");
        var returnParameter = new ReturnParameterView("test", ParameterType: typeof(object), Schema: schema);
        var functionName = "Foo";

        // Act
        var result = returnParameter.ToParameterView(functionName);

        // Assert
        Assert.Equal("FooReturns", result.Name);
        Assert.Equal("test", result.Description);
        Assert.Equal(typeof(object), result.ParameterType);
        Assert.Equal(schema, result.Schema);
    }

    [Fact]
    public void ReturnsReturnParameterViewWithParameterViewProperties()
    {
        // Arrange
        var schema = JsonDocument.Parse("{\"type\": \"object\", \"properties\": {\"name\": {\"type\": \"string\"}}}");
        var parameter = new ParameterView("test", "test", ParameterType: typeof(object), Schema: schema);

        // Act
        var result = parameter.ToReturnParameterView();

        // Assert
        Assert.Equal("test", result.Description);
        Assert.Equal(typeof(object), result.ParameterType);
        Assert.Equal(schema, result.Schema);
    }

    #region Simple helper classes

    private sealed class SimpleClass
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
    }

    private sealed class AnotherClass
    {
        public double Value { get; set; }
    }

    private sealed class NestedClass
    {
        public int Id { get; set; }
        public SimpleClass? Simple { get; set; }
        public AnotherClass? Another { get; set; }
    }

    #endregion  
}
