// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Contents;

/// <summary>
/// Unit testing of <see cref="ActionContent"/>.
/// </summary>
public class ActionContentTests
{
    [Fact]
    public void VerifyActionContextText()
    {
        ActionContent content = new("test");

        Assert.Equal("test", content.Text);
        Assert.Equal("test", $"{content}");
    }

    [Fact]
    public void VerifyActionContextInvalid()
    {
        Assert.Throws<ArgumentNullException>(() => new ActionContent(null!));
        Assert.Throws<ArgumentException>(() => new ActionContent(string.Empty));
        Assert.Throws<ArgumentException>(() => new ActionContent(" "));
    }
}
