// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Security;
using Xunit;

namespace SemanticKernel.UnitTests.Security;

/// <summary>
/// Unit tests of <see cref="TrustAwareString"/>.
/// </summary>
public sealed class TrustAwareStringTest
{
    [Fact]
    public void CreateNewWithDefaultTrustedSucceeds()
    {
        // Arrange
        string anyValue = Guid.NewGuid().ToString();

        // Act
        TrustAwareString value = new(anyValue);

        // Assert
        Assert.Equal(anyValue, value.ToString());
        Assert.Equal(anyValue, value.Value);
        Assert.True(value.IsTrusted);
    }

    [Fact]
    public void CreateEmptySucceeds()
    {
        // Act
        TrustAwareString value = TrustAwareString.Empty;

        // Assert
        Assert.Empty(value.ToString());
        Assert.Empty(value.Value);
        Assert.True(value.IsTrusted);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void CreateNewWithIsTrustedValueSucceeds(bool isTrusted)
    {
        // Arrange
        string anyValue = Guid.NewGuid().ToString();

        // Act
        TrustAwareString value = new(anyValue, isTrusted);

        // Assert
        Assert.Equal(anyValue, value.ToString());
        Assert.Equal(anyValue, value.Value);
        Assert.Equal(isTrusted, value.IsTrusted);
    }

    [Fact]
    public void EqualsAndGetHashCodeSucceeds()
    {
        // Arrange
        var trustedValue0 = TrustAwareString.CreateTrusted("some value 0");
        var trustedValue0Copy = TrustAwareString.CreateTrusted("some value 0");
        var untrustedValue0 = TrustAwareString.CreateUntrusted("some value 0");
        var untrustedValue0Copy = TrustAwareString.CreateUntrusted("some value 0");
        var trustedValue1 = TrustAwareString.CreateTrusted("some value 1");
        var untrustedValue1 = TrustAwareString.CreateTrusted("some value 1");
        var stringValue0 = "some value 0";
        int someObj = 10;

        // Act and assert
        Assert.True(trustedValue0.Equals(trustedValue0Copy));
        Assert.True(untrustedValue0.Equals(untrustedValue0Copy));
        Assert.True(trustedValue0 == trustedValue0Copy);
        Assert.True(untrustedValue0 == untrustedValue0Copy);

        Assert.False(trustedValue0.Equals(untrustedValue0));
        Assert.False(trustedValue0.Equals(trustedValue1));
        Assert.False(untrustedValue0.Equals(untrustedValue1));
        Assert.True(trustedValue0 != untrustedValue0);
        Assert.True(trustedValue0 != trustedValue1);
        Assert.True(untrustedValue0 != untrustedValue1);

        // Uses override with object
        // Comparison with string should work
        Assert.True(trustedValue0.Equals(stringValue0));
        // Comparison with int should not work
        Assert.False(trustedValue0.Equals(someObj));

        // Uses the implicit conversion
        Assert.True(trustedValue0 == stringValue0);
        Assert.True(stringValue0 == trustedValue0);

        Assert.Equal(trustedValue0.GetHashCode(), trustedValue0Copy.GetHashCode());
        Assert.NotEqual(trustedValue0.GetHashCode(), untrustedValue0.GetHashCode());
        Assert.NotEqual(trustedValue0.GetHashCode(), trustedValue1.GetHashCode());
    }

    [Fact]
    public void EqualsWithNullsSucceeds()
    {
        // Arrange
        TrustAwareString? null1 = null;
        TrustAwareString? null2 = null;
        TrustAwareString value = new("value");

        // Act and assert
#pragma warning disable CA1508 // Avoid dead conditional code
        Assert.True(null1 == null2);
        Assert.False(null1 != null2);
        Assert.False(value.Equals(null1));
        Assert.False(value == null1);
        Assert.True(value != null1);

        Assert.True(null1 == null);
        Assert.False(null1 != null);
        Assert.False(value.Equals(null));
        Assert.False(value == null);
        Assert.True(value != null);
#pragma warning restore CA1508 // Avoid dead conditional code
    }
}
