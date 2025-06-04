// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Utilities.Model;

public class FreezableTests
{
    [Fact]
    public void ItShouldBeUnfrozenByDefault()
    {
        // Arrange
        Freezable sut = new();

        // Act & Assert
        Assert.False(sut.IsFrozen);
    }

    [Fact]
    public void ItShouldFreezeAndBeFrozen()
    {
        // Arrange
        Freezable sut = new();

        // Act
        sut.Freeze();

        // Assert
        Assert.True(sut.IsFrozen);
    }

    [Fact]
    public void ItShouldThrowIfFrozen()
    {
        // Arrange
        Freezable sut = new();
        sut.Freeze();

        // Act & Assert
        Assert.Throws<InvalidOperationException>(sut.ThrowIfFrozen);
    }

    [Fact]
    public void ItShouldNotThrowIfNotFrozen()
    {
        // Arrange
        Freezable sut = new();

        // Act & Assert
        sut.ThrowIfFrozen();
    }
}
