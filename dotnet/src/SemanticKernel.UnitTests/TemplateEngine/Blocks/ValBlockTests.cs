// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.TemplateEngine.Blocks;
using Xunit;

namespace SemanticKernel.UnitTests.TemplateEngine.Blocks;

public class ValBlockTests
{
    [Fact]
    public void ItHasTheCorrectType()
    {
        // Act
        var target = new ValBlock("");

        // Assert
        Assert.Equal(BlockTypes.Value, target.Type);
    }

    [Fact]
    public void ItTrimsSpaces()
    {
        // Act + Assert
        Assert.Equal("' '", new ValBlock("  ' '  ").Content);
        Assert.Equal("\"  \"", new ValBlock("  \"  \"  ").Content);
    }

    [Fact]
    public void ItChecksIfAValueStartsWithQuote()
    {
        // Assert
        Assert.True(ValBlock.HasValPrefix("'"));
        Assert.True(ValBlock.HasValPrefix("'a"));
        Assert.True(ValBlock.HasValPrefix("\""));
        Assert.True(ValBlock.HasValPrefix("\"b"));

        Assert.False(ValBlock.HasValPrefix("d'"));
        Assert.False(ValBlock.HasValPrefix("e\""));
        Assert.False(ValBlock.HasValPrefix(null));
        Assert.False(ValBlock.HasValPrefix(""));
        Assert.False(ValBlock.HasValPrefix("v"));
        Assert.False(ValBlock.HasValPrefix("-"));
    }

    [Fact]
    public void ItRequiresConsistentQuotes()
    {
        // Arrange
        var validBlock1 = new ValBlock("'ciao'");
        var validBlock2 = new ValBlock("\"hello\"");
        var badBlock1 = new ValBlock("'nope\"");
        var badBlock2 = new ValBlock("'no\"");

        // Act + Assert
        Assert.True(validBlock1.IsValid(out _));
        Assert.True(validBlock2.IsValid(out _));
        Assert.False(badBlock1.IsValid(out _));
        Assert.False(badBlock2.IsValid(out _));
    }
}
