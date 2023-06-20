// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Security;
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
        Assert.True(target.TryGetValue(anyName, out TrustAwareString? _));
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
        Assert.True(target.TryGetValue(anyName, out TrustAwareString? _));
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
        Assert.True(target.TryGetValue(anyName, out TrustAwareString? _));
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
        Assert.True(target.TryGetValue(anyName, out TrustAwareString? _));
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
        Assert.True(target.TryGetValue(anyName, out TrustAwareString? _));
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
        Assert.True(target.TryGetValue(anyName, out TrustAwareString? _));
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
        AssertContextVariable(target, anyName, anyContent, true);

        // Act - Erase entry
        target.Set(anyName, null);

        // Assert - Should have been erased
        Assert.False(target.TryGetValue(anyName, out string? _));
        Assert.False(target.TryGetValue(anyName, out TrustAwareString? _));
    }

    [Fact]
    public void GetWithTrustAwareStringSucceeds()
    {
        // Arrange
        string mainContent = Guid.NewGuid().ToString();
        string anyName = Guid.NewGuid().ToString();
        string anyContent = Guid.NewGuid().ToString();
        ContextVariables target = new(mainContent);

        // Act
        target.Set(anyName, TrustAwareString.CreateUntrusted(anyContent));

        // Assert
        Assert.True(target.TryGetValue(anyName, out TrustAwareString? trustAwareValue));
        Assert.NotNull(trustAwareValue);
        Assert.Equal(anyContent, trustAwareValue.Value);
        Assert.False(trustAwareValue.IsTrusted);
        Assert.Equal(mainContent, target.Input.Value);
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
        target.Set(anyName, TrustAwareString.CreateUntrusted(anyContent));

        // Assert
        Assert.True(target.TryGetValue(anyName, out string? value));
        Assert.Equal(anyContent, value);
        Assert.Equal(mainContent, target.Input.Value);
    }

    [Fact]
    public void CreateWithInputDefaultIsTrustedSucceeds()
    {
        // Arrange
        string anyContent = Guid.NewGuid().ToString();
        ContextVariables target = new(anyContent);

        // Assert
        Assert.Equal(anyContent, target.Input);
        AssertContextVariable(target, ContextVariables.MainKey, anyContent, true);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void CreateWithInputIsTrustedValueSucceeds(bool isTrusted)
    {
        // Arrange
        string anyContent = Guid.NewGuid().ToString();
        ContextVariables target = new(new TrustAwareString(anyContent, isTrusted));

        // Assert
        Assert.Equal(anyContent, target.Input);
        AssertContextVariable(target, ContextVariables.MainKey, anyContent, isTrusted);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void KeepInputContentAndUpdateIsTrustedSucceeds(bool isTrusted)
    {
        // Arrange
        string anyContent = Guid.NewGuid().ToString();
        ContextVariables target = new(new TrustAwareString(anyContent, !isTrusted));

        // Assert
        Assert.Equal(anyContent, target.Input);
        AssertContextVariable(target, ContextVariables.MainKey, anyContent, !isTrusted);

        // Act
        target.Update(new TrustAwareString(target.Input, isTrusted));

        // Assert
        Assert.Equal(anyContent, target.Input);
        AssertContextVariable(target, ContextVariables.MainKey, anyContent, isTrusted);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void UpdateInputContentAndUpdateIsTrustedSucceeds(bool isTrusted)
    {
        // Arrange
        string anyContent = Guid.NewGuid().ToString();
        string newContent = Guid.NewGuid().ToString();
        ContextVariables target = new(new TrustAwareString(anyContent, !isTrusted));

        // Assert
        Assert.Equal(anyContent, target.Input);
        AssertContextVariable(target, ContextVariables.MainKey, anyContent, !isTrusted);

        // Act
        target.Update(new TrustAwareString(newContent, isTrusted));

        // Assert
        Assert.Equal(newContent, target.Input);
        AssertContextVariable(target, ContextVariables.MainKey, newContent, isTrusted);
    }

    [Fact]
    public void UpdateWithStringDefaultsToTrustedSucceeds()
    {
        // Arrange
        string content0 = Guid.NewGuid().ToString();
        string content1 = Guid.NewGuid().ToString();
        ContextVariables trustedVar = new(TrustAwareString.CreateTrusted(Guid.NewGuid().ToString()));
        ContextVariables untrustedVar = new(TrustAwareString.CreateUntrusted(Guid.NewGuid().ToString()));

        // Act
        trustedVar.Update(content0);
        untrustedVar.Update(content1);

        // Assert
        AssertContextVariable(trustedVar, ContextVariables.MainKey, content0, true);
        AssertContextVariable(untrustedVar, ContextVariables.MainKey, content1, true);
    }

    [Fact]
    public void UpdateWithNullDefaultsToEmptyTrustedSucceeds()
    {
        // Arrange
        ContextVariables untrustedVar = new(TrustAwareString.CreateUntrusted(Guid.NewGuid().ToString()));

        // Act
        untrustedVar.Update(null);

        // Assert
        AssertContextVariable(untrustedVar, ContextVariables.MainKey, string.Empty, true);
    }

    [Fact]
    public void UpdateUntrustedSucceeds()
    {
        // Arrange
        string trustedContent = Guid.NewGuid().ToString();
        string untrustedContent = Guid.NewGuid().ToString();
        ContextVariables trustedVar = new(TrustAwareString.CreateTrusted(Guid.NewGuid().ToString()));
        ContextVariables untrustedVar = new(TrustAwareString.CreateUntrusted(Guid.NewGuid().ToString()));

        // Act
        trustedVar.Update(TrustAwareString.CreateUntrusted(trustedContent));
        untrustedVar.Update(TrustAwareString.CreateUntrusted(untrustedContent));

        // Assert
        AssertContextVariable(trustedVar, ContextVariables.MainKey, trustedContent, false);
        AssertContextVariable(untrustedVar, ContextVariables.MainKey, untrustedContent, false);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void UpdateKeepingTrustStateSucceeds(bool isTrusted)
    {
        // Arrange
        string someContent = Guid.NewGuid().ToString();
        string someNewContent = Guid.NewGuid().ToString();
        ContextVariables variables = new(new TrustAwareString(someContent, isTrusted));

        // Assert
        AssertContextVariable(variables, ContextVariables.MainKey, someContent, isTrusted);

        // Act
        variables.UpdateKeepingTrustState(someNewContent);

        // Assert
        AssertContextVariable(variables, ContextVariables.MainKey, someNewContent, isTrusted);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void SetWithTrustSucceeds(bool isTrusted)
    {
        // Arrange
        string anyName = Guid.NewGuid().ToString();
        string anyContent = Guid.NewGuid().ToString();
        ContextVariables target = new();

        // Act
        target.Set(anyName, new TrustAwareString(anyContent, isTrusted));

        // Assert
        AssertContextVariable(target, anyName, anyContent, isTrusted);
    }

    [Fact]
    public void GetNameThatDoesNotExistReturnsFalse()
    {
        // Arrange
        string anyName = Guid.NewGuid().ToString();
        ContextVariables target = new();

        // Act
        var exists = target.TryGetValue(anyName, out TrustAwareString? trustAwareValue);

        // Assert
        Assert.False(exists);
        Assert.Null(trustAwareValue);

        // Act
        exists = target.TryGetValue(anyName, out string? value);

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
        ContextVariables original = new(TrustAwareString.CreateUntrusted(mainContent));

        original.Set(anyName, TrustAwareString.CreateUntrusted(anyContent));

        // Act
        // Clone original into target
        target.Update(original);
        // Update original
        original.Update(TrustAwareString.CreateTrusted(someOtherMainContent));
        original.Set(anyName, TrustAwareString.CreateTrusted(someOtherContent));

        // Assert
        // Target should be the same as the original before the update
        AssertContextVariable(target, ContextVariables.MainKey, mainContent, false);
        AssertContextVariable(target, anyName, anyContent, false);
        // Original should have been updated
        AssertContextVariable(original, ContextVariables.MainKey, someOtherMainContent, true);
        AssertContextVariable(original, anyName, someOtherContent, true);
    }

    [Fact]
    public void CallIsAllTrustedSucceeds()
    {
        // Arrange
        string mainContent = Guid.NewGuid().ToString();
        string anyName = Guid.NewGuid().ToString();
        string anyContent = Guid.NewGuid().ToString();
        ContextVariables target = new(TrustAwareString.CreateTrusted(mainContent));

        // Act
        target.Set(anyName, TrustAwareString.CreateTrusted(anyContent));

        // Assert
        Assert.True(target.IsAllTrusted());

        // Act
        target.Set(anyName, TrustAwareString.CreateUntrusted(anyContent));

        // Assert
        Assert.False(target.IsAllTrusted());
    }

    [Fact]
    public void CallUntrustAllSucceeds()
    {
        // Arrange
        string mainContent = Guid.NewGuid().ToString();
        string anyName0 = Guid.NewGuid().ToString();
        string anyContent0 = Guid.NewGuid().ToString();
        string anyName1 = Guid.NewGuid().ToString();
        string anyContent1 = Guid.NewGuid().ToString();
        ContextVariables target = new(TrustAwareString.CreateTrusted(mainContent));

        // Act - Default set with string should be trusted
        target.Set(anyName0, anyContent0);
        target.Set(anyName1, anyContent1);

        // Assert
        // Assert everything is trusted
        Assert.True(target.IsAllTrusted());
        AssertContextVariable(target, ContextVariables.MainKey, mainContent, true);
        AssertContextVariable(target, anyName0, anyContent0, true);
        AssertContextVariable(target, anyName1, anyContent1, true);

        // Act
        target.UntrustAll();

        // Assert
        // Assert everything is now untrusted
        Assert.False(target.IsAllTrusted());
        AssertContextVariable(target, ContextVariables.MainKey, mainContent, false);
        AssertContextVariable(target, anyName0, anyContent0, false);
        AssertContextVariable(target, anyName1, anyContent1, false);
    }

    [Fact]
    public void CallUntrustInputSucceeds()
    {
        // Arrange
        string mainContent = Guid.NewGuid().ToString();
        string anyName0 = Guid.NewGuid().ToString();
        string anyContent0 = Guid.NewGuid().ToString();
        string anyName1 = Guid.NewGuid().ToString();
        string anyContent1 = Guid.NewGuid().ToString();
        ContextVariables target = new(TrustAwareString.CreateTrusted(mainContent));

        // Act - Default set with string should be trusted
        target.Set(anyName0, anyContent0);
        target.Set(anyName1, anyContent1);

        // Assert
        // Assert everything is trusted
        Assert.True(target.IsAllTrusted());
        Assert.True(target.Input.IsTrusted);
        AssertContextVariable(target, ContextVariables.MainKey, mainContent, true);
        AssertContextVariable(target, anyName0, anyContent0, true);
        AssertContextVariable(target, anyName1, anyContent1, true);

        // Act
        target.UntrustInput();

        // Assert
        // Assert the input is untrusted but everything else was kept trusted
        Assert.False(target.IsAllTrusted());
        Assert.False(target.Input.IsTrusted);
        AssertContextVariable(target, ContextVariables.MainKey, mainContent, false);
        AssertContextVariable(target, anyName0, anyContent0, true);
        AssertContextVariable(target, anyName1, anyContent1, true);
    }

    private static void AssertContextVariable(ContextVariables variables, string name, string expectedValue, bool expectedIsTrusted)
    {
        var exists = variables.TryGetValue(name, out TrustAwareString? trustAwareValue);

        // Assert the variable exists
        Assert.True(exists);
        // Assert the value matches
        Assert.NotNull(trustAwareValue);
        Assert.Equal(expectedValue, trustAwareValue.Value);
        // Assert isTrusted matches
        Assert.Equal(expectedIsTrusted, trustAwareValue.IsTrusted);
    }
}
