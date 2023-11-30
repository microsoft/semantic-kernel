// Copyright (c) Microsoft. All rights reserved.

using System;
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
    public void TryGetMetadataValueReturnsTrueWhenKeyExists()
    {
        // Arrange
        string key = Guid.NewGuid().ToString();
        string value = Guid.NewGuid().ToString();
        FunctionResult target = new("functionName");

        // Act
        target.Metadata.Add(key, value);

        // Assert
        Assert.True(target.TryGetMetadataValue(key, out string result));
        Assert.Equal(value, result);
    }

    [Fact]
    public void TryGetMetadataValueReturnsFalseWhenKeyDoesNotExist()
    {
        // Arrange
        string key = Guid.NewGuid().ToString();
        FunctionResult target = new("functionName");

        // Act,Assert
        Assert.False(target.TryGetMetadataValue(key, out string result));
        Assert.Null(result);
    }

    [Fact]
    public void TryGetMetadataValueReturnsFalseWhenKeyExistsButTypeDoesNotMatch()
    {
        // Arrange
        string key = Guid.NewGuid().ToString();
        int value = 42;
        FunctionResult target = new("functionName");

        // Act
        target.Metadata.Add(key, value);

        // Assert
        Assert.False(target.TryGetMetadataValue(key, out string result));
        Assert.Null(result);
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
