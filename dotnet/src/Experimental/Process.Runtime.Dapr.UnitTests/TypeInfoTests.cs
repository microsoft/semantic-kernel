// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process.Serialization;
using Xunit;

namespace SemanticKernel.Process.Dapr.Runtime.UnitTests;

/// <summary>
/// Unit tests for the <see cref="TypeInfo"/> class.
/// </summary>
public class TypeInfoTests
{
    /// <summary>
    /// Tests that ConvertValue deserializes a JsonElement to the correct type.
    /// </summary>
    [Fact]
    public void ConvertValueDeserializesJsonElement()
    {
        // Arrange
        var json = JsonSerializer.SerializeToElement(42);
        var typeName = typeof(int).AssemblyQualifiedName;

        // Act
        var result = TypeInfo.ConvertValue(typeName, json);

        // Assert
        Assert.Equal(42, result);
    }

    /// <summary>
    /// Tests that ConvertValue throws when the type name cannot be resolved.
    /// </summary>
    [Fact]
    public void ConvertValueThrowsForUnresolvableType()
    {
        // Arrange
        var json = JsonSerializer.SerializeToElement(42);

        // Act & Assert
        Assert.Throws<KernelException>(() =>
            TypeInfo.ConvertValue("NonExistent.Type, NonExistent.Assembly", json));
    }

    /// <summary>
    /// Tests that ConvertValue returns non-JsonElement values unchanged.
    /// </summary>
    [Fact]
    public void ConvertValueReturnsNonJsonElementUnchanged()
    {
        // Arrange
        var value = "plain string";

        // Act
        var result = TypeInfo.ConvertValue(typeof(string).AssemblyQualifiedName, value);

        // Assert
        Assert.Equal("plain string", result);
    }

    /// <summary>
    /// Tests that ConvertValue returns null when value is null.
    /// </summary>
    [Fact]
    public void ConvertValueReturnsNullWhenValueIsNull()
    {
        // Act
        var result = TypeInfo.ConvertValue(typeof(string).AssemblyQualifiedName, null);

        // Assert
        Assert.Null(result);
    }
}
