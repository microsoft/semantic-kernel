// Copyright (c) Microsoft. All rights reserved.
using System;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.UnitTests.Contents;

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
        Assert.Throws<ArgumentException>(() => new AnnotationContent(AnnotationKind.FileCitation, string.Empty, "test"));
        Assert.Throws<ArgumentException>(() => new AnnotationContent(AnnotationKind.FileCitation, "test", string.Empty));
    }
    /// <summary>
    /// Verify usage.
    /// </summary>
    [Fact]
    public void VerifyAnnotationContentUsage()
    {
        AnnotationContent definition =
            new(AnnotationKind.TextCitation, "test label", "#id")
            {
                StartIndex = 33,
                EndIndex = 49,
            };

        Assert.Equal(AnnotationKind.TextCitation, definition.Kind);
        Assert.Equal("test label", definition.Label);
        Assert.Equal(33, definition.StartIndex);
        Assert.Equal(49, definition.EndIndex);
        Assert.Equal("#id", definition.ReferenceId);
    }
}
