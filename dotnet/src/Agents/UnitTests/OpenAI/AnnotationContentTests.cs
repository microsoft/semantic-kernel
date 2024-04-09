// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.OpenAI.Assistants;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

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

        Assert.Null(definition.Quote);
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
        TestTextAnnotation annotation = new("testquote", 33, 49);

        AnnotationContent definition = new(annotation);

        Assert.Equal("testquote", definition.Quote);
        Assert.Equal(33, definition.StartIndex);
        Assert.Equal(49, definition.EndIndex);
        Assert.Null(definition.FileId);
    }

    /// <summary>
    /// Need local type for testability.
    /// </summary>
#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class TestTextAnnotation : MessageTextAnnotation
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        public TestTextAnnotation(string text, int startIndex, int endIndex)
            : base(text, startIndex, endIndex)
        { }
    }
}
