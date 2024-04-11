// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Planning.Handlebars;
using Xunit;

namespace Microsoft.SemanticKernel.Planners.UnitTests.Handlebars;

public class KernelParameterMetadataExtensionsTests
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
            Assert.True(KernelParameterMetadataExtensions.IsPrimitiveOrStringType(type));
        }

        Assert.True(KernelParameterMetadataExtensions.IsPrimitiveOrStringType(stringType));
    }

    [Fact]
    public void ReturnsFalseForNonPrimitiveOrStringTypes()
    {
        // Arrange
        var nonPrimitiveTypes = new Type[] { typeof(object), typeof(DateTime), typeof(List<int>), typeof(HandlebarsParameterTypeMetadata) };

        // Act and Assert
        foreach (var type in nonPrimitiveTypes)
        {
            Assert.False(KernelParameterMetadataExtensions.IsPrimitiveOrStringType(type));
        }
    }

    [Fact]
    public void ReturnsEmptySetForPrimitiveOrStringType()
    {
        // Arrange
        var primitiveType = typeof(int);

        // Act
        var result = primitiveType.ToHandlebarsParameterTypeMetadata();

        // Assert
        Assert.Empty(result);
    }

    [Fact]
    public void ReturnsSetWithOneElementForSimpleClassType()
    {
        // Arrange
        var simpleClassType = typeof(SimpleClass);

        // Act
        var result = simpleClassType.ToHandlebarsParameterTypeMetadata();

        // Assert
        Assert.Single(result);
        Assert.Equal("SimpleClass", result.First().Name);
        Assert.True(result.First().IsComplex);
        Assert.Equal(2, result.First().Properties.Count);
        Assert.Equal("Id", result.First().Properties[0].Name);
        Assert.Equal(typeof(int), result.First().Properties[0].ParameterType);
        Assert.Equal("Name", result.First().Properties[1].Name);
        Assert.Equal(typeof(string), result.First().Properties[1].ParameterType);
    }

    [Fact]
    public void ReturnsSetWithOneElementForRecursiveClassType()
    {
        // Arrange
        var recursiveClassType = typeof(RecursiveClass);

        // Act
        var result = recursiveClassType.ToHandlebarsParameterTypeMetadata();

        // Assert
        Assert.Single(result);
        Assert.Equal(nameof(RecursiveClass), result.First().Name);
        Assert.True(result.First().IsComplex);
        Assert.Equal(2, result.First().Properties.Count);
        Assert.Equal(nameof(RecursiveClass.Name), result.First().Properties[0].Name);
        Assert.Equal(typeof(string), result.First().Properties[0].ParameterType);
        Assert.Equal(nameof(RecursiveClass.Next), result.First().Properties[1].Name);
        Assert.Equal(typeof(RecursiveClass), result.First().Properties[1].ParameterType);
    }

    [Fact]
    public void ReturnsSetWithMultipleElementsForNestedClassType()
    {
        // Arrange
        var nestedClassType = typeof(NestedClass);

        // Act
        var result = nestedClassType.ToHandlebarsParameterTypeMetadata();

        // Assert
        Assert.Equal(3, result.Count);
        Assert.Contains(result, r => r.Name == "NestedClass");
        Assert.Contains(result, r => r.Name == "SimpleClass");
        Assert.Contains(result, r => r.Name == "AnotherClass");

        var nestedClass = result.First(r => r.Name == "NestedClass");
        Assert.True(nestedClass.IsComplex);
        Assert.Equal(3, nestedClass.Properties.Count);
        Assert.Equal("Id", nestedClass.Properties[0].Name);
        Assert.Equal(typeof(int), nestedClass.Properties[0].ParameterType);
        Assert.Equal("Simple", nestedClass.Properties[1].Name);
        Assert.Equal(typeof(SimpleClass), nestedClass.Properties[1].ParameterType);
        Assert.Equal("Another", nestedClass.Properties[2].Name);
        Assert.Equal(typeof(AnotherClass), nestedClass.Properties[2].ParameterType);

        var simpleClass = result.First(r => r.Name == "SimpleClass");
        Assert.True(simpleClass.IsComplex);
        Assert.Equal(2, simpleClass.Properties.Count);
        Assert.Equal("Id", simpleClass.Properties[0].Name);
        Assert.Equal(typeof(int), simpleClass.Properties[0].ParameterType);
        Assert.Equal("Name", simpleClass.Properties[1].Name);
        Assert.Equal(typeof(string), simpleClass.Properties[1].ParameterType);

        var anotherClass = result.First(r => r.Name == "AnotherClass");
        Assert.True(anotherClass.IsComplex);
        Assert.Single(anotherClass.Properties);
        Assert.Equal("Value", anotherClass.Properties[0].Name);
        Assert.Equal(typeof(double), anotherClass.Properties[0].ParameterType);

        // Should not contain primitive types
        Assert.DoesNotContain(result, r => r.Name == "Id");
        Assert.DoesNotContain(result, r => !r.IsComplex);

        // Should not contain empty complex types
        Assert.DoesNotContain(result, r => r.IsComplex && r.Properties.Count == 0);
    }

    [Fact]
    public void ReturnsSetWithOneElementForTaskOfSimpleClassType()
    {
        // Arrange
        var taskOfSimpleClassType = typeof(Task<SimpleClass>);

        // Act
        var result = taskOfSimpleClassType.ToHandlebarsParameterTypeMetadata();

        // Assert
        Assert.Single(result);
        Assert.Equal("SimpleClass", result.First().Name);
        Assert.True(result.First().IsComplex);
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
        var result1 = taskOfPrimitiveType.ToHandlebarsParameterTypeMetadata();
        var result2 = taskOfStringType.ToHandlebarsParameterTypeMetadata();

        // Assert
        Assert.Empty(result1);
        Assert.Empty(result2);
    }

    [Fact]
    public void ReturnsTrueForPrimitiveOrStringSchemaTypes()
    {
        // Arrange
        var primitiveSchemaTypes = new string[] { "string", "number", "integer", "boolean" };

        // Act and Assert
        foreach (var type in primitiveSchemaTypes)
        {
            Assert.True(KernelParameterMetadataExtensions.IsPrimitiveOrStringType(type));
        }
    }

    [Fact]
    public void ReturnsFalseForNonPrimitiveOrStringSchemaTypes()
    {
        // Arrange
        var nonPrimitiveSchemaTypes = new string[] { "object", "array", "any", "null" };

        // Act and Assert
        foreach (var type in nonPrimitiveSchemaTypes)
        {
            Assert.False(KernelParameterMetadataExtensions.IsPrimitiveOrStringType(type));
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
            var schema = KernelJsonSchema.Parse($$"""{"type": "{{pair.Key}}"}""");
            var parameter = new KernelParameterMetadata("test") { Schema = schema };

            // Act
            var result = parameter.ParseJsonSchema();

            // Assert
            Assert.Equal(pair.Value, result.ParameterType);
        }
    }

    [Fact]
    public void ReturnsParameterWithSchemaForNonPrimitiveOrStringSchemaType()
    {
        // Arrange
        var schema = KernelJsonSchema.Parse("""{"type": "object", "properties": {"name": {"type": "string"}}}""");
        var parameter = new KernelParameterMetadata("test") { Schema = schema };

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
        var jsonProperties = KernelJsonSchema.Parse("""{"name": "Alice", "age": 25}""").RootElement;

        // Act
        var result = jsonProperties.ToJsonString();

        // Ensure that the line endings are consistent across different dotnet versions
        result = result.Replace("\r\n", "\n", StringComparison.InvariantCulture);

        // Assert
        var expected = "{\n  \"name\": \"Alice\",\n  \"age\": 25\n}";
        Assert.Equal(expected, result);
    }

    [Fact]
    public void ReturnsParameterNameAndSchemaType()
    {
        // Arrange
        var schema = KernelJsonSchema.Parse("""{"type": "object", "properties": {"name": {"type": "string"}}}""");
        var parameter = new KernelParameterMetadata("test") { Schema = schema };

        // Act
        var result = parameter.GetSchemaTypeName();

        // Assert
        Assert.Equal("test-object", result);
    }

    [Fact]
    public void ConvertsReturnParameterMetadataToParameterMetadata()
    {
        // Arrange
        var schema = KernelJsonSchema.Parse("""{"type": "object", "properties": {"name": {"type": "string"}}}""");
        var returnParameter = new KernelReturnParameterMetadata() { Description = "test", ParameterType = typeof(object), Schema = schema };

        // Act
        var functionName = "Foo";
        var result = returnParameter.ToKernelParameterMetadata(functionName);

        // Assert
        Assert.Equal("FooReturns", result.Name);
        Assert.Equal("test", result.Description);
        Assert.Equal(typeof(object), result.ParameterType);
        Assert.Equal(schema, result.Schema);
    }

    [Fact]
    public void ConvertsParameterMetadataToReturnParameterMetadata()
    {
        // Arrange
        var schema = KernelJsonSchema.Parse("""{"type": "object", "properties": {"name": {"type": "string"}}}""");
        var parameter = new KernelParameterMetadata("test") { Description = "test", ParameterType = typeof(object), Schema = schema };

        // Act
        var result = parameter.ToKernelReturnParameterMetadata();

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

    private static class NestedClass
    {
        public static int Id { get; set; }
        public static SimpleClass Simple { get; set; } = new SimpleClass();
        public static AnotherClass Another { get; set; } = new AnotherClass();
    }

    private sealed class RecursiveClass
    {
        public string Name { get; set; } = "";

        public RecursiveClass Next { get; set; } = new();
    }

    #endregion  
}
