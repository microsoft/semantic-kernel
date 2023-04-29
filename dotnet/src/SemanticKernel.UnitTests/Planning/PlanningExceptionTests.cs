// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Planning;
using Xunit;

namespace SemanticKernel.UnitTests.Planning;

public class PlanningExceptionTests
{
    [Fact]
    public void ItRoundtripsArgsToErrorCodeCtor()
    {
        // Arrange
        var e = new PlanningException(PlanningException.ErrorCodes.InvalidGoal);

        // Assert
        Assert.Equal(PlanningException.ErrorCodes.InvalidGoal, e.ErrorCode);
        Assert.Contains("Invalid goal", e.Message, StringComparison.Ordinal);
        Assert.Null(e.InnerException);
    }

    [Fact]
    public void ItRoundtripsArgsToErrorCodeMessageCtor()
    {
        // Arrange
        const string message = "this is a test";
        var e = new PlanningException(PlanningException.ErrorCodes.InvalidGoal, message);

        // Assert
        Assert.Equal(PlanningException.ErrorCodes.InvalidGoal, e.ErrorCode);
        Assert.Contains("Invalid goal", e.Message, StringComparison.Ordinal);
        Assert.Contains(message, e.Message, StringComparison.Ordinal);
        Assert.Null(e.InnerException);
    }

    [Fact]
    public void ItRoundtripsArgsToErrorCodeMessageExceptionCtor()
    {
        // Arrange
        const string message = "this is a test";
        var inner = new FormatException();
        var e = new PlanningException(PlanningException.ErrorCodes.InvalidGoal, message, inner);

        // Assert
        Assert.Equal(PlanningException.ErrorCodes.InvalidGoal, e.ErrorCode);
        Assert.Contains("Invalid goal", e.Message, StringComparison.Ordinal);
        Assert.Contains(message, e.Message, StringComparison.Ordinal);
        Assert.Same(inner, e.InnerException);
    }

    [Fact]
    public void ItAllowsNullMessageAndInnerExceptionInCtors()
    {
        // Arrange
        var e = new PlanningException(PlanningException.ErrorCodes.InvalidGoal, null, null);

        // Assert
        Assert.Equal(PlanningException.ErrorCodes.InvalidGoal, e.ErrorCode);
        Assert.Contains("Invalid goal", e.Message, StringComparison.Ordinal);
        Assert.Null(e.InnerException);
    }
}
