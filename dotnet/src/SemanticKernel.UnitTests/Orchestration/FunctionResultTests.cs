// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Orchestration;

/// <summary>
/// Unit tests of <see cref="FunctionResult"/>.
/// </summary>
public class FunctionResultTests
{
    private readonly Mock<IFunctionRunner> _functionRunner = new();
    private readonly Mock<IAIServiceProvider> _serviceProvider = new();
    private readonly Mock<IAIServiceSelector> _serviceSelector = new();

    private SKContext CreateContext()
    {
        return new SKContext(this._functionRunner.Object, this._serviceProvider.Object, this._serviceSelector.Object);
    }

    [Fact]
    public void TryGetMetadataValueReturnsTrueWhenKeyExists()
    {
        // Arrange
        string key = Guid.NewGuid().ToString();
        string value = Guid.NewGuid().ToString();
        FunctionResult target = new("functionName", "pluginName", this.CreateContext());

        // Act
        target.Metadata.Add(key, value);

        // Assert
        Assert.True(target.TryGetMetadataValue<string>(key, out string result));
        Assert.Equal(value, result);
    }

    [Fact]
    public void TryGetMetadataValueReturnsFalseWhenKeyDoesNotExist()
    {
        // Arrange
        string key = Guid.NewGuid().ToString();
        FunctionResult target = new("functionName", "pluginName", this.CreateContext());

        // Act,Assert
        Assert.False(target.TryGetMetadataValue<string>(key, out string result));
        Assert.Null(result);
    }

    [Fact]
    public void TryGetMetadataValueReturnsFalseWhenKeyExistsButTypeDoesNotMatch()
    {
        // Arrange
        string key = Guid.NewGuid().ToString();
        int value = 42;
        FunctionResult target = new("functionName", "pluginName", this.CreateContext());

        // Act
        target.Metadata.Add(key, value);

        // Assert
        Assert.False(target.TryGetMetadataValue<string>(key, out string result));
        Assert.Null(result);
    }

    [Fact]
    public void GetValueReturnsValueWhenValueIsNotNull()
    {
        // Arrange
        string value = Guid.NewGuid().ToString();
        FunctionResult target = new("functionName", "pluginName", this.CreateContext(), value);

        // Act,Assert
        Assert.Equal(value, target.GetValue<string>());
    }

    [Fact]
    public void GetValueReturnsNullWhenValueIsNull()
    {
        // Arrange
        FunctionResult target = new("functionName", "pluginName", this.CreateContext(), null);

        // Act,Assert
        Assert.Null(target.GetValue<string>());
    }

    [Fact]
    public void GetValueThrowsWhenValueIsNotNullButTypeDoesNotMatch()
    {
        // Arrange
        int value = 42;
        FunctionResult target = new("functionName", "pluginName", this.CreateContext(), value);

        // Act,Assert
        Assert.Throws<InvalidCastException>(() => target.GetValue<string>());
    }

    [Fact]
    public void ConstructorSetsProperties()
    {
        // Arrange
        string functionName = Guid.NewGuid().ToString();
        string pluginName = Guid.NewGuid().ToString();
        SKContext context = this.CreateContext();

        // Act
        FunctionResult target = new(functionName, pluginName, context);

        // Assert
        Assert.Equal(functionName, target.FunctionName);
        Assert.Equal(pluginName, target.PluginName);
        Assert.Equal(context, target.Context);
    }

    [Fact]
    public void ConstructorSetsPropertiesAndValue()
    {
        // Arrange
        string functionName = Guid.NewGuid().ToString();
        string pluginName = Guid.NewGuid().ToString();
        SKContext context = this.CreateContext();
        string value = Guid.NewGuid().ToString();

        // Act
        FunctionResult target = new(functionName, pluginName, context, value);

        // Assert
        Assert.Equal(functionName, target.FunctionName);
        Assert.Equal(pluginName, target.PluginName);
        Assert.Equal(context, target.Context);
        Assert.Equal(value, target.Value);
    }

    [Fact]
    public void ToStringWorksCorrectly()
    {
        // Arrange
        string value = Guid.NewGuid().ToString();
        FunctionResult target = new("functionName", "pluginName", this.CreateContext(), value);

        // Act and Assert
        Assert.Equal(value, target.ToString());
    }
}
