// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Utilities;
public class FullyQualifiedFunctionNameTests
{
    [Fact]
    public void ItShouldParseFullyQualifiedNameThatHasPluginNameAndFunctionName()
    {
        // Arrange & act
        var sut = FullyQualifiedFunctionName.Parse("p1.f1", ".");

        // Assert
        Assert.Equal("f1", sut.FunctionName);
        Assert.Equal("p1", sut.PluginName);
    }

    [Fact]
    public void ItShouldParseFullyQualifiedNameThatHasFunctionNameOnly()
    {
        // Arrange & act
        var sut = FullyQualifiedFunctionName.Parse("f1");

        // Assert
        Assert.Equal("f1", sut.FunctionName);
        Assert.Null(sut.PluginName);
    }
}
