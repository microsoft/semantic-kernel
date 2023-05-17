// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Orchestration;
using Xunit;

namespace SemanticKernel.UnitTests.Orchestration;

/// <summary>
/// Unit tests of <see cref="ContextVariables"/>.
/// </summary>
public class ContextVariablesTests
{
    [Fact]
    public void EnumerationOfContextVariableVariablesSucceeds()
    {
        // Arrange
        string firstName = Guid.NewGuid().ToString();
        string firstValue = Guid.NewGuid().ToString();
        string secondName = Guid.NewGuid().ToString();
        string secondValue = Guid.NewGuid().ToString();

        // Act            
        ContextVariables target = new();
        target.Set(firstName, firstValue);
        target.Set(secondName, secondValue);

        // Assert
        var items = target.ToArray();

        Assert.Single(items.Where(i => i.Key == firstName && i.Value == firstValue));
        Assert.Single(items.Where(i => i.Key == secondName && i.Value == secondValue));
    }

    [Fact]
    public void IndexGetAfterIndexSetSucceeds()
    {
        // Arrange
        string anyName = Guid.NewGuid().ToString();
        string anyValue = Guid.NewGuid().ToString();
        ContextVariables target = new();

        // Act
        target[anyName] = anyValue;

        // Assert
        Assert.Equal(anyValue, target[anyName]);
    }

    [Fact]
    public void IndexGetWithoutSetThrowsKeyNotFoundException()
    {
        // Arrange
        string anyName = Guid.NewGuid().ToString();
        ContextVariables target = new();

        // Act,Assert
        Assert.Throws<KeyNotFoundException>(() => target[anyName]);
    }

    [Fact]
    public void IndexSetAfterIndexSetSucceeds()
    {
        // Arrange
        string anyName = Guid.NewGuid().ToString();
        string anyValue = Guid.NewGuid().ToString();
        ContextVariables target = new();

        // Act
        target[anyName] = anyValue;
        target[anyName] = anyValue;

        // Assert
        Assert.Equal(anyValue, target[anyName]);
    }

    [Fact]
    public void IndexSetWithoutGetSucceeds()
    {
        // Arrange
        string anyName = Guid.NewGuid().ToString();
        string anyValue = Guid.NewGuid().ToString();
        ContextVariables target = new();

        // Act
        target[anyName] = anyValue;

        // Assert
        Assert.Equal(anyValue, target[anyName]);
    }

    [Fact]
    public void SetAfterIndexSetSucceeds()
    {
        // Arrange
        string anyName = Guid.NewGuid().ToString();
        string anyContent = Guid.NewGuid().ToString();
        ContextVariables target = new();

        // Act
        target[anyName] = anyContent;
        target.Set(anyName, anyContent);

        // Assert
        Assert.True(target.Get(anyName, out string _));
    }

    [Fact]
    public void SetAfterSetSucceeds()
    {
        // Arrange
        string anyName = Guid.NewGuid().ToString();
        string anyContent = Guid.NewGuid().ToString();
        ContextVariables target = new();

        // Act
        target.Set(anyName, anyContent);
        target.Set(anyName, anyContent);

        // Assert
        Assert.True(target.Get(anyName, out string _));
    }

    [Fact]
    public void SetBeforeIndexSetSucceeds()
    {
        // Arrange
        string anyName = Guid.NewGuid().ToString();
        string anyContent = Guid.NewGuid().ToString();
        ContextVariables target = new();

        // Act
        target.Set(anyName, anyContent);
        target[anyName] = anyContent;

        // Assert
        Assert.True(target.Get(anyName, out string _));
    }

    [Fact]
    public void SetBeforeSetSucceeds()
    {
        // Arrange
        string anyName = Guid.NewGuid().ToString();
        string anyContent = Guid.NewGuid().ToString();
        ContextVariables target = new();

        // Act
        target.Set(anyName, anyContent);
        target.Set(anyName, anyContent);

        // Assert
        Assert.True(target.Get(anyName, out string _));
    }

    [Fact]
    public void SetWithoutGetSucceeds()
    {
        // Arrange
        string anyName = Guid.NewGuid().ToString();
        string anyContent = Guid.NewGuid().ToString();
        ContextVariables target = new();

        // Act
        target.Set(anyName, anyContent);

        // Assert
        Assert.True(target.Get(anyName, out string _));
    }

    [Fact]
    public void SetWithoutLabelSucceeds()
    {
        // Arrange
        string anyName = Guid.NewGuid().ToString();
        string anyContent = Guid.NewGuid().ToString();
        ContextVariables target = new();

        // Act
        target.Set(anyName, anyContent);

        // Assert
        Assert.True(target.Get(anyName, out string _));
    }
}
