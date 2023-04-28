// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;
using Xunit;

namespace SemanticKernel.UnitTests.Diagnostics;

public class ValidationExceptionTests
{
    [Fact]
    public void ItRoundtripsArgsToErrorCodeCtor()
    {
        // Arrange
        var e = new ValidationException(ValidationException.ErrorCodes.DirectoryNotFound);

        // Assert
        Assert.Equal(ValidationException.ErrorCodes.DirectoryNotFound, e.ErrorCode);
        Assert.Contains("Directory not found", e.Message, StringComparison.Ordinal);
        Assert.Null(e.InnerException);
    }

    [Fact]
    public void ItRoundtripsArgsToErrorCodeMessageCtor()
    {
        // Arrange
        const string Message = "this is a test";
        var e = new ValidationException(ValidationException.ErrorCodes.DirectoryNotFound, Message);

        // Assert
        Assert.Equal(ValidationException.ErrorCodes.DirectoryNotFound, e.ErrorCode);
        Assert.Contains("Directory not found", e.Message, StringComparison.Ordinal);
        Assert.Contains(Message, e.Message, StringComparison.Ordinal);
        Assert.Null(e.InnerException);
    }

    [Fact]
    public void ItRoundtripsArgsToErrorCodeMessageExceptionCtor()
    {
        // Arrange
        const string Message = "this is a test";
        var inner = new FormatException();
        var e = new ValidationException(ValidationException.ErrorCodes.DirectoryNotFound, Message, inner);

        // Assert
        Assert.Equal(ValidationException.ErrorCodes.DirectoryNotFound, e.ErrorCode);
        Assert.Contains("Directory not found", e.Message, StringComparison.Ordinal);
        Assert.Contains(Message, e.Message, StringComparison.Ordinal);
        Assert.Same(inner, e.InnerException);
    }

    [Fact]
    public void ItAllowsNullMessageAndInnerExceptionInCtors()
    {
        // Arrange
        var e = new ValidationException(ValidationException.ErrorCodes.DirectoryNotFound, null, null);

        // Assert
        Assert.Equal(ValidationException.ErrorCodes.DirectoryNotFound, e.ErrorCode);
        Assert.Contains("Directory not found", e.Message, StringComparison.Ordinal);
        Assert.Null(e.InnerException);
    }
}
