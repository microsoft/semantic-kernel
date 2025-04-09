// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Utilities;

public class FunctionNameTests
{
    [Fact]
    public void ItShouldParseFullyQualifiedNameThatHasPluginNameAndFunctionName()
    {
        // Arrange & act
        var sut = FunctionName.Parse("p1.f1", ".");

        // Assert
        Assert.Equal("f1", sut.Name);
        Assert.Equal("p1", sut.PluginName);
    }

    [Fact]
    public void ItShouldParseFullyQualifiedNameThatHasFunctionNameOnly()
    {
        // Arrange & act
        var sut = FunctionName.Parse("f1");

        // Assert
        Assert.Equal("f1", sut.Name);
        Assert.Null(sut.PluginName);
    }

    [Fact]
    public void ItShouldCreateFullyQualifiedNameFromPluginAndFunctionNames()
    {
        // Act
        var fullyQualifiedName = FunctionName.ToFullyQualifiedName("f1", "p1", ".");

        // Assert
        Assert.Equal("p1.f1", fullyQualifiedName);
    }

    [Fact]
    public void ItShouldCreateFullyQualifiedNameFromFunctionName()
    {
        // Act
        var fullyQualifiedName = FunctionName.ToFullyQualifiedName("f1");

        // Assert
        Assert.Equal("f1", fullyQualifiedName);
    }
}
