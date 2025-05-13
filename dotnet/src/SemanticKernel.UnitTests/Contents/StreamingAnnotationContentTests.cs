// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Text;
using System.Threading.Tasks;
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
        Assert.Throws<ArgumentException>(() => new StreamingAnnotationContent(AnnotationKind.FileCitation, string.Empty, "test"));
        Assert.Throws<ArgumentException>(() => new StreamingAnnotationContent(AnnotationKind.FileCitation, "test", string.Empty));
    }

    /// <summary>
    /// Verify usage.
    /// </summary>
    [Fact]
    public void VerifyStreamingAnnotationContentWithFileId()
    {
        StreamingAnnotationContent definition =
            new(AnnotationKind.FileCitation, "test label", "#id")
            {
                StartIndex = 33,
                EndIndex = 49,
            };

        Assert.Equal(AnnotationKind.FileCitation, definition.Kind);
        Assert.Equal("test label", definition.Label);
        Assert.Equal(33, definition.StartIndex);
        Assert.Equal(49, definition.EndIndex);
        Assert.Equal("#id", definition.ReferenceId);
        Assert.Equal("test label: #id", definition.ToString());
        Assert.Equal("test label: #id", Encoding.UTF8.GetString(definition.ToByteArray()));
    }
}
