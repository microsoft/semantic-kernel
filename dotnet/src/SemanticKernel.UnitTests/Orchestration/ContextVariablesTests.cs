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
        Assert.True(target.TryGetValue(anyName, out string? _));
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
        Assert.True(target.TryGetValue(anyName, out string? _));
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
        Assert.True(target.TryGetValue(anyName, out string? _));
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
        Assert.True(target.TryGetValue(anyName, out string? _));
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
        Assert.True(target.TryGetValue(anyName, out string? _));
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
        Assert.True(target.TryGetValue(anyName, out string? _));
    }

    [Fact]
    public void SetWithNullValueErasesSucceeds()
    {
        // Arrange
        string anyName = Guid.NewGuid().ToString();
        string anyContent = Guid.NewGuid().ToString();
        ContextVariables target = new();

        // Act
        target.Set(anyName, anyContent);

        // Assert
        AssertContextVariable(target, anyName, anyContent);

        // Act - Erase entry
        target.Set(anyName, null);

        // Assert - Should have been erased
        Assert.False(target.TryGetValue(anyName, out string? _));
    }

    [Fact]
    public void GetWithStringSucceeds()
    {
        // Arrange
        string mainContent = Guid.NewGuid().ToString();
        string anyName = Guid.NewGuid().ToString();
        string anyContent = Guid.NewGuid().ToString();
        ContextVariables target = new(mainContent);

        // Act
        target.Set(anyName, anyContent);

        // Assert
        Assert.True(target.TryGetValue(anyName, out string? value));
        Assert.Equal(anyContent, value);
        Assert.Equal(mainContent, target.Input);
    }

    [Fact]
    public void GetNameThatDoesNotExistReturnsFalse()
    {
        // Arrange
        string anyName = Guid.NewGuid().ToString();
        ContextVariables target = new();

        // Act
        var exists = target.TryGetValue(anyName, out string? value);

        // Assert
        Assert.False(exists);
        Assert.Null(value);
    }

    [Fact]
    public void UpdateOriginalDoesNotAffectClonedSucceeds()
    {
        // Arrange
        string mainContent = Guid.NewGuid().ToString();
        string anyName = Guid.NewGuid().ToString();
        string anyContent = Guid.NewGuid().ToString();
        string someOtherMainContent = Guid.NewGuid().ToString();
        string someOtherContent = Guid.NewGuid().ToString();
        ContextVariables target = new();
        ContextVariables original = new(mainContent);

        original.Set(anyName, anyContent);

        // Act
        // Clone original into target
        target.Update(original);
        // Update original
        original.Update(someOtherMainContent);
        original.Set(anyName, someOtherContent);

        // Assert
        // Target should be the same as the original before the update
        AssertContextVariable(target, ContextVariables.MainKey, mainContent);
        AssertContextVariable(target, anyName, anyContent);
        // Original should have been updated
        AssertContextVariable(original, ContextVariables.MainKey, someOtherMainContent);
        AssertContextVariable(original, anyName, someOtherContent);
    }

    private static void AssertContextVariable(ContextVariables variables, string name, string expectedValue)
    {
        var exists = variables.TryGetValue(name, out string? value);

        // Assert the variable exists
        Assert.True(exists);
        // Assert the value matches
        Assert.NotNull(value);
        Assert.Equal(expectedValue, value);
    }
}
