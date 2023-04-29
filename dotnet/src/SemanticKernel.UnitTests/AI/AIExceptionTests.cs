// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.AI;
using Xunit;

namespace SemanticKernel.UnitTests.AI;

public class AIExceptionTests
{
    [Fact]
    public void ItRoundtripsArgsToErrorCodeCtor()
    {
        // Arrange
        var e = new AIException(AIException.ErrorCodes.InvalidRequest);

        // Assert
        Assert.Equal(AIException.ErrorCodes.InvalidRequest, e.ErrorCode);
        Assert.Contains("Invalid request", e.Message, StringComparison.Ordinal);
        Assert.Null(e.Detail);
        Assert.Null(e.InnerException);
    }

    [Fact]
    public void ItRoundtripsArgsToErrorCodeMessageCtor()
    {
        // Arrange
        const string message = "this is a test";
        var e = new AIException(AIException.ErrorCodes.InvalidRequest, message);

        // Assert
        Assert.Equal(AIException.ErrorCodes.InvalidRequest, e.ErrorCode);
        Assert.Contains("Invalid request", e.Message, StringComparison.Ordinal);
        Assert.Contains(message, e.Message, StringComparison.Ordinal);
        Assert.Null(e.Detail);
        Assert.Null(e.InnerException);
    }

    [Fact]
    public void ItRoundtripsArgsToErrorCodeMessageExceptionCtor()
    {
        // Arrange
        const string message = "this is a test";
        var inner = new FormatException();
        var e = new AIException(AIException.ErrorCodes.InvalidRequest, message, inner);

        // Assert
        Assert.Equal(AIException.ErrorCodes.InvalidRequest, e.ErrorCode);
        Assert.Contains("Invalid request", e.Message, StringComparison.Ordinal);
        Assert.Contains(message, e.Message, StringComparison.Ordinal);
        Assert.Null(e.Detail);
        Assert.Same(inner, e.InnerException);
    }

    [Fact]
    public void ItRoundtripsArgsToErrorCodeMessageDetailCtor()
    {
        // Arrange
        const string message = "this is a test";
        const string detail = "so is this";
        var e = new AIException(AIException.ErrorCodes.InvalidRequest, message, detail);

        // Assert
        Assert.Equal(AIException.ErrorCodes.InvalidRequest, e.ErrorCode);
        Assert.Contains("Invalid request", e.Message, StringComparison.Ordinal);
        Assert.Contains(message, e.Message, StringComparison.Ordinal);
        Assert.Equal(detail, e.Detail);
        Assert.Null(e.InnerException);
    }

    [Fact]
    public void ItRoundtripsArgsToErrorCodeMessageDetailExceptionCtor()
    {
        // Arrange
        const string message = "this is a test";
        const string detail = "so is this";
        var inner = new FormatException();
        var e = new AIException(AIException.ErrorCodes.InvalidRequest, message, detail, inner);

        // Assert
        Assert.Equal(AIException.ErrorCodes.InvalidRequest, e.ErrorCode);
        Assert.Contains("Invalid request", e.Message, StringComparison.Ordinal);
        Assert.Contains(message, e.Message, StringComparison.Ordinal);
        Assert.Equal(detail, e.Detail);
        Assert.Same(inner, e.InnerException);
    }

    [Fact]
    public void ItAllowsNullMessageAndInnerExceptionInCtors()
    {
        // Arrange
        var e = new AIException(AIException.ErrorCodes.AccessDenied, null, null, null);

        // Assert
        Assert.Equal(AIException.ErrorCodes.AccessDenied, e.ErrorCode);
        Assert.Contains("Access denied", e.Message, StringComparison.Ordinal);
        Assert.Null(e.Detail);
        Assert.Null(e.InnerException);
    }
}
