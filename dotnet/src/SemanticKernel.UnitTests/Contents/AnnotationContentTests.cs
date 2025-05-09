// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.Agents;
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

        Assert.Empty(definition.Label);
        Assert.Null(definition.StartIndex);
        Assert.Null(definition.EndIndex);
        Assert.Empty(definition.ReferenceId);
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
                Label = "test quote",
                StartIndex = 33,
                EndIndex = 49,
                ReferenceId = "#id",
            };

        Assert.Equal("test quote", definition.Label);
        Assert.Equal(33, definition.StartIndex);
        Assert.Equal(49, definition.EndIndex);
        Assert.Equal("#id", definition.ReferenceId);
    }
}
