// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;
using Xunit;

namespace SemanticKernel.UnitTests.TemplateEngine.Blocks;

public class FunctionIdBlockTests
{
    [Fact]
    public void ItHasTheCorrectType()
    {
        // Act
        var target = new FunctionIdBlock("", NullLoggerFactory.Instance);

        // Assert
        Assert.Equal(BlockTypes.FunctionId, target.Type);
    }

    [Fact]
    public void ItTrimsSpaces()
    {
        // Act + Assert
        Assert.Equal("aa", new FunctionIdBlock("  aa  ", NullLoggerFactory.Instance).Content);
    }

    [Theory]
    [InlineData("0", true)]
    [InlineData("1", true)]
    [InlineData("a", true)]
    [InlineData("_", true)]
    [InlineData("01", true)]
    [InlineData("01a", true)]
    [InlineData("a01", true)]
    [InlineData("_0", true)]
    [InlineData("a01_", true)]
    [InlineData("_a01", true)]
    [InlineData(".", true)]
    [InlineData("a.b", true)]
    [InlineData("-", false)]
    [InlineData("a b", false)]
    [InlineData("a\nb", false)]
    [InlineData("a\tb", false)]
    [InlineData("a\rb", false)]
    [InlineData("a,b", false)]
    [InlineData("a-b", false)]
    [InlineData("a+b", false)]
    [InlineData("a~b", false)]
    [InlineData("a`b", false)]
    [InlineData("a!b", false)]
    [InlineData("a@b", false)]
    [InlineData("a#b", false)]
    [InlineData("a$b", false)]
    [InlineData("a%b", false)]
    [InlineData("a^b", false)]
    [InlineData("a*b", false)]
    [InlineData("a(b", false)]
    [InlineData("a)b", false)]
    [InlineData("a|b", false)]
    [InlineData("a{b", false)]
    [InlineData("a}b", false)]
    [InlineData("a[b", false)]
    [InlineData("a]b", false)]
    [InlineData("a:b", false)]
    [InlineData("a;b", false)]
    [InlineData("a'b", false)]
    [InlineData("a\"b", false)]
    [InlineData("a<b", false)]
    [InlineData("a>b", false)]
    [InlineData("a/b", false)]
    [InlineData("a\\b", false)]
    public void ItAllowsUnderscoreDotsLettersAndDigits(string name, bool isValid)
    {
        // Arrange
        var target = new FunctionIdBlock($" {name} ");

        // Act + Assert
        Assert.Equal(isValid, target.IsValid(out _));
    }

    [Fact]
    public void ItAllowsOnlyOneDot()
    {
        // Arrange
        var target1 = new FunctionIdBlock("functionName");
        var target2 = new FunctionIdBlock("skillName.functionName");
        Assert.Throws<SKException>(() => new FunctionIdBlock("foo.skillName.functionName"));

        // Act + Assert
        Assert.True(target1.IsValid(out _));
        Assert.True(target2.IsValid(out _));
    }
}
