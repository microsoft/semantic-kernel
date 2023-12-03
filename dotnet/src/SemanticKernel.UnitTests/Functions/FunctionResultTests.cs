// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

/// <summary>
/// Unit tests of <see cref="FunctionResult"/>.
/// </summary>
public class FunctionResultTests
{
    [Fact]
    public void DefaultsAreExpected()
    {
        var result = new FunctionResult("test");
        Assert.Null(result.GetValue<object>());
        Assert.Same(CultureInfo.InvariantCulture, result.Culture);
        Assert.Null(result.Metadata);
    }

    [Fact]
    public void PropertiesRoundtrip()
    {
        object resultValue = new();
        CultureInfo culture = new("fr-FR");
        IDictionary<string, object?> metadata = new Dictionary<string, object?>();

        FunctionResult result = new("test", resultValue, culture);
        Assert.Same(resultValue, result.GetValue<object>());
        Assert.Same(culture, result.Culture);
        Assert.Null(result.Metadata);

        result = new("test", resultValue, culture, metadata);
        Assert.Same(resultValue, result.GetValue<object>());
        Assert.Same(culture, result.Culture);
        Assert.Same(metadata, result.Metadata);
    }

    [Fact]
    public void GetValueReturnsValueWhenValueIsNotNull()
    {
        // Arrange
        string value = Guid.NewGuid().ToString();
        FunctionResult target = new("functionName", value, CultureInfo.InvariantCulture);

        // Act,Assert
        Assert.Equal(value, target.GetValue<string>());
    }

    [Fact]
    public void GetValueReturnsNullWhenValueIsNull()
    {
        // Arrange
        FunctionResult target = new("functionName");

        // Act,Assert
        Assert.Null(target.GetValue<string>());
    }

    [Fact]
    public void GetValueThrowsWhenValueIsNotNullButTypeDoesNotMatch()
    {
        // Arrange
        int value = 42;
        FunctionResult target = new("functionName", value, CultureInfo.InvariantCulture);

        // Act,Assert
        Assert.Throws<InvalidCastException>(() => target.GetValue<string>());
    }

    [Fact]
    public void ConstructorSetsProperties()
    {
        // Arrange
        string functionName = Guid.NewGuid().ToString();
        string pluginName = Guid.NewGuid().ToString();

        // Act
        FunctionResult target = new(functionName);

        // Assert
        Assert.Equal(functionName, target.FunctionName);
    }

    [Fact]
    public void ConstructorSetsPropertiesAndValue()
    {
        // Arrange
        string functionName = Guid.NewGuid().ToString();
        string value = Guid.NewGuid().ToString();

        // Act
        FunctionResult target = new(functionName, value, CultureInfo.InvariantCulture);

        // Assert
        Assert.Equal(functionName, target.FunctionName);
        Assert.Equal(value, target.Value);
    }

    [Fact]
    public void ToStringWorksCorrectly()
    {
        // Arrange
        string value = Guid.NewGuid().ToString();
        FunctionResult target = new("functionName", value, CultureInfo.InvariantCulture);

        // Act and Assert
        Assert.Equal(value, target.ToString());
    }
}
