// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Contents;

/// <summary>
/// Unit testing of <see cref="ReasoningContent"/>.
/// </summary>
public class ReasoningContentTests
{
    [Fact]
    public void VerifyReasoningContextText()
    {
        ReasoningContent content = new("test");

        Assert.Equal("test", content.Text);
        Assert.Equal("test", $"{content}");
    }

    [Fact]
    public void VerifyReasoningContextEmpty()
    {
        ReasoningContent content = new();

        Assert.Equal(string.Empty, content.Text);
        Assert.Equal(string.Empty, $"{content}");
    }

    [Fact]
    public void VerifyReasoningContextNull()
    {
        ReasoningContent content = new(null);

        Assert.Equal(string.Empty, content.Text);
        Assert.Equal(string.Empty, $"{content}");
    }
}
