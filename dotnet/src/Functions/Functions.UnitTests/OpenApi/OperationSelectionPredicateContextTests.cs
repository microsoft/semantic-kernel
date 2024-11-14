// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

public class OperationSelectionPredicateContextTests
{
    [Fact]
    public void ItShouldCheckTwoContextsAreEqual()
    {
        // Arrange
        var context1 = new OperationSelectionPredicateContext("id", "path", "method", "description");
        var context2 = new OperationSelectionPredicateContext("id", "path", "method", "description");

        // Act & Assert
        Assert.True(context1 == context2);
    }

    [Fact]
    public void ItShouldCheckTwoContextsAreNotEqual()
    {
        // Arrange
        var context1 = new OperationSelectionPredicateContext("id", "path", "method", "description");
        var context2 = new OperationSelectionPredicateContext("id1", "path1", "method1", "description1");

        // Act & Assert
        Assert.False(context1 == context2);
    }

    [Fact]
    public void ItShouldCheckContextsIsEqualToItself()
    {
        // Arrange
        var context = new OperationSelectionPredicateContext("id", "path", "method", "description");

        // Act & Assert
#pragma warning disable CS1718 // Comparison made to same variable
        Assert.True(context == context);
#pragma warning restore CS1718 // Comparison made to same variable
    }

    [Fact]
    public void ItShouldCheckContextIsNotEqualToNull()
    {
        // Arrange
        var context = new OperationSelectionPredicateContext("id", "path", "method", "description");

        // Act & Assert
        Assert.False(context.Equals(null));
    }
}
