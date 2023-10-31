// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.TemplateEngine.Basic.Blocks;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.TemplateEngine.Prompt.Blocks;

public class TextBlockTests
{
    [Fact]
    public void ItHasTheCorrectType()
    {
        // Act
        var target = new TextBlock("");

        // Assert
        Assert.Equal(BlockTypes.Text, target.Type);
    }

    [Fact]
    public void ItPreservesEmptyValues()
    {
        // Act + Assert
        Assert.Equal("", new TextBlock(null).Content);
        Assert.Equal("", new TextBlock("").Content);
        Assert.Equal(" ", new TextBlock(" ").Content);
        Assert.Equal("  ", new TextBlock("  ").Content);
        Assert.Equal(" \n", new TextBlock(" \n").Content);
    }

    [Fact]
    public void ItIsAlwaysValid()
    {
        // Act + Assert
        Assert.True(new TextBlock(null).IsValid(out _));
        Assert.True(new TextBlock("").IsValid(out _));
        Assert.True(new TextBlock(" ").IsValid(out _));
        Assert.True(new TextBlock("  ").IsValid(out _));
        Assert.True(new TextBlock(" \n").IsValid(out _));
        Assert.True(new TextBlock(" \nabc").IsValid(out _));
    }

    [Fact]
    public void ItRendersTheContentAsIs()
    {
        // Act + Assert
        Assert.Equal("", new TextBlock(null).Render(null));
        Assert.Equal("", new TextBlock("").Render(null));
        Assert.Equal(" ", new TextBlock(" ").Render(null));
        Assert.Equal("  ", new TextBlock("  ").Render(null));
        Assert.Equal(" \n", new TextBlock(" \n").Render(null));
        Assert.Equal("'x'", new TextBlock("'x'").Render(null));
    }
}
