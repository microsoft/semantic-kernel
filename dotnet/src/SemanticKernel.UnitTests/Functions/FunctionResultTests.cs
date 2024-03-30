// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

/// <summary>
/// Unit tests of <see cref="FunctionResult"/>.
/// </summary>
public class FunctionResultTests
{
    private static readonly KernelFunction s_nopFunction = KernelFunctionFactory.CreateFromMethod(() => { });

    [Fact]
    public void DefaultsAreExpected()
    {
        var result = new FunctionResult(s_nopFunction);
        Assert.Null(result.GetValue<object>());
        Assert.Same(CultureInfo.InvariantCulture, result.Culture);
        Assert.Null(result.Metadata);
    }

    [Fact]
    public void PropertiesRoundtrip()
    {
        object resultValue = new();
        CultureInfo culture = new("fr-FR");
        var metadata = new Dictionary<string, object?>();

        FunctionResult result = new(s_nopFunction, resultValue, culture);
        Assert.Same(resultValue, result.GetValue<object>());
        Assert.Same(culture, result.Culture);
        Assert.Null(result.Metadata);

        result = new(s_nopFunction, resultValue, culture, metadata);
        Assert.Same(resultValue, result.GetValue<object>());
        Assert.Same(culture, result.Culture);
        Assert.Same(metadata, result.Metadata);
    }

    [Fact]
    public void GetValueReturnsValueWhenValueIsNotNull()
    {
        // Arrange
        string value = Guid.NewGuid().ToString();
        FunctionResult target = new(s_nopFunction, value, CultureInfo.InvariantCulture);

        // Act,Assert
        Assert.Equal(value, target.GetValue<string>());
    }

    [Fact]
    public void GetValueReturnsNullWhenValueIsNull()
    {
        // Arrange
        FunctionResult target = new(s_nopFunction);

        // Act,Assert
        Assert.Null(target.GetValue<string>());
    }

    [Fact]
    public void GetValueThrowsWhenValueIsNotNullButTypeDoesNotMatch()
    {
        // Arrange
        int value = 42;
        FunctionResult target = new(s_nopFunction, value, CultureInfo.InvariantCulture);

        // Act,Assert
        Assert.Throws<InvalidCastException>(() => target.GetValue<string>());
    }

    [Fact]
    public void ConstructorSetsProperties()
    {
        // Act
        FunctionResult target = new(s_nopFunction);

        // Assert
        Assert.Same(s_nopFunction, target.Function);
    }

    [Fact]
    public void ConstructorSetsPropertiesAndValue()
    {
        // Arrange
        string functionName = Guid.NewGuid().ToString();
        string value = Guid.NewGuid().ToString();

        // Act
        FunctionResult target = new(s_nopFunction, value, CultureInfo.InvariantCulture);

        // Assert
        Assert.Same(s_nopFunction, target.Function);
        Assert.Equal(value, target.Value);
    }

    [Fact]
    public void ToStringWorksCorrectly()
    {
        // Arrange
        string value = Guid.NewGuid().ToString();
        FunctionResult target = new(s_nopFunction, value, CultureInfo.InvariantCulture);

        // Act and Assert
        Assert.Equal(value, target.ToString());
    }

    [Fact]
    public void GetValueWhenValueIsKernelContentGenericStringShouldReturnContentBaseToString()
    {
        // Arrange
        string expectedValue = Guid.NewGuid().ToString();
        FunctionResult target = new(s_nopFunction, new TextContent(expectedValue));

        // Act and Assert
        Assert.Equal(expectedValue, target.GetValue<string>());
    }

    [Fact]
    public void GetValueWhenValueIsKernelContentGenericTypeMatchShouldReturn()
    {
        // Arrange
        string expectedValue = Guid.NewGuid().ToString();
        var valueType = new TextContent(expectedValue);
        FunctionResult target = new(s_nopFunction, valueType);

        // Act and Assert

        Assert.Equal(valueType, target.GetValue<TextContent>());
        Assert.Equal(valueType, target.GetValue<KernelContent>());
    }

    [Fact]
    public async Task ItCanBeSerializedAndDeserializedAsync()
    {
        // Arrange
        string value = Guid.NewGuid().ToString();

        FunctionResult target = new(KernelFunctionFactory.CreateFromMethod((int a) => a), value, CultureInfo.InvariantCulture, new Dictionary<string, object?> { { "key", "value" } });

        // Act
        string serialized = JsonSerializer.Serialize(target);

        FunctionResult? deserialized = JsonSerializer.Deserialize<FunctionResult>(serialized);

        // Assert
        Assert.NotNull(deserialized);

        // Function is lost during serialization
        Assert.Null(deserialized!.Function);

        // Value lost original .NET type during serialization
        Assert.Equal(typeof(JsonElement), deserialized.ValueType);
        Assert.Equal(typeof(JsonElement), deserialized.Value!.GetType());

        Assert.Equal(value, deserialized.Value.ToString());
        Assert.Equal(CultureInfo.InvariantCulture, deserialized.Culture);
        Assert.NotNull(deserialized.Metadata);
        Assert.Equal(target.Metadata!.Count, deserialized.Metadata!.Count);

        // A try to invoke the function will fail because the function is lost during serialization
        var kernel = new Kernel();

        try
        {
            var res = await deserialized!.Function!.InvokeAsync(kernel);
        }
        catch (NullReferenceException)
        {
        }
    }
}
