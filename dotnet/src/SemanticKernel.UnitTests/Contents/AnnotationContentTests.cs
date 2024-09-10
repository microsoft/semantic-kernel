// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.UnitTests.Contents;

#pragma warning disable SKEXP0110

/// <summary>
/// Unit testing of <see cref="AnnotationContent"/>.
/// </summary>
public class AnnotationContentTests
{
    /// <summary>
    /// Verify default state.
    /// </summary>
    [Fact]
    public void VerifyAnnotationContentInitialState()
    {
        AnnotationContent definition = new();

        Assert.Empty(definition.Quote);
        Assert.Equal(0, definition.StartIndex);
        Assert.Equal(0, definition.EndIndex);
        Assert.Null(definition.FileId);
    }
    /// <summary>
    /// Verify usage.
    /// </summary>
    [Fact]
    public void VerifyAnnotationContentUsage()
    {
        AnnotationContent definition =
            new()
            {
                Quote = "test quote",
                StartIndex = 33,
                EndIndex = 49,
                FileId = "#id",
            };

        Assert.Equal("test quote", definition.Quote);
        Assert.Equal(33, definition.StartIndex);
        Assert.Equal(49, definition.EndIndex);
        Assert.Equal("#id", definition.FileId);
    }
}
