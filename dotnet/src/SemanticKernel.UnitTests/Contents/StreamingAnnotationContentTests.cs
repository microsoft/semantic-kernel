// Copyright (c) Microsoft. All rights reserved.
using System.Text;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.UnitTests.Contents;

#pragma warning disable SKEXP0110

/// <summary>
/// Unit testing of <see cref="StreamingAnnotationContent"/>.
/// </summary>
public class StreamingAnnotationContentTests
{
    /// <summary>
    /// Verify default state.
    /// </summary>
    [Fact]
    public void VerifyStreamingAnnotationContentInitialState()
    {
        StreamingAnnotationContent definition = new();

        Assert.Empty(definition.Label);
        Assert.Null(definition.StartIndex);
        Assert.Null(definition.EndIndex);
        Assert.Null(definition.ReferenceId);
    }

    /// <summary>
    /// Verify usage.
    /// </summary>
    [Fact]
    public void VerifyStreamingAnnotationContentWithFileId()
    {
        StreamingAnnotationContent definition =
            new("test quote", "#id", AnnotationKind.FileCitation)
            {
                StartIndex = 33,
                EndIndex = 49,
            };

        Assert.Equal("test quote", definition.Label);
        Assert.Equal(33, definition.StartIndex);
        Assert.Equal(49, definition.EndIndex);
        Assert.Equal("#id", definition.ReferenceId);
        Assert.Equal("test quote: #id", definition.ToString());
        Assert.Equal("test quote: #id", Encoding.UTF8.GetString(definition.ToByteArray()));
    }
}
