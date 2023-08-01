// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Plugins.Memory;
using Xunit;

namespace SemanticKernel.Plugins.Memory.UnitTests;

public class MemoryExceptionTests
{
    [Fact]
    public void ItRoundtripsArgsToErrorCodeCtor()
    {
        // Arrange
        var e = new MemoryException(MemoryException.ErrorCodes.FailedToCreateCollection);

        // Assert
        Assert.Equal(MemoryException.ErrorCodes.FailedToCreateCollection, e.ErrorCode);
        Assert.Contains("Failed to create collection", e.Message, StringComparison.Ordinal);
        Assert.Null(e.InnerException);
    }

    [Fact]
    public void ItRoundtripsArgsToErrorCodeMessageCtor()
    {
        // Arrange
        const string Message = "this is a test";
        var e = new MemoryException(MemoryException.ErrorCodes.FailedToCreateCollection, Message);

        // Assert
        Assert.Equal(MemoryException.ErrorCodes.FailedToCreateCollection, e.ErrorCode);
        Assert.Contains("Failed to create collection", e.Message, StringComparison.Ordinal);
        Assert.Contains(Message, e.Message, StringComparison.Ordinal);
        Assert.Null(e.InnerException);
    }

    [Fact]
    public void ItRoundtripsArgsToErrorCodeMessageExceptionCtor()
    {
        // Arrange
        const string Message = "this is a test";
        var inner = new FormatException();
        var e = new MemoryException(MemoryException.ErrorCodes.FailedToCreateCollection, Message, inner);

        // Assert
        Assert.Equal(MemoryException.ErrorCodes.FailedToCreateCollection, e.ErrorCode);
        Assert.Contains("Failed to create collection", e.Message, StringComparison.Ordinal);
        Assert.Contains(Message, e.Message, StringComparison.Ordinal);
        Assert.Same(inner, e.InnerException);
    }

    [Fact]
    public void ItAllowsNullMessageAndInnerExceptionInCtors()
    {
        // Arrange
        var e = new MemoryException(MemoryException.ErrorCodes.FailedToCreateCollection, null, null);

        // Assert
        Assert.Equal(MemoryException.ErrorCodes.FailedToCreateCollection, e.ErrorCode);
        Assert.Contains("Failed to create collection", e.Message, StringComparison.Ordinal);
        Assert.Null(e.InnerException);
    }
}
