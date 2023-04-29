// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.TemplateEngine;
using Xunit;

namespace SemanticKernel.UnitTests.TemplateEngine;

public class TemplateExceptionTests
{
    [Fact]
    public void ItRoundtripsArgsToErrorCodeCtor()
    {
        // Arrange
        var e = new TemplateException(TemplateException.ErrorCodes.RuntimeError);

        // Assert
        Assert.Equal(TemplateException.ErrorCodes.RuntimeError, e.ErrorCode);
        Assert.Contains("Runtime error", e.Message, StringComparison.Ordinal);
        Assert.Null(e.InnerException);
    }

    [Fact]
    public void ItRoundtripsArgsToErrorCodeMessageCtor()
    {
        // Arrange
        const string message = "this is a test";
        var e = new TemplateException(TemplateException.ErrorCodes.RuntimeError, message);

        // Assert
        Assert.Equal(TemplateException.ErrorCodes.RuntimeError, e.ErrorCode);
        Assert.Contains("Runtime error", e.Message, StringComparison.Ordinal);
        Assert.Contains(message, e.Message, StringComparison.Ordinal);
        Assert.Null(e.InnerException);
    }

    [Fact]
    public void ItRoundtripsArgsToErrorCodeMessageExceptionCtor()
    {
        // Arrange
        const string message = "this is a test";
        var inner = new FormatException();
        var e = new TemplateException(TemplateException.ErrorCodes.RuntimeError, message, inner);

        // Assert
        Assert.Equal(TemplateException.ErrorCodes.RuntimeError, e.ErrorCode);
        Assert.Contains("Runtime error", e.Message, StringComparison.Ordinal);
        Assert.Contains(message, e.Message, StringComparison.Ordinal);
        Assert.Same(inner, e.InnerException);
    }

    [Fact]
    public void ItAllowsNullMessageAndInnerExceptionInCtors()
    {
        // Arrange
        var e = new TemplateException(TemplateException.ErrorCodes.RuntimeError, null, null);

        // Assert
        Assert.Equal(TemplateException.ErrorCodes.RuntimeError, e.ErrorCode);
        Assert.Contains("Runtime error", e.Message, StringComparison.Ordinal);
        Assert.Null(e.InnerException);
    }
}
