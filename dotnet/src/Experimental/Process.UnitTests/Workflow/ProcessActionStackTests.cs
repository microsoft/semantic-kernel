// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Process.Workflows;
using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows;

public sealed class ProcessActionStackTests
{
    [Fact]
    public void EmptyStackFailure()
    {
        // Arrange
        ProcessActionStack stack = new();

        // Act & Assert
        InvalidOperationException exception = Assert.Throws<InvalidOperationException>(() => stack.CurrentScope);
        Assert.Equal("No scope defined", exception.Message);
    }

    [Fact]
    public void RootScope()
    {
        // Arrange
        ProcessActionStack stack = new();

        // Act
        stack.Recognize("missing");
        string actualScope = stack.CurrentScope;

        // Assert
        Assert.Equal("missing", actualScope);
    }

    [Fact]
    public void NewScope()
    {
        // Arrange
        ProcessActionStack stack = new();

        // Act
        stack.Recognize("rootscope");
        stack.Recognize("childscope");

        // Assert
        Assert.Equal("childscope", stack.CurrentScope);
    }

    [Fact]
    public void SameConsecutiveScope()
    {
        // Arrange
        ProcessActionStack stack = new();

        // Act
        stack.Recognize("rootscope");
        stack.Recognize("childscope");
        stack.Recognize("childscope");

        // Assert
        Assert.Equal("childscope", stack.CurrentScope);
    }

    [Fact]
    public void CompletedScope()
    {
        // Arrange
        ProcessActionStack stack = new();

        // Act
        stack.Recognize("rootscope");
        stack.Recognize("childscope");
        stack.Recognize("deepscope");
        stack.Recognize("childscope");

        // Assert
        Assert.Equal("childscope", stack.CurrentScope);
    }

    [Fact]
    public void DeepScope()
    {
        // Arrange
        ProcessActionStack stack = new();

        // Act
        stack.Recognize("rootscope");
        stack.Recognize("childscope");
        stack.Recognize("deepscope");
        stack.Recognize("rootscope");

        // Assert
        Assert.Equal("rootscope", stack.CurrentScope);
    }

    [Fact]
    public void ScopeCallback()
    {
        // Arrange
        ProcessActionStack stack = new();
        HashSet<string> completedScopes = [];

        // Act
        stack.Recognize("rootscope", HandleCompletion);
        stack.Recognize("childscope", HandleCompletion);
        stack.Recognize("deepscope", HandleCompletion);
        stack.Recognize("rootscope", HandleCompletion);

        // Assert
        Assert.Equal("rootscope", stack.CurrentScope);
        Assert.Contains("deepscope", completedScopes);
        Assert.Contains("childscope", completedScopes);
        Assert.DoesNotContain("rootscope", completedScopes);

        void HandleCompletion(string scopeId)
        {
            completedScopes.Add(scopeId);
        }
    }
}
